# Paths, sys.save and safe writes (Defold 1.14.0)

Depth for `defold-save`: where files go, what the sys API guarantees, and how to keep a save
loadable across crashes and content updates.

## API used by the skill

| API | Form | Notes |
|-----|------|-------|
| `sys.get_save_file` | `(application_id, file_name)` → `path` | OS-specific absolute path; raises on failure. `DM_SAVE_HOME` overrides the base. |
| `sys.save` | `(filename, table)` → `bool` | Writes the table; raises on error. |
| `sys.load` | `(filename)` → `table` | Raises if missing/corrupt/not a sys.save file. |
| `os.rename` | `(old, new)` → `bool, err` | Used for the temp→main and main→backup steps. |
| `os.remove` | `(filename)` → `bool, err` | Delete a file. |
| `io.open` | standard Lua | For text/binary formats outside `sys.save`. |
| `sys.serialize` | `(table)` → `string` | Serialize a table to a string (debug/inspection). |
| `sys.deserialize` | `(string)` → `table` | Inverse; useful for tests. |

`sys.*` functions operate on absolute paths; `sys.get_save_file` is the supported way to obtain
one.

## Path behavior

| Platform | Typical location |
|----------|------------------|
| Windows | `%APPDATA%\<application_id>\<file>` |
| macOS | `~/Library/Application Support/<application_id>/<file>` |
| Linux | `~/.local/share/<application_id>/<file>` (XDG data dir) |
| iOS/Android | app sandbox application-support directory |
| HTML5 | browser-managed storage (IndexedDB); may be cleared by the user |

- `application_id` is the Defold application id (`game.project` → project → title/id), not an
  arbitrary string; use one stable id for the whole game.
- `DM_SAVE_HOME` overrides the base directory, which is useful for tests and CI.
- Never write next to the bundle or under `/res`; those are read-only on device and in HTML5.
- Console platforms associate saves with a user; use the platform extension instead.

## Write protocol

1. `path = sys.get_save_file(app_id, name)`.
2. `sys.save(path .. ".tmp", data)` inside `pcall`; check the boolean.
3. `sys.load(path .. ".tmp")` inside `pcall`; verify it returns a table.
4. If the main file exists, `os.rename(path, path .. ".bak")`.
5. `os.rename(path .. ".tmp", path)`; on failure, restore `.bak` and report.
6. Keep `.bak` until the next successful save.

There is no atomic replace primitive in `sys.*`; `os.rename` is the closest and may fail when the
destination exists on some platforms, hence step 4.

## Table constraints

- Supported values: `nil` (absent), booleans, numbers, strings, and nested tables.
- Unsupported: functions, userdata, threads, metatables with behavior, cycles.
- Keys: strings or numbers; mixed key types are fine but keep them consistent for readability.
- Type stability: loading returns the types you saved; do not rely on implicit conversions.
- Size: keep saves small (KBs). Large worlds need chunking or a compact binary format via
  `io.open`.

## Migration example

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

local function migrate(save)
    local version = save.version or 1
    while version < CURRENT_VERSION do
        local step = MIGRATIONS[version]
        if not step then return nil, "no migration from " .. version end
        save = step(save)
        version = save.version
    end
    return save
end
```

- Migrate on load; write only when the player saves.
- Never reuse a version number.
- Keep a fixture save per released version and load each one in a CI test.
- Refuse a save whose version is above the build's `CURRENT_VERSION`.

## Testing checklist

1. Fresh install: no save, first load returns defaults, first save creates the file.
2. Save, quit, relaunch: progress restored.
3. Truncate the main file: `pcall` catches it and `.bak` loads.
4. Remove the main file: `.bak` loads.
5. Make the directory read-only: save returns false / pcall errors, old save intact.
6. Load every fixture version: each migrates to `CURRENT_VERSION`.
7. Delete a slot: both main and `.bak` gone.
8. Bundle on desktop, mobile and HTML5: path resolves and the save survives a restart.
9. Console (if targeted): platform save extension used, asynchronous completion handled.
