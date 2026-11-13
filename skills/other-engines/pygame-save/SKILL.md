---
name: pygame-save
description: >
  Save and load pygame games without an engine save API: a per-OS data directory, JSON saves
  written atomically with os.replace, backup copies, schema versions and migrations, settings
  kept apart from slots, and recovery from a corrupt save. Use when a pygame game must persist
  progress or settings, or the request mentions saving in pygame, a save file, save slots, or a
  corrupted save. Targets pygame-ce 2.5.8 on Python 3.10+.
---

# pygame saves

pygame has no save system: persistence is Python's `pathlib` plus `json` plus an atomic replace.
This skill sets up the directory, the format, the write protocol and the migrations.
Targets **pygame-ce 2.5.8** on **Python 3.10+**.

## When to use

- Use when a pygame game must remember progress, unlocks, settings or level edits between runs.
- Use when a save is missing, corrupt, shared between machines, or incompatible after an update.

**When *not* to use:** slot design and player-facing save UX for any engine → `save-systems`;
the loop and `Sprite`/`Group` basics → `pygame-core`; tile-level persistence → `pygame-tilemap`
plus this skill; LÖVE/Godot/Unity equivalents → `love2d-save`, `godot-save`, `unity-save`.

## Core workflow

1. **Choose a writable data directory.** Never write next to the script or the packaged
   executable: that folder may be read-only or inside the install tree. Use
   `%APPDATA%`/`Application Support`/`$XDG_DATA_HOME`, or the `platformdirs` package.
2. **Separate settings from progress.** Settings are one small file written on change; progress
   is one file per slot plus its backup.
3. **Define a versioned JSON schema.** A `version` integer and plain JSON types only; no
   tuples-as-keys, no `set`, no `bytes`, no NaN/infinity.
4. **Write atomically.** Write a temp file in the *same directory*, `flush()` and `fsync()`,
   then `os.replace(tmp, target)`. Copy the old target to `.bak` first.
5. **Load defensively.** Missing file → defaults. Parse errors, wrong types or an unknown future
   version → try `.bak`, then defaults, and log which path was used.
6. **Migrate, then save.** Migrate in memory on load; write only when the player saves.
7. **Verify on a packaged build.** Run the PyInstaller/zipapp build and confirm the same files in
   the same directory; the working directory differs from the source checkout.

## Patterns

### 1. A data directory that works on every desktop OS

```python
import os
from pathlib import Path

APP = "my-game"

def data_dir() -> Path:
    if os.name == "nt":                                   # Windows
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":                         # macOS
        base = Path.home() / "Library" / "Application Support"
    else:                                                  # Linux and other XDG systems
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / APP
    path.mkdir(parents=True, exist_ok=True)
    return path

SAVE_DIR = data_dir() / "saves"
SAVE_DIR.mkdir(exist_ok=True)
```

`platformdirs.user_data_dir(APP)` does the same job with the per-OS rules kept up to date; use it
if the project already depends on it. Keep the path under the user profile, not next to the
game files.

### 2. Write a save atomically

```python
import json
import os
import shutil
import tempfile
from pathlib import Path

def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())          # content reaches the disk before the swap
        if path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        os.replace(tmp, path)                  # atomic on POSIX; replaces on Windows too
    finally:
        tmp.unlink(missing_ok=True)
```

`os.replace` is atomic on POSIX and overwrites an existing destination on Windows (Python 3.3+);
it requires the temp file and target to be on the same filesystem, which is why the temp file is
created in `path.parent`. `allow_nan=False` makes a non-finite float fail loudly instead of
producing a file other parsers reject.

### 3. Save and load with schema versions

```python
CURRENT_VERSION = 3

def save_slot(slot: str, state: dict) -> None:
    state = dict(state, version=CURRENT_VERSION)
    atomic_write_json(SAVE_DIR / f"{slot}.json", state)

def _read(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None

def load_slot(slot: str) -> dict | None:
    for name in (f"{slot}.json", f"{slot}.json.bak"):
        data = _read(SAVE_DIR / name)
        if data is not None:
            return migrate(data)
    return None
```

Catch `json.JSONDecodeError` **and** `OSError`; a permission error or a half-written file should
fall through to the backup, not crash the game.

