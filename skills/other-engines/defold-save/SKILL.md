---
name: defold-save
description: >
  Save and load Defold games with sys.save, sys.load and sys.get_save_file: platform save paths,
  versioned tables and migrations, safe overwrite with os.rename and backups, separate settings
  and slots, corrupt-save recovery with pcall, and console save caveats. Use when a Defold game
  must persist progress or settings, or the request mentions a Defold save file, highscore file,
  sys.save, or a corrupt save. Targets Defold 1.14.0.
---

# Defold saves

Defold stores Lua tables with `sys.save`/`sys.load` at a path from `sys.get_save_file`; there is
no save-game asset type. This skill covers the path, the format, the write protocol and the
migrations. Targets **Defold 1.14.0**.

## When to use

- Use when a Defold game must remember progress, unlocks, settings or high scores between runs.
- Use when a save is missing, corrupt, lands in the wrong folder, or breaks after an update.

**When *not* to use:** save-slot design for any engine → `save-systems`; Defold script and
message basics → `defold-core`; keeping edited tile cells → `defold-tilemap` plus this skill;
console-specific save APIs are platform extensions, not `sys.*`.

## Core workflow

1. **Build the path once.** `sys.get_save_file(application_id, file_name)` returns an OS-specific
   absolute path under the user's application-support directory; it raises a Lua error if it
   cannot resolve one.
2. **Save a Lua table.** `sys.save(path, table)` returns a boolean; it raises on error. Check both
   outcomes.
3. **Load defensively.** `sys.load(path)` raises if the file is missing, corrupt or not written by
   `sys.save`; wrap it in `pcall` and fall back to defaults.
4. **Version the table.** A `version` field and forward-only migrations.
5. **Write safely.** Save to a temp file with `sys.save`, verify it loads, copy the old file to
   `.bak`, then `os.rename` the temp over the real file.
6. **Separate settings from slots.** Settings are one small file; progress is one file per slot.
7. **Verify in a bundle.** Paths differ between editor and packaged builds; log the resolved path
   once during development.

## Patterns

### 1. Save path and basic round trip

```lua
local APP_ID = "my_game"

local function save_path(name)
    -- OS-specific absolute path; raises if the path cannot be resolved.
    return sys.get_save_file(APP_ID, name)
end

local function read_table(name)
    local path = save_path(name)
    local ok, data = pcall(sys.load, path)
    if ok and type(data) == "table" then
        return data
    end
    return nil
end

local function write_table(name, data)
    local path = save_path(name)
    local ok, err = pcall(sys.save, path, data)
    if not ok then
        print("save failed: " .. tostring(err))
        return false
    end
    return true
end
```

`sys.get_save_file` is the only correct way to get a writable path on desktop, mobile and web;
hardcoding `game.project`-relative paths writes into the read-only bundle and fails on device.

### 2. Safe overwrite with a backup

```lua
local function save_slot(slot, data)
    local path = save_path("slot_" .. slot)
    local tmp = path .. ".tmp"
    local bak = path .. ".bak"

    if not write_table("slot_" .. slot .. ".tmp", data) then
        return false
    end

    -- Verify the temp file really loads before touching the real one.
    local ok, check = pcall(sys.load, tmp)
    if not ok or type(check) ~= "table" then
        os.remove(tmp)
        return false
    end

    -- No atomic replace primitive in sys.*; keep a backup, then rename over the original.
    if os.rename(path, bak) then
        -- best effort: the old file is now the backup
    end
    local renamed = os.rename(tmp, path)
    if not renamed then
        -- restore the previous save so the player keeps a working file
        os.rename(bak, path)
        return false
    end
    return true
end
```

- `sys.save` writes the whole file; a crash mid-write can truncate it. The temp+rename protocol
  bounds the damage to one good copy.
- `os.rename` is available in Defold's Lua; on some platforms renaming over an existing file
  fails, which is why the old file is moved to `.bak` first.
- Keep `.bak` until the next successful save; the loader tries the main file first.

### 3. Load with fallback and migration

```lua
local CURRENT_VERSION = 2

local function migrate(data)
    local version = data.version or 1
    if version > CURRENT_VERSION then
        return nil, "save is newer than this build"
    end

    if version == 1 then
        data.gold = data.money or 0
        data.money = nil
        data.version = 2
        version = 2
    end

    return data
end

local function load_slot(slot)
    for _, suffix in ipairs({ "", ".bak" }) do
        local data = read_table("slot_" .. slot .. suffix)
        if data then
            local migrated, err = migrate(data)
            if migrated then
                return migrated
            end
            print("cannot migrate save: " .. tostring(err))
        end
    end
    return nil
end
```

Never treat a missing `version` as version 0; `data.version or 1` keeps pre-versioning saves
loadable. Refuse a save from a newer build instead of loading it partially.

### 4. Settings and slot listing

```lua
local function save_settings(settings)
    settings.version = 1
    return write_table("settings", settings)
end

local function delete_slot(slot)
    os.remove(save_path("slot_" .. slot))
    os.remove(save_path("slot_" .. slot .. ".bak"))
end
```

- Settings live in `settings`, not in a slot; a volume change should not rewrite progress.
- Slot listing on desktop can use `io.popen`/`lfs`, but those are platform- and extension-dependent;
  keep a slot index table (`slots = {1, 2, 3}`) in settings or the game config instead.
- If a player-visible "delete save" exists, delete the `.bak` too or the slot returns.

### 5. What `sys.save` can store

- Tables of strings, numbers, booleans and nested tables; keys must be strings or numbers.
- No functions, userdata, metatables, or references to game objects; the loader returns plain
  data.
- Cycles are not supported; flatten or reference by id.
- Numbers keep their Lua type; very large integers on 32-bit builds need care.
- Store entity ids as strings/numbers and resolve them to objects after load; ids are not stable
  across sessions.

### 6. Console caveat

`sys.get_save_file`/`sys.save` work on desktop, mobile and web. On consoles, saves are associated
with a user/profile and are usually asynchronous through platform extensions; use those APIs and
treat their callbacks as the save completion. Do not assume the desktop path protocol applies.

## Pitfalls

- **Save works in the editor but not on device** → a relative path or one under the game bundle.
  Always use `sys.get_save_file`.
- **`sys.load` crashes on first run** → the file does not exist and `sys.load` raises. Always
  `pcall` it and default to a new save.
- **Corrupt save bricks the game** → no `pcall` and no `.bak`. Load with a fallback chain.
- **Save is truncated after a crash** → written directly to the live file. Use temp + verify +
  rename + backup.
- **Old saves fail after an update** → no version/migration. Add a migration per released schema.
- **`sys.save` returns false silently ignored** → disk full or permission error. Check the boolean
  and the `pcall` error, and tell the player.
- **Settings overwrite progress** → both written to the same file. Use separate files.
- **Deleting a slot resurrects it** → `.bak` left behind. Delete both files.
- **Storing game objects in the save table** → `sys.save` cannot serialize them. Store ids/data.
- **Console certification failure** → desktop save APIs used on console. Use the platform's
  user-associated save extension.

## References

- Read `references/paths-and-safe-writes.md` for the sys API table, platform path behavior, the
  write/backup protocol, migration patterns and a device test checklist.

## Related skills

- `defold-core` — scripts, messages and the build workflow that call this save layer.
- `defold-tilemap` — persisting edited tile data through this layer.
- `save-systems` — engine-neutral slot design and save UX.
- `godot-save` / `unity-save` / `love2d-save` — the same concerns in other engines.
