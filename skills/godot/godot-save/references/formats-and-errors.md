# Godot 4.7 save formats and file APIs

Reference material for `SKILL.md`. Targets **Godot 4.7**.

## Format comparison

| Format | API | Strengths | Weaknesses | Use for |
|--------|-----|-----------|------------|---------|
| JSON | `JSON.stringify` / `JSON.parse_string` | Readable, diffable, cross-version | Floats for all numbers, string keys only, no resources | Progress, inventory, world state |
| ConfigFile | `ConfigFile` | Typed Variants, sections, defaults | Not for deep nested data | Settings, keybinds, options |
| Binary Variant | `store_var` / `get_var` | Compact, fast, keeps Variant types | Opaque, engine-version sensitive | Large or frequent saves |
| Resource | `ResourceSaver` / `ResourceLoader` | Typed fields, editor tooling, `.tres` diffable | Script references, unsafe for untrusted files | Editor-authored save data |

## FileAccess API

| Call | Notes |
|------|-------|
| `FileAccess.open(path, mode)` | Returns `null` on failure; check `get_open_error()` |
| `FileAccess.file_exists(path)` | Static existence check without opening |
| `file.store_string(text)` / `file.get_as_text()` | UTF-8 text |
| `file.store_var(value, full_objects=false)` / `file.get_var(allow_objects=false)` | Binary Variant |
| `file.store_buffer(buffer)` / `file.get_buffer(length)` | Raw bytes |
| `file.store_line(line)` / `file.get_line()` | Line-oriented text |
| `file.flush()` / `file.close()` | Flush before renaming; closing frees the handle |
| `FileAccess.open_encrypted_with_pass(path, mode, pass)` | AES with a password from the build |
| `FileAccess.get_open_error()` | Error code of the last failed open |

Modes: `FileAccess.READ`, `WRITE`, `READ_WRITE`, `WRITE_READ`.

## DirAccess static helpers

| Call | Notes |
|------|-------|
| `DirAccess.make_dir_recursive_absolute("user://saves/slot1")` | Creates missing parents |
| `DirAccess.dir_exists_absolute(path)` | Check before creating |
| `DirAccess.rename_absolute(from, to)` | Move a finished temp file into place |
| `DirAccess.remove_absolute(path)` | Delete a file; check the returned `Error` |
| `DirAccess.copy_absolute(from, to)` | Keep a `.bak` of the previous save |

## Paths

- `user://` maps to a per-user, writable location on every platform:
  Windows `%APPDATA%`, macOS `~/Library/Application Support`, Linux `~/.local/share`, Android/iOS
  app sandboxes, web IndexedDB.
- `res://` is the project bundle and is read-only in exports.
- `ProjectSettings.globalize_path("user://")` prints the real directory while debugging.
- Keep save files small and versioned; the directory is not backed up by the engine.

## Atomic write and backup recipe

```text
write user://save.json.tmp
close
if user://save.json exists:
    copy user://save.json -> user://save.json.bak
    remove user://save.json
rename user://save.json.tmp -> user://save.json
```

Load order: `save.json` → `save.json.bak` → defaults. Log which path succeeded; a silent fallback
hides corruption during development.

Deleting before renaming is deliberate: some platforms refuse to rename onto an existing file. The
`.bak` copy keeps the previous good state available if the rename fails.

## Migration

Store an integer `version` in every payload. On load:

```gdscript
var version := int(data.get("version", 0))
if version < CURRENT_VERSION:
    data = migrate(data, version)
```

Rules that keep migrations sane:

- Never reuse a version number.
- Migrate one step at a time (`v1 → v2 → v3`), not with a chain of `if` blocks.
- Fill missing keys with defaults instead of assuming presence.
- Keep a fixture of an old save in the repo and load it in a headless test.
- Write the migrated payload back once, so the next load is fast and current.

## Encryption limits

`open_encrypted_with_pass` uses AES with a key derived from the password. The password is embedded
in the client, so a determined player can extract it and decrypt or re-encrypt the file. Treat it as
tamper deterrence, never as authoritative anti-cheat:

- Keep currency, unlocks and competitive stats on a server when they matter.
- Sign or checksum payloads server-side.
- Do not put secrets (API keys, tokens) in save files.

## Failure-path test checklist

1. No save file: fresh defaults, no errors in the log.
2. Normal save → quit → relaunch → state restored.
3. Corrupt the main file: load falls back to `.bak` and logs it.
4. Both files corrupt: defaults with a clear error, no crash.
5. Old version fixture: migration runs, data survives, file is rewritten at the new version.
6. Delete the `user://saves` directory: save recreates it recursively.
7. Save twice in a row: no `.tmp` left behind, `.bak` holds the previous state.
8. Export a build: saves work on the target platform, not just in the editor.
9. Quit immediately after saving: the file on disk is complete and parses.