### 4. Migrations

```python
def _v1_to_v2(save: dict) -> dict:
    save["gold"] = save.pop("money", 0)
    save["version"] = 2
    return save

def _v2_to_v3(save: dict) -> dict:
    save.setdefault("stats", {"deaths": 0})
    save["version"] = 3
    return save

MIGRATIONS = {1: _v1_to_v2, 2: _v2_to_v3}

def migrate(save: dict) -> dict:
    version = int(save.get("version", 1))
    if version > CURRENT_VERSION:
        raise ValueError(f"save is newer than this build: {version}")
    while version < CURRENT_VERSION:
        step = MIGRATIONS.get(version)
        if step is None:
            raise ValueError(f"no migration from version {version}")
        save = step(save)
        version = int(save["version"])
    return save
```

Treat an unknown **future** version as "cannot load in this build", not as version 1; otherwise a
newer save is silently downgraded.

### 5. Slots and settings

```python
def list_slots() -> list[dict]:
    slots = []
    for path in SAVE_DIR.glob("*.json"):
        if path.name.endswith(".bak.json"):
            continue
        slots.append({"slot": path.stem, "mtime": path.stat().st_mtime})
    return sorted(slots, key=lambda item: item["mtime"], reverse=True)

def delete_slot(slot: str) -> None:
    (SAVE_DIR / f"{slot}.json").unlink(missing_ok=True)
    (SAVE_DIR / f"{slot}.json.bak").unlink(missing_ok=True)

def save_settings(settings: dict) -> None:
    atomic_write_json(data_dir() / "settings.json", dict(settings, version=1))
```

`Path.unlink(missing_ok=True)` is Python 3.8+; no `try` needed for an absent file. Save settings
on change, and save progress on a deliberate event (checkpoint, quit) rather than every frame.

### 6. Saving on quit

```python
import pygame

def run(game) -> None:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        game.update()
        game.draw()

    game.save_if_dirty()      # before pygame.quit(), while game objects still exist
    pygame.quit()
```

Do the write before `pygame.quit()`; keep the save independent of the display so a headless test
can call it. If the game can be killed from the task manager, also autosave at checkpoints.

## Pitfalls

- **Save disappears after installing the game** → it was written next to the executable, which is
  replaced on update or read-only under `Program Files`. Write under the per-user data directory.
- **Save is empty or truncated** → the file was opened with `"w"` and the process died mid-write.
  Use the temp + `fsync` + `os.replace` protocol.
- **Backup is silently overwritten with the broken file** → the `.bak` copy was made *after* the
  new write succeeded, or the loader tried `.bak` before the main file. Copy the old file first,
  load the main file first.
- **`json.dump` raises `ValueError: Out of range float values are not JSON compliant`** → a NaN
  or infinity reached the save. Sanitize or reject those values before saving.
- **Tuple keys turned into strings** → JSON object keys must be strings. Use lists of
  `{"x": ..., "y": ...}` for positions or a flat string key and parse it back.
- **`TypeError: Object of type set is not JSON serializable`** → convert sets to sorted lists and
  restore them on load.
- **Save is not atomic on Windows** → `os.replace` needs the temp file on the same drive and may
  fail if the target is open. Close readers before replacing, and keep the temp file in the same
  folder.
- **A newer save is loaded as version 1** → check for a version above `CURRENT_VERSION` and
  refuse instead of migrating downward.
- **`PermissionError` on `Path.home()` in a sandbox/CI** → allow the data directory to be
  overridden (for example with an environment variable) so tests can point at `tmp_path`.
- **Two instances overwrite each other** → there is no locking. Save to a per-process temp name
  and accept last-writer-wins, or add a lock file if the game allows multiple instances.

## References

- Read `references/directories-and-atomic-writes.md` for data-directory rules per OS, the exact
  write protocol, JSON validation, migration examples, compression and a testing checklist.

## Related skills

- `save-systems` — engine-neutral slot design, schemas and save UX.
- `pygame-core` — the loop and game state this save layer serializes.
- `pygame-tilemap` — persisting edited tile grids through this layer.
- `love2d-save` — the same concerns in LÖVE, including its missing-rename workaround.
- `godot-save` / `unity-save` / `unreal-save` — engine-native alternatives.
