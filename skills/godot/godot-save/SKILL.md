---
name: godot-save
description: >
  Save and load game state in Godot 4.7: user:// paths, FileAccess text/binary/Variant IO, JSON
  payloads with versioning and migrations, ConfigFile settings, custom Resource saves, atomic
  writes through a temp file, and encrypted saves with their limits. Use when a game must persist
  progress, settings or inventory, or when a save file fails to load after an update.
---

# Godot save and load

Persist game state in Godot 4.7 with the engine's file APIs. Targets **Godot 4.7**.

Everything writable lives under `user://`. `FileAccess` reads and writes, `JSON` and `ConfigFile`
serialize, `ResourceSaver` stores typed resources, and `DirAccess` handles directories and the
rename that makes a write atomic.

## When to use

- Use when implementing save slots, settings persistence, checkpoints, inventory or progress.
- Use when a save fails to load, a save file from an older build breaks, or writes leave a
  truncated file after a crash.

**When *not* to use:** save-format design, slot UX and anti-cheat strategy across engines →
`save-systems`; custom `Resource` types as data architecture → `godot-resources`; UI for the load
menu → `godot-ui-control`; networked persistence → `godot-multiplayer` or the platform service.

## Core workflow

1. **Pick the format.** JSON for readable, debuggable saves; `ConfigFile` for settings; `store_var`
   for compact binary; a custom `Resource` when the data is authored in the editor. See the
   reference for the tradeoffs.
2. **Write only under `user://`.** `res://` is read-only in exported builds. Create subdirectories
   with `DirAccess.make_dir_recursive_absolute`.
3. **Serialize plain data.** Dictionaries, arrays, numbers, strings, bools — no nodes, no object
   references. Store IDs and rebuild nodes on load.
4. **Version the payload.** Put an integer `version` at the top and migrate older files on read.
5. **Write atomically.** Write to `path.tmp`, close it, keep a `.bak` of the previous file, then
   rename the temp into place. A crash mid-write must not destroy the last good save.
6. **Validate on read.** Check existence, `null` handles, parse errors, expected types and version
   before touching game state; fall back to defaults.
7. **Test the failure paths.** Missing file, corrupt file, old version, missing directory, and a
   save triggered while quitting.

## Patterns

### 1. JSON save with version and atomic replace

```gdscript
const SAVE_PATH := "user://save.json"
const SAVE_VERSION := 2

func save_game(state: Dictionary) -> Error:
	state["version"] = SAVE_VERSION
	var tmp_path := SAVE_PATH + ".tmp"
	var file := FileAccess.open(tmp_path, FileAccess.WRITE)
	if file == null:
		var err := FileAccess.get_open_error()
		push_error("save: cannot open %s (%s)" % [tmp_path, error_string(err)])
		return err

	file.store_string(JSON.stringify(state, "\t"))
	file.close()

	# Keep the previous good save, then swap the new one in.
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.copy_absolute(SAVE_PATH, SAVE_PATH + ".bak")
		DirAccess.remove_absolute(SAVE_PATH)

	var rename_err := DirAccess.rename_absolute(tmp_path, SAVE_PATH)
	if rename_err != OK:
		push_error("save: rename failed (%s)" % error_string(rename_err))
	return rename_err
```

`JSON.stringify` returns an empty string for unsupported types — log a failure instead of writing
a zero-byte save. On load, prefer the main file and fall back to `.bak` when it does not parse.

### 2. JSON load with defaults and migration

```gdscript
func load_game() -> Dictionary:
	if not FileAccess.file_exists(SAVE_PATH):
		return {}

	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		push_error("load: cannot open (%s)" % error_string(FileAccess.get_open_error()))
		return {}

	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("load: corrupt save, trying backup")
		return load_backup()

	var data: Dictionary = parsed
	var version := int(data.get("version", 0))
	if version < SAVE_VERSION:
		data = _migrate(data, version)
	return data

func _migrate(data: Dictionary, from_version: int) -> Dictionary:
	if from_version < 1:
		data["coins"] = int(data.get("coins", 0))
	if from_version < 2:
		data["inventory"] = data.get("inventory", [])
	data["version"] = SAVE_VERSION
	return data
```

