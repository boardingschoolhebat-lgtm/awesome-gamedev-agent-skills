---
name: love2d-save
description: >
  Save and load LÖVE 11.5 game data with love.filesystem: identity and the save directory,
  versioned save tables with migrations, safe overwrite with a backup, text versus compressed
  binary files, and separate settings and slot saves. Use when a LÖVE game must persist progress
  or settings, or the request mentions love.filesystem, a save file, save slots, or a corrupt or
  vanishing LÖVE save. Targets LÖVE 11.5.
---

# LÖVE saves

Persist a LÖVE game's state through `love.filesystem`, which writes only into the per-game
**save directory** — never next to `main.lua`. This skill covers the identity, the format, the
write protocol and the migrations. Targets **LÖVE 11.5**.

## When to use

- Use when a LÖVE game must remember progress, unlocks, settings or level edits between runs.
- Use when a save is missing, corrupt, written to the wrong folder, or incompatible after a
  content update.

**When *not* to use:** save-slot *design* for any engine → `save-systems`; the game loop and
states → `love2d-core`; tile-level persistence of edited cells → `love2d-tilemap` plus this
skill; engine-neutral JSON schemas → `save-systems`.

## Core workflow

1. **Set the identity before the first write.** Put `t.identity = "my-game"` in `conf.lua`.
   `love.filesystem` then maps all relative paths into that save directory; print
   `love.filesystem.getSaveDirectory()` once while developing to see where files land.
2. **Choose one format and stay with it.** A Lua table literal (`return {...}`) parsed in an
   empty environment, a JSON library's output, or a binary blob via `love.data`. Do not mix.
3. **Version every save.** Store `version = N` inside the table and migrate forward on load.
4. **Write safely.** LÖVE has no `rename`, so write `.tmp`, read it back, copy the old file to
   `.bak`, then overwrite the real file. This bounds a crash to one good copy.
5. **Load defensively.** Check `getInfo`, cap the size, parse with `pcall`, validate the shape,
   migrate, and fall back to `.bak`, then to defaults. A missing save is normal, not an error.
6. **Separate settings from slots.** Settings are one small file written on change; slots are
   one file per slot, listed from the directory.
7. **Verify on a packaged build.** Run the `.love`/packaged executable, not only `love .`, and
   confirm the same save directory and file names are used.

## Patterns

### 1. Identity and the save directory

```lua
-- conf.lua
function love.conf(t)
    t.identity = "my-game"        -- folder name under LÖVE's save root
    t.version = "11.5"
end
```

```lua
-- main.lua, once, at startup
print(love.filesystem.getSaveDirectory())   -- e.g. .../love/my-game
print(love.filesystem.getIdentity())        -- "my-game"
```

`love.filesystem.setIdentity("my-game")` does the same at runtime, but only before anything
writes; the `conf.lua` field is simpler and applies from the first frame. Paths passed to
`love.filesystem` are always relative to the save directory (the game's own assets are read-only
and mounted separately).

### 2. Serialize a table to a Lua literal

```lua
local ESCAPES = { ["\\"] = "\\\\", ['"'] = '\\"', ["\n"] = "\\n", ["\r"] = "\\r", ["\t"] = "\\t" }

local function quote(s)
    return '"' .. s:gsub('[\\"\n\r\t]', ESCAPES) .. '"'
end

local function serialize(value)
    local kind = type(value)
    if kind == "table" then
        local parts = {}
        for k, v in pairs(value) do
            parts[#parts + 1] = "[" .. serialize(k) .. "]=" .. serialize(v)
        end
        return "{" .. table.concat(parts, ",") .. "}"
    elseif kind == "string" then
        return quote(value)
    elseif kind == "number" or kind == "boolean" then
        return tostring(value)
    else
        error("cannot save a " .. kind)
    end
end
```

This produces `return {["version"]=2,...}`, which is valid Lua and easy to read while debugging.
`pairs` order is not stable, so do not diff save files byte-for-byte; compare decoded tables.

### 3. Write with a backup (no `rename` in LÖVE)

```lua
local MAX_SAVE_BYTES = 1024 * 1024

local function read_file(name)
    if not love.filesystem.getInfo(name, "file") then return nil end
    return love.filesystem.read(name)
end

local function write_checked(name, text)
    local ok, err = love.filesystem.write(name, text)
    if not ok then return false, err end
    if love.filesystem.read(name) ~= text then
        return false, "write did not round-trip"
    end
    return true
end

local function save_slot(slot, data)
    love.filesystem.createDirectory("saves")
    local name = "saves/" .. slot .. ".lua"
    local text = "return " .. serialize(data)

    local ok, err = write_checked(name .. ".tmp", text)
    if not ok then return false, err end

    local old = read_file(name)
    if old then
        local ok_bak, err_bak = write_checked(name .. ".bak", old)
        if not ok_bak then return false, err_bak end
    end

    local ok_main, err_main = write_checked(name, text)
    if not ok_main then return false, err_main end

    love.filesystem.remove(name .. ".tmp")
    return true
end
```

Because `love.filesystem` has no move/rename, there is a short window where the main file is
being replaced. The `.bak` copy is what makes that window recoverable: a crash before the final
write leaves the old main file, a crash during it leaves the backup.

### 4. Load with fallbacks and migrations

