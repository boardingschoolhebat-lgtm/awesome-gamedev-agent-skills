---
name: bevy-save
description: >
  Persist a Bevy 0.20 game with serde: save resources and plain data, serialize to JSON or RON,
  write atomically through a temp file and rename, version and migrate saves, keep settings
  separate from slots, and load on Startup without serializing entities or asset handles. Use
  when a Bevy game needs save/load, save slots, or recovery from a corrupted save. Targets Bevy
  0.20.
---

# Bevy saves

Bevy has no save system: persistence is `serde` plus Rust's filesystem API, driven from a system
or a startup step. This skill defines the data, the file, the write protocol and the migrations.
Targets **Bevy 0.20**.

## When to use

- Use when a Bevy game must remember progress, unlocks, settings or run state between launches.
- Use when a save fails to deserialize after a refactor, or a save must survive a schema change.

**When *not* to use:** slot design and player-facing save UX → `save-systems`; ECS structure and
scheduling → `bevy-ecs`; asset loading → `bevy` asset docs; engine-neutral persistence → the
`save-systems` discipline.

## Core workflow

1. **Model the save as plain data.** A `#[derive(Resource, Serialize, Deserialize)]` struct of
   primitives, `String`, `Vec`, `BTreeMap` and other save structs. Never serialize `Entity`,
   `Handle<T>`, `Transform` hierarchies or component ids: they differ between runs.
2. **Pin the crates.** Read `Cargo.toml`/`Cargo.lock`; add `serde` with `derive` and one format
   crate (`serde_json` or `ron`). Do not silently upgrade Bevy or serde majors.
3. **Choose the save directory.** A per-user data directory (for example via the `directories`
   crate), never the working directory or the asset folder.
4. **Version the schema.** `version: u32` in the root save struct, with explicit migration
   functions for every released version.
5. **Write atomically.** Serialize to a string, write `save.json.tmp`, `sync_all()`, back up the
   old file, then `std::fs::rename(tmp, save)`.
6. **Load on `Startup` (or a loading state).** Read, parse, validate, migrate, then
   `commands.insert_resource(...)`. Keep the load fallible: a bad save starts a new game, it does
   not panic.
7. **Verify with a round-trip test.** Serialize, deserialize, compare the fields you care about;
   run it in CI without a window.

## Patterns

### 1. Cargo.toml and the save type

```toml
[dependencies]
bevy = "0.20"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

```rust
use bevy::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

const SAVE_VERSION: u32 = 2;

#[derive(Resource, Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct SaveData {
    pub version: u32,
    pub gold: u64,
    pub unlocked: Vec<String>,
    pub levels: BTreeMap<String, LevelRecord>,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct LevelRecord {
    pub best_time: f32,
    pub stars: u8,
}

impl Default for SaveData {
    fn default() -> Self {
        Self {
            version: SAVE_VERSION,
            gold: 0,
            unlocked: vec!["level-1".into()],
            levels: BTreeMap::new(),
        }
    }
}
```

`BTreeMap` keeps the file stable between runs; `HashMap` iteration order changes the bytes, which
makes diffs and hashes noisy. `#[serde(default)]` on new fields lets an older save load without a
migration when the default is correct.

### 2. Save directory and paths

```rust
use std::path::PathBuf;

fn save_dir() -> PathBuf {
    // `directories` maps this to %APPDATA%, ~/Library/Application Support,
    // and $XDG_DATA_HOME (or ~/.local/share) respectively.
    directories::ProjectDirs::from("com", "studio", "my-game")
        .expect("no home directory")
        .data_dir()
        .join("saves")
}
```

If the project avoids the `directories` crate, build the same path from `std::env::var_os`:
`APPDATA` on Windows, `HOME/Library/Application Support` on macOS, `XDG_DATA_HOME` or
`HOME/.local/share` elsewhere. Create the directory with `std::fs::create_dir_all` before writing.

### 3. Atomic write with a backup

```rust
use std::fs;
use std::io::Write;

fn write_save(path: &std::path::Path, data: &SaveData) -> std::io::Result<()> {
    let text = serde_json::to_string_pretty(data)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;

    fs::create_dir_all(path.parent().unwrap())?;
    let tmp = path.with_extension("json.tmp");
    {
        let mut file = fs::File::create(&tmp)?;
        file.write_all(text.as_bytes())?;
        file.sync_all()?;                       // content is on disk before the rename
    }

    if path.exists() {
        fs::copy(path, path.with_extension("json.bak"))?;
    }
    fs::rename(&tmp, path)?;                    // replaces an existing file on Unix and Windows
    Ok(())
}
```

`std::fs::rename` replaces the destination on both Unix and Windows, but only within one
filesystem; `path.with_extension` keeps the temp file in the same directory. On a crash before
the rename, the old save is intact; after it, the new save is complete.