JSON numbers parse as floats: cast counters with `int()`, and store integers above 2^53 as strings
to avoid precision loss.

### 3. Settings with ConfigFile

```gdscript
func save_settings(music: float, fullscreen: bool) -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("audio", "music", music)
	cfg.set_value("video", "fullscreen", fullscreen)
	cfg.save("user://settings.cfg")

func load_settings() -> Dictionary:
	var cfg := ConfigFile.new()
	if cfg.load("user://settings.cfg") != OK:
		return {"music": 0.8, "fullscreen": false}
	return {
		"music": cfg.get_value("audio", "music", 0.8),
		"fullscreen": cfg.get_value("video", "fullscreen", false),
	}
```

`ConfigFile` keeps typed Variants in a human-readable file and is the right tool for options;
`get_value` takes a default, so missing keys never crash a first run.

### 4. Compact binary Variant save

```gdscript
var file := FileAccess.open("user://save.dat", FileAccess.WRITE)
if file:
	file.store_var({"version": 1, "coins": 25, "inventory": ["axe", "rope"]})

# read
var data: Variant = file.get_var()   # allow_objects defaults to false
```

Faster and smaller than JSON, but not human-readable and not portable across engine versions you
do not control. Never pass `true` for `allow_objects` on files the player can edit — it can
instantiate objects.

### 5. Typed Resource save

```gdscript
class_name SaveData
extends Resource

@export var version: int = 1
@export var coins: int = 0
@export var inventory: Array[String] = []

# save
var data := SaveData.new()
data.coins = 25
ResourceSaver.save(data, "user://save.tres")

# load
var loaded := ResourceLoader.load("user://save.tres") as SaveData
```

Resources give typed fields and editor tooling, and `.tres` stays diffable. They also store script
references: never load a resource from a user-writable or downloaded location without trusting its
origin.

### 6. Encrypted save (obfuscation, not security)

```gdscript
var file := FileAccess.open_encrypted_with_pass("user://save.dat", FileAccess.WRITE, "key")
```

The password ships inside the client and can be extracted, so this stops casual editing only.
For anything competitive, keep authoritative state on a server.

## Pitfalls

- **`FileAccess.open` returned `null`** — the directory does not exist, the path is not `user://`,
  or permissions failed. Check `FileAccess.get_open_error()` before using the handle.
- **Save written to `res://`** — works in the editor, fails in an exported build because `res://` is
  read-only. Use `user://`.
- **JSON contains nodes or objects** — `JSON.stringify` cannot serialize them and returns an empty
  string. Store plain dictionaries and IDs, rebuild nodes after load.
- **Counters come back as floats** — JSON has one number type. Cast with `int()`; store very large
  integers as strings.
- **Dictionary keys are not strings** — JSON object keys are strings by definition; keys like
  `Vector2(1, 2)` are lost. Convert keys to strings or use arrays of records.
- **First run crashes on load** — no file exists yet. Return defaults when
  `FileAccess.file_exists` is false.
- **Crash during save destroys the slot** — writing directly over the live file. Write a temp file
  and rename; keep a `.bak`.
- **Old save breaks new code** — no version field and no migration path. Add `version` from day one.
- **`get_var(true)` on a player-editable file** — object deserialization is a code-execution risk.
  Leave `allow_objects` at `false`.
- **Encryption treated as anti-cheat** — the key is in the build. Validate important state
  server-side.
- **Saving every frame** — disk churn and stutter. Save at checkpoints, on pause, and on
  `NOTIFICATION_WM_CLOSE_REQUEST`.
- **Quit-time save lost** — the process exits before the write completes. Save synchronously on
  quit or save continuously at safe points.

## References

- Read `references/formats-and-errors.md` for the format comparison, the `FileAccess`/`DirAccess`
  API tables, migration and backup strategy, encryption limits and a failure-path test checklist.

## Related skills

- `save-systems` — save-format design, slots, versioning strategy and cross-engine concerns.
- `godot-resources` — custom `Resource` classes and `.tres` data architecture.
- `godot-ui-control` — load/save menus and confirmation dialogs.
- `godot-multiplayer` — authoritative state when saves must sync across players.
- `godot-gdscript-headless-testing` — scripted saves and loads in CI.
- `roblox-datastores` — the equivalent persistence skill for Roblox.
