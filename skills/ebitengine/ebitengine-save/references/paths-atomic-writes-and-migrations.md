# Paths, atomic writes and migrations (Go 1.25, Ebitengine v2.10.5)

Depth for `ebitengine-save`: where files go, how to replace them safely, and how to keep old saves
loadable.

## API used by the skill

| API | Package | Notes |
|-----|---------|-------|
| `os.UserConfigDir()` | `os` | `%AppData%`, `~/Library/Application Support`, `$XDG_CONFIG_HOME` or `~/.config`. |
| `os.MkdirAll(path, perm)` | `os` | Creates parents; no error if it exists. |
| `os.CreateTemp(dir, pattern)` | `os` | Temp file in the same directory for atomic rename. |
| `(*os.File).Sync()` | `os` | Flush to disk before rename. |
| `os.Rename(old, new)` | `os` | Replace; may fail if destination exists on Windows. |
| `os.ReadFile` / `os.WriteFile` | `os` | Whole-file read/write. |
| `encoding/json` | stdlib | `MarshalIndent`, `Unmarshal`. |
| `encoding/gob` | stdlib | Compact binary alternative. |
| `errors.Is(err, fs.ErrNotExist)` | `errors`, `io/fs` | First-run detection. |

## Platform paths

| OS | `os.UserConfigDir()` |
|----|----------------------|
| Windows | `%AppData%` (Roaming) |
| macOS | `~/Library/Application Support` |
| Linux/BSD | `$XDG_CONFIG_HOME` or `~/.config` |
| Plan 9 | `$home/lib` |
| WASM | no real user dir; virtual FS |

Always append an app-specific folder: `<config>/MyGame/`. Create it with `MkdirAll` before writing.

## Atomic write variants

### Simple (single process, best effort)

```go
tmp, err := os.CreateTemp(dir, "save-*")
...
tmp.Sync(); tmp.Close()
os.Rename(tmp.Name(), path)
```

### With backup (Windows-safe)

```go
_ = os.Rename(path, path+".bak")     // move old aside
if err := os.Rename(tmp, path); err != nil {
    _ = os.Rename(path+".bak", path) // restore
    return err
}
```

### With fsync of the directory (Unix durability)

After rename, open the directory and `Sync` it to persist the directory entry. This is optional
for a game but reduces the chance of losing the rename on power loss.

```go
if d, err := os.Open(dir); err == nil {
    _ = d.Sync()
    d.Close()
}
```

## Save schema

```go
type Save struct {
    Version  int       `json:"version"`
    Slot     int       `json:"slot"`
    Level    int       `json:"level"`
    Coins    int       `json:"coins"`
    Playtime int64     `json:"playtime_seconds"`
    SavedAt  time.Time `json:"saved_at"`
    Unlocks  []string  `json:"unlocks"`
}
```

- `Version` first; every migration bumps it.
- `SavedAt` for slot lists and "continue".
- No pointers to game objects; store ids and rebuild on load.
- Keep field names stable once released; add fields, do not rename.

## Migration pattern

```go
type migration func(Save) Save

var migrations = map[int]migration{
    1: func(s Save) Save { s.Unlocks = append(s.Unlocks, "default"); s.Version = 2; return s },
    2: func(s Save) Save { s.Playtime = s.Playtime * 1; s.Version = 3; return s },
}

func migrate(s Save) (Save, error) {
    for s.Version < currentVersion {
        m, ok := migrations[s.Version]
        if !ok {
            return s, fmt.Errorf("no migration from version %d", s.Version)
        }
        s = m(s)
    }
    return s, nil
}
```

- Migrate on load, write on save.
- Refuse `Version > currentVersion`.
- Keep fixtures: `testdata/save-v1.json`, `v2.json`, ... loaded by a table test.

## Error handling

| Situation | Behavior |
|-----------|----------|
| First run, no file | Defaults; no error shown |
| Decode error | Try `.bak`; if that fails, defaults + log |
| Newer version | Refuse, keep file untouched |
| Disk full / permission | Return error, keep old save, tell the player |
| Rename failure | Restore `.bak`, return error |

## WASM storage

`os` file writes in the browser are virtual and may not survive reload. Options:

- `localStorage` for small JSON (synchronous, ~5 MB limit).
- IndexedDB for larger or structured data (async; wrap in a goroutine + channel).
- Keep the same versioning/migration code; only the reader/writer changes.

```go
//go:build js && wasm

func writeSaveJS(key string, data []byte) {
    js.Global().Get("localStorage").Call("setItem", key, string(data))
}
```

Test a page reload, a cleared storage, and private browsing (storage can throw).

## Test checklist

1. First run: defaults, no error dialog.
2. Save, quit, relaunch: state restored on Windows, macOS, Linux.
3. Kill the process during save: file is either old or new, never truncated.
4. Corrupt main file: `.bak` loads.
5. Newer-version file: refused with a clear message, file untouched.
6. Every fixture version migrates to current.
7. Slot delete removes main and `.bak`.
8. Settings changes do not touch slot files.
9. Save directory read-only: error surfaced, old save intact.
10. WASM: reload keeps progress via browser storage; cleared storage falls back to defaults.