### 4. Load, validate and migrate

```rust
fn load_save(path: &std::path::Path) -> Option<SaveData> {
    for candidate in [path.to_path_buf(), path.with_extension("json.bak")] {
        let Ok(text) = fs::read_to_string(&candidate) else { continue };
        let Ok(mut save) = serde_json::from_str::<SaveData>(&text) else { continue };
        if save.version > SAVE_VERSION {
            warn!("save {} is newer than this build", save.version);
            continue;
        }
        if migrate(&mut save).is_err() {
            continue;
        }
        return Some(save);
    }
    None
}

fn migrate(save: &mut SaveData) -> Result<(), String> {
    while save.version < SAVE_VERSION {
        match save.version {
            1 => {
                save.levels.retain(|_, record| record.stars > 0);
                save.version = 2;
            }
            other => return Err(format!("no migration from version {other}")),
        }
    }
    Ok(())
}
```

Cap the file size before parsing if saves are large (`fs::metadata(...).len()`), and clamp values
after parsing: a hand-edited save is untrusted input.

### 5. Systems that use the save

```rust
fn main() {
    App::new()
        .add_plugins(DefaultPlugins)
        .insert_resource(SaveData::default())
        .add_systems(Startup, load_on_startup)
        .add_systems(Update, autosave_on_checkpoint)
        .run();
}

fn load_on_startup(mut commands: Commands) {
    if let Some(save) = load_save(&save_dir().join("save.json")) {
        commands.insert_resource(save);
    }
}

fn autosave_on_checkpoint(save: Res<SaveData>, mut last: Local<u64>) {
    if save.gold == *last {
        return;                                  // nothing changed since the last write
    }
    if let Err(error) = write_save(&save_dir().join("save.json"), &save) {
        error!("save failed: {error}");
        return;
    }
    *last = save.gold;
}
```

`Local<T>` gives a system its own private state without adding a resource. Write from a system
that runs on a deliberate event, not every frame; for a large save, hand the string to a worker
thread and poll the result instead of blocking the frame.

### 6. Settings and slots

```rust
#[derive(Resource, Serialize, Deserialize, Default)]
pub struct Settings {
    pub master_volume: f32,
    pub fullscreen: bool,
}

fn slot_path(slot: &str) -> std::path::PathBuf {
    save_dir().join(format!("{slot}.json"))
}

fn list_slots() -> Vec<String> {
    let Ok(entries) = fs::read_dir(save_dir()) else { return Vec::new() };
    entries
        .filter_map(|entry| entry.ok())
        .filter_map(|entry| {
            let name = entry.file_name().to_string_lossy().into_owned();
            name.strip_suffix(".json").map(str::to_owned)
        })
        .collect()
}
```

Keep settings in their own file written on change; progress slots are one file per slot. Do not
put both in one file: a settings toggle then rewrites the progress save.

## Pitfalls

- **`Entity` or `Handle<T>` in the save struct** → ids and handles are runtime values and do not
  survive a restart. Save stable ids (`String`, `u64`) and resolve them to entities on load.
- **Serializing a whole component with `#[derive(Component, Serialize)]`** → works only while the
  component contains save-safe data. Keep a separate save DTO; components change with gameplay
  code and silently break old saves.
- **`HashMap` order changes the file every run** → use `BTreeMap` for saved maps.
- **NaN/infinity in a JSON save** → JSON cannot represent them; `serde_json` fails to serialize
  or produces a value other tools reject. Sanitize floats before saving.
- **Save written into `assets/`** → assets are read-only in a packaged build and are not a user
  data location. Use a data directory.
- **`rename` fails with "cross-device link"** → the temp file is on another filesystem. Create it
  in the destination directory.
- **Save lost when two systems write** → two writers to one path. Serialize saves through one
  system, or use a queue resource.
- **Load panics on a corrupt file** → do not `unwrap` the deserialize; fall back to the backup and
  then to defaults.
- **New field breaks every old save** → add `#[serde(default)]`, or a migration step, and bump
  the version.
- **Version check happens after using fields** → a newer save may have a different shape. Check
  `version` before anything else.
- **Autosave every frame** → serialization and disk I/O on the main thread stall the frame. Save
  on checkpoints, or move the write to a task.

## References

- Read `references/serde-files-and-migrations.md` for the crate/API table, JSON versus RON, the
  write protocol, migration patterns and a round-trip testing checklist.

## Related skills

- `bevy-ecs` — resources, systems, `Local<T>` and startup ordering.
- `save-systems` — engine-neutral slot design, schemas and save UX.
- `godot-save` / `unity-save` / `unreal-save` / `love2d-save` — the same concerns per engine.