```lua
local CURRENT_VERSION = 3

local function compile(text)
    if setfenv then                                   -- LuaJIT / Lua 5.1 (LÖVE 11 default)
        local chunk = assert((loadstring or load)(text, "save"))
        setfenv(chunk, {})                            -- no love, io, os or require
        return chunk
    end
    return assert(load(text, "save", "t", {}))        -- Lua 5.2+
end

local function decode(text)
    if #text > MAX_SAVE_BYTES then return nil, "save too large" end
    local ok, data = pcall(compile(text))
    if not ok or type(data) ~= "table" then return nil, "malformed save" end
    return data
end

local MIGRATIONS = {
    [1] = function(s) s.gold = s.money or 0; s.money = nil; s.version = 2; return s end,
    [2] = function(s) s.stats = s.stats or {}; s.version = 3; return s end,
}

local function migrate(save)
    local version = save.version or 1
    while version < CURRENT_VERSION do
        local step = MIGRATIONS[version]
        if not step then return nil, "no migration from version " .. version end
        save = step(save)
        version = save.version
    end
    return save
end

local function load_slot(slot)
    for _, name in ipairs({ "saves/" .. slot .. ".lua", "saves/" .. slot .. ".lua.bak" }) do
        local text = read_file(name)
        if text then
            local data = decode(text)
            if data then
                local ok, migrated = pcall(migrate, data)
                if ok and migrated then return migrated end
            end
        end
    end
    return nil
end
```

`love.filesystem.load` and `loadstring` **execute code**. Loading a save in an empty environment
removes access to `love`, `require`, `io` and `os`, which is why the loader above does it; a save
that only ever needs data still costs a compile, so cap its size. If the project already ships a
JSON library, prefer decoding JSON and skip code loading entirely.

### 5. Settings and slot listing

```lua
-- Settings: one small file, written when a value changes.
local function save_settings(settings)
    settings.version = 1
    return write_checked("settings.lua", "return " .. serialize(settings))
end

local function list_slots()
    local slots = {}
    for _, name in ipairs(love.filesystem.getDirectoryItems("saves")) do
        local info = love.filesystem.getInfo("saves/" .. name, "file")
        local slot = name:match("^(.-)%.lua$")
        if info and slot then
            slots[#slots + 1] = { slot = slot, size = info.size, modified = info.modtime }
        end
    end
    table.sort(slots, function(a, b) return a.modified > b.modified end)
    return slots
end

local function delete_slot(slot)
    love.filesystem.remove("saves/" .. slot .. ".lua")
    love.filesystem.remove("saves/" .. slot .. ".lua.bak")
end
```

`getInfo` returns `nil` for a missing path and a table (`type`, `size`, `modtime`) otherwise;
`modtime` is a Unix timestamp suitable for "most recent first".

### 6. Compress large saves

```lua
local function save_compressed(slot, data)
    local text = "return " .. serialize(data)
    local packed = love.data.compress("string", "zlib", text, 9)
    return write_checked("saves/" .. slot .. ".bin", packed)
end

local function load_compressed(slot)
    local text = read_file("saves/" .. slot .. ".bin")
    if not text then return nil end
    local ok, raw = pcall(love.data.decompress, "string", "zlib", text)
    if not ok then return nil end
    return decode(raw)
end
```

Compression pays off for large worlds and saves little on tiny ones; keep a plain-text format
during development so a broken save can be inspected by hand.

## Pitfalls

- **Save lands in the wrong folder** → no identity is set, so LÖVE writes under the default
  identity. Set `t.identity` in `conf.lua` before shipping; changing it later orphans old saves.
- **Works with `love .`, fails in a packaged build** → the save directory is per identity and per
  platform, not next to the executable. Log `getSaveDirectory()` in the packaged build.
- **`love.filesystem.write` failed silently** → it returns `success, message`; an unchecked
  failure looks like a save that never persisted. Check both values.
- **File is truncated after a crash** → the process died mid-write. Use the `.tmp` → verify →
  `.bak` → main protocol above; never write the live save in place first.
- **Save file runs code** → `love.filesystem.load`/`loadstring` execute whatever is in the file.
  Load into an empty environment and cap the size, or use a data format with no code.
- **Old saves fail after an update** → the schema changed without a migration. Bump `version` and
  add a migration step for every released version.
- **`version` is missing** → treat it as version `1`; that is what `save.version or 1` does, and
  it keeps pre-versioning saves loadable.
- **`pairs` ordering changes the file every run** → expected; save files are data, not fixtures.
  Do not hash them for change detection without canonical ordering.
- **`getInfo` says the file exists but `read` fails** → it is a directory or unreadable. Pass
  `"file"` as the second argument to `getInfo` and handle `nil`.
- **Deleting a slot leaves a resurrected save** → the `.bak` file was not removed with the main
  file. Delete both.
- **Settings and progress overwrite each other** → they are separate files; keep one writer per
  file and write settings only when they change.

## References

- Read `references/filesystem-and-migrations.md` for the filesystem API table, save-directory
  locations, the write/backup protocol, migration examples and a testing checklist.

## Related skills

- `save-systems` — engine-neutral slot design, schemas and player-facing save UX.
- `love2d-core` — the loop and screen states that trigger saves.
- `love2d-tilemap` — persisting edited tile grids through this save layer.
- `godot-save` / `unity-save` / `unreal-save` — the same concerns in other engines.
