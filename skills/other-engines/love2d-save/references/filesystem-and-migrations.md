# love.filesystem, save layout and migrations (LÖVE 11.5)

Depth for `love2d-save`: exact function behaviour, where files land, and the failure modes worth
testing before shipping.

## API used by the skill

| Call | Signature | Behaviour |
|------|-----------|-----------|
| `love.filesystem.write` | `write(name, data[, size])` → `success, message` | Replaces the file; creates it if missing. Check both returns. |
| `love.filesystem.read` | `read(name[, size])` → `contents, size` | Returns `nil` plus an error string when missing/unreadable. |
| `love.filesystem.append` | `append(name, data[, size])` → `success, message` | Adds to the end; also creates the file. |
| `love.filesystem.getInfo` | `getInfo(path[, filter])` → `table` or `nil` | `type` = `"file"`/`"directory"`; also `size`, `modtime`. |
| `love.filesystem.createDirectory` | `createDirectory(name)` → `success` | Creates one level; parent must exist. |
| `love.filesystem.remove` | `remove(name)` → `success` | Removes a file or an **empty** directory. |
| `love.filesystem.getDirectoryItems` | `getDirectoryItems(dir)` → `table` | Names only, not paths; order is unspecified. |
| `love.filesystem.getSaveDirectory` | `getSaveDirectory()` → `string` | Absolute, platform-specific path. |
| `love.filesystem.getIdentity` | `getIdentity()` → `string` | Current write identity. |
| `love.filesystem.setIdentity` | `setIdentity(name[, append])` | Changes the write directory; do it before writing. |
| `love.filesystem.load` | `load(name)` → `chunk` or `nil, err` | **Compiles** a Lua file; calling it executes it. |
| `love.data.compress` | `compress(container, format, raw[, level])` | Formats: `"lz4"`, `"zlib"`, `"gzip"`, `"deflate"`. |
| `love.data.decompress` | `decompress(container, format, packed)` | Inverse; errors on corrupt input (use `pcall`). |

There is **no** `rename`, `move`, `copy` or `truncate` in `love.filesystem`; the backup protocol
in the skill exists because of that gap.

## Where saves live

The path is `getSaveDirectory()`, always under the OS's per-user data location and the identity:

| OS | Typical location |
|----|------------------|
| Windows | `%APPDATA%\LOVE\<identity>` |
| macOS | `~/Library/Application Support/LOVE/<identity>` |
| Linux | `$XDG_DATA_HOME/love/<identity>` (usually `~/.local/share/love/<identity>`) |
| Android/iOS | app-private storage; use `getSaveDirectory()` rather than guessing |

`love.filesystem` also mounts the game's source (the `.love` archive or folder) read-only. Reads
fall through to it, writes always go to the save directory — so `"data/level.lua"` can be read
from the game while `"saves/slot1.lua"` is created next to the save.

The `append` argument of `setIdentity` is for development tools that want several identities to
share a directory; do not use it for player saves.

## Save layout used here

```text
<identity>/
├── settings.lua            -- one small table, written on change
├── saves/
│   ├── slot1.lua           -- current save
│   ├── slot1.lua.bak       -- previous good copy
│   └── slot2.lua
```

Names are relative and use `/` on every platform; `love.filesystem` handles the separator.

## Write protocol, step by step

1. `createDirectory("saves")` — idempotent; a missing parent makes `write` fail.
2. Serialize to a string. Prefix `return ` once, at the top level, so the file is a Lua chunk.
3. `write(name .. ".tmp", text)`; check `success`.
4. `read(name .. ".tmp")` and compare with `text`; catches disk-full and encoding problems.
5. If the main file exists, `write(name .. ".bak", old_contents)`.
6. `write(name, text)`; check `success`.
7. `remove(name .. ".tmp")`.

If any step fails, leave the previous main file untouched and report the error to the player
(and log it); do not delete or overwrite the backup on failure.

## Migrations

Keep a table keyed by the **old** version, each step returning the next version:

```lua
local MIGRATIONS = {
    [1] = function(s)
        s.gold = s.money or 0
        s.money = nil
        s.version = 2
        return s
    end,
    [2] = function(s)
        s.stats = s.stats or { deaths = 0 }
        s.version = 3
        return s
    end,
}
```

Rules:

- Migrate on load, not on save; a save file is only rewritten when the player saves again.
- Never reuse a version number; a released schema is immutable.
- A migration must be pure data work (no `love.*` calls that need a window).
- Validate after migrating: required fields present, numbers finite, tables the expected shape.
- If a step is missing, refuse the save and offer a new game instead of loading a half-migrated
  table.
- Keep a test save for every released version in the repository and load each one in CI.

## Sandboxed loading

`compile()` in the skill uses `setfenv(chunk, {})` on LuaJIT/5.1 and `load(text, "save", "t", {})`
on 5.2+. Either way the chunk has no globals, so it cannot call `love`, `require`, `io` or `os`.
It can still allocate memory, which is why `decode` rejects files above `MAX_SAVE_BYTES` before
compiling. If the project has a JSON library, prefer it: data-only formats do not need a sandbox.

## Compression

```lua
local packed = love.data.compress("string", "zlib", text, 9)   -- level 0-9
local raw = love.data.decompress("string", "zlib", packed)     -- pcall this
```

- `"lz4"` is fastest but compresses less; `"zlib"` is a good default for save data.
- Compression is only worth it above roughly a few kilobytes; profile before adding it.
- A compressed save cannot be inspected in a text editor, so keep an uncompressed debug mode.
- Do not compress the `.bak` file differently from the main file; keep one format per slot.

## Testing checklist

1. Fresh profile: no save directory, first save creates it, game loads defaults.
2. Normal save, quit, relaunch: progress restored.
3. Delete the main file, keep `.bak`: the loader falls back and the game still starts.
4. Truncate the main file to half its length: `pcall` catches the parse error, `.bak` loads.
5. Fill the disk (or point the identity at a read-only path): `write` fails, the error is
   surfaced, the old save is intact.
6. Load a save from every released schema version; each migrates to `CURRENT_VERSION`.
7. Save from a packaged build on each target platform; confirm the path and the file list.
8. Save while a level edit is in progress; confirm the grid and the player position agree after
   reload.
