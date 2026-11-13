# Data directories, atomic writes and migrations (pygame-ce)

Depth for `pygame-save`: where files belong, why the write protocol looks like that, and what to
test before shipping.

## Data directory rules

| OS | Base | Typical game folder |
|----|------|---------------------|
| Windows | `%APPDATA%` | `%APPDATA%\my-game` |
| macOS | `~/Library/Application Support` | `~/Library/Application Support/my-game` |
| Linux/BSD | `$XDG_DATA_HOME` (default `~/.local/share`) | `~/.local/share/my-game` |

- Never use the current working directory, `__file__`, or the folder containing a frozen
  executable; all three change between source runs, packaged runs and updates.
- `pathlib.Path.home()` can raise or point somewhere unwritable in restricted environments; offer
  an override (`MY_GAME_DATA_DIR`) and use it in tests.
- `platformdirs.user_data_dir("my-game", "studio")` implements these rules and adds the macOS
  bundle id convention; it is a small third-party dependency, not part of pygame.
- Keep one directory per game, and one subdirectory (`saves/`) for slots so settings and saves
  can be backed up or deleted independently.
- If the game is portable by design, put a `portable.txt` marker next to the executable and use
  `Path.cwd() / "saves"`; document that choice, because it breaks under `Program Files`.

## Write protocol

```text
settings.json
saves/
├── slot1.json          <- current
├── slot1.json.bak      <- previous good copy
└── slot1.json.<rand>.tmp
```

Steps and reasons:

1. `tempfile.mkstemp(dir=target.parent, ...)` creates a unique temp name in the same directory;
   the same filesystem is required for an atomic replace.
2. `json.dump(..., allow_nan=False)` fails before the swap if the data is not representable.
3. `flush()` + `os.fsync(fd)` pushes content to disk; without it a power loss can leave the
   renamed file empty even though the rename happened.
4. Copy the existing target to `.<ext>.bak` before replacing it. Use `shutil.copy2` to keep
   metadata, or `os.replace(target, backup)` if you do not need the target to exist during the
   copy (it briefly disappears).
5. `os.replace(tmp, target)` swaps in the new file. On POSIX it is atomic; on Windows it replaces
   an existing file and is atomic in practice for same-volume paths, but the docs only promise
   atomicity on Unix.
6. In the `finally`, `tmp.unlink(missing_ok=True)`: a failed save must not leave temp files in
   the player's save folder.

Directory durability (optional, POSIX): after the replace, `fd = os.open(dir, os.O_RDONLY)` and
`os.fsync(fd)` so the directory entry itself is flushed. This matters for sudden power loss, not
for a normal process crash.

## Validation after load

```python
def validate(save: dict) -> dict:
    if not isinstance(save.get("player"), dict):
        raise ValueError("missing player object")
    save.setdefault("unlocks", [])
    save.setdefault("settings", {})
    return save
```

- Reject or clamp values instead of trusting them: a save can be edited by hand, and a huge or
  negative number must not corrupt the game.
- Check the version **before** touching fields; a migration expects the old shape.
- Reject a save whose `version` is greater than `CURRENT_VERSION`; it was written by a newer
  build.
- Do not `eval` or `pickle` save files. `pickle.load` executes arbitrary code and is not a save
  format for player-controlled files.

## Migration examples

```python
def migrate(save: dict) -> dict:
    version = int(save.get("version", 1))
    while version < CURRENT_VERSION:
        save = MIGRATIONS[version](save)
        version = int(save["version"])
    return save
```

| Change | Migration |
|--------|-----------|
| rename a field | copy old → new, `pop` the old name, bump version |
| add a field | `setdefault` a sane default |
| change a container | convert list ↔ dict, preserving ids |
| split one save into slots | read the legacy file once, write the new slots, keep the old file as `.legacy` |
| change coordinate space | convert in the migration, never in gameplay code |

Keep a small fixture per released version under `tests/fixtures/` and load each one in CI.

## Compression and binary formats

- `gzip.compress(text.encode())` / `gzip.decompress` is enough for large worlds and keeps JSON
  debuggable when decompressed.
- `lzma` compresses better but is slower; profile before using it on every save.
- `struct` is fine for fixed binary records, but versioning binary layouts is harder than JSON:
  keep the header small and explicit (`magic`, `version`, `count`).
- Never use `pickle` for saves that players can edit, copy between machines, or download.

## Testing checklist

1. Fresh profile: no directory, first save creates it, load returns defaults.
2. Save, quit, relaunch: progress restored.
3. Corrupt the main file (truncate, invalid UTF-8, wrong JSON type): the `.bak` loads.
4. Delete the main file but keep `.bak`: the backup loads.
5. Make the directory read-only: the save reports a clear error and the old file survives.
6. Save with NaN/infinity in state: it fails before the swap, old save intact.
7. Load a fixture from every released version: each migrates to `CURRENT_VERSION`.
8. Load a save with `version` greater than the build: it is refused, not downgraded.
9. Packaged build on each OS: same directory, same file names.
10. Two rapid saves in a row: no `.tmp` files remain and the backup is the previous save.
