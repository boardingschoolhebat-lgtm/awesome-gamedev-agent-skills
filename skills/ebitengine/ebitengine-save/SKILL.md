---
name: ebitengine-save
description: >
  Save and load Ebitengine (Go) games: choosing a config directory with os.UserConfigDir, JSON
  encoding with versioned structs and migrations, atomic writes via temp file + rename, save
  slots, settings vs progress, corrupt-file recovery, and the browser/WASM storage limitation.
  Use when an Ebitengine game must persist progress or settings. Targets Ebitengine v2.10.5 and Go 1.25.
---

# Ebitengine saves

Ebitengine has no save API; a Go game writes its own file. The standard library gives everything
needed: `os.UserConfigDir` for the location, `encoding/json` for the format, and temp-file +
rename for a safe overwrite. Targets **Ebitengine v2.10.5** and **Go 1.25**.

## When to use

- Use when an Ebitengine game must remember progress, unlocks, settings or high scores.
- Use when saves land in the wrong place, break between versions, or corrupt on crash.

**When *not* to use:** save-slot UX design → `save-systems`; the game loop → `ebitengine-core`;
desktop-only deployment → `ebitengine-core` build notes.

## Core workflow

1. **Resolve a per-user directory** with `os.UserConfigDir()` plus an app-specific subdirectory;
   do not write next to the executable (read-only on macOS, Program Files on Windows).
2. **Define versioned structs** with JSON tags and a `version` field.
3. **Write atomically**: temp file in the same directory, `Sync`, `Close`, rename over the target,
   with a `.bak` fallback.
4. **Read defensively**: missing file → defaults; decode error → try `.bak`; then migrate.
5. **Separate settings and slots** into different files.
6. **Test on Windows, macOS and Linux** — rename semantics differ.

## Patterns

### 1. Save location

```go
func saveDir() (string, error) {
    base, err := os.UserConfigDir()   // %AppData%, ~/Library/Application Support, ~/.config
    if err != nil {
        return "", err
    }
    dir := filepath.Join(base, "MyGame")
    if err := os.MkdirAll(dir, 0o755); err != nil {
        return "", err
    }
    return dir, nil
}
```

- `os.UserConfigDir` honors `XDG_CONFIG_HOME` on Unix, `%AppData%` on Windows, and Application
  Support on macOS.
- Use a stable directory name derived from the game, not the executable path.
- For a portable build, allow an override (flag/env) for the save directory.

### 2. Versioned state and atomic write

```go
type Save struct {
    Version int    `json:"version"`
    Slot    int    `json:"slot"`
    Level   int    `json:"level"`
    Coins   int    `json:"coins"`
    Unlocks []string `json:"unlocks"`
}

const currentVersion = 2

func writeSave(path string, s Save) error {
    s.Version = currentVersion
    data, err := json.MarshalIndent(s, "", "  ")
    if err != nil {
        return err
    }

    dir := filepath.Dir(path)
    tmp, err := os.CreateTemp(dir, filepath.Base(path)+".tmp-*")
    if err != nil {
        return err
    }
    tmpName := tmp.Name()
    defer os.Remove(tmpName)          // no-op after a successful rename

    if _, err := tmp.Write(data); err != nil {
        tmp.Close()
        return err
    }
    if err := tmp.Sync(); err != nil {
        tmp.Close()
        return err
    }
    if err := tmp.Close(); err != nil {
        return err
    }

    // Keep the previous save as a backup.
    _ = os.Rename(path, path+".bak")
    if err := os.Rename(tmpName, path); err != nil {
        _ = os.Rename(path+".bak", path)
        return err
    }
    return nil
}
```

- Create the temp file **in the same directory** so the rename stays on one filesystem.
- `Sync` before rename reduces the chance of an empty file after a power loss.
- On Windows, `os.Rename` over an existing file can fail; moving the old file to `.bak` first
  avoids that.
- If the final rename fails, restore `.bak` so the player keeps a working save.

### 3. Load with fallback and migration

```go
func loadSave(path string) (Save, error) {
    for _, p := range []string{path, path + ".bak"} {
        data, err := os.ReadFile(p)
        if err != nil {
            continue
        }
        var s Save
        if err := json.Unmarshal(data, &s); err != nil {
            continue
        }
        if s.Version > currentVersion {
            return Save{}, fmt.Errorf("save is from a newer version")
        }
        return migrate(s), nil
    }
    return Save{Version: currentVersion}, os.ErrNotExist
}

func migrate(s Save) Save {
    if s.Version < 2 {
        s.Unlocks = append(s.Unlocks, "default")
        s.Version = 2
    }
    return s
}
```

- Missing file is normal on first run; return defaults, not an error dialog.
- A save from a newer build must be refused, not partially loaded.
- Migrations run in order and each bumps `Version`.
- Keep one fixture save per released version and load them in a test.

### 4. Slots and settings

```go
func slotPath(dir string, slot int) string {
    return filepath.Join(dir, fmt.Sprintf("slot-%d.json", slot))
}
func settingsPath(dir string) string {
    return filepath.Join(dir, "settings.json")
}
```

- Settings (volume, remap, accessibility) are a separate small file; changing volume should not
  rewrite progress.
- Slot metadata (level, playtime, timestamp) can live in the slot file itself; read all slots to
  build the load menu.
- Deleting a slot removes both the file and its `.bak`.

### 5. What JSON can and cannot store

- Exported struct fields only; unexported fields are silently skipped.
- Maps need string keys.
- No functions, channels, complex numbers, or cycles.
- `time.Time` marshals as RFC 3339; durations as integers (nanoseconds) unless you add a custom
  type.
- Very large saves: JSON is fine for KBs; for MBs consider a compact binary format with
  `encoding/gob` or a custom layout, and keep the same atomic-write protocol.

### 6. Browser/WASM caveat

On WebAssembly, `os.UserConfigDir` has no real user directory and `os` file writes are backed by
the browser's virtual filesystem (often in-memory, cleared on reload). For a browser build, persist
to `localStorage`/IndexedDB via `syscall/js` (or a small storage abstraction), and keep the same
versioned struct and migration path. Test a reload, not only a same-session read.

## Pitfalls

- **Save next to the executable** → read-only on macOS bundles and Program Files. Use
  `os.UserConfigDir`.
- **Empty save after a crash** → direct `os.WriteFile` on the live file. Use temp + sync + rename.
- **Rename fails on Windows** → destination exists. Move it to `.bak` first.
- **Corrupt save bricks the game** → no fallback. Try `.bak`, then defaults.
- **Old saves fail after an update** → no version/migration. Version every schema.
- **Settings wipe progress** → one file for everything. Split settings and slots.
- **Silent write failures** → ignored `error` from `Write`/`Sync`/`Rename`. Surface a message.
- **Unexported fields vanish** → JSON ignores them; keep save fields exported.
- **Web build "saves" but loses data on reload** → in-memory FS. Use browser storage.
- **Concurrent writes** → autosave and manual save racing. Serialize writes (one goroutine or a
  mutex).

## References

- Read `references/paths-atomic-writes-and-migrations.md` for the Go API table, platform paths,
  atomic-write variants, migration patterns and a save test checklist.

## Related skills

- `ebitengine-core` — the game state being saved.
- `save-systems` — engine-neutral slot and autosave design.
- `defold-save` / `godot-save` / `love2d-save` — the same concerns in other engines.
