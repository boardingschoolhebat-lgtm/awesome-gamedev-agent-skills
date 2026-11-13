# serde, save files and migrations (Bevy 0.20)

Depth for `bevy-save`: the crates and calls involved, the write protocol, and the checks that keep
a save loadable across content updates.

## Crates and APIs

| Item | Signature / use | Notes |
|------|-----------------|-------|
| `serde` | `#[derive(Serialize, Deserialize)]` | Add `features = ["derive"]`. |
| `serde_json` | `to_string_pretty` / `from_str` | Human-readable, rejects non-finite floats. |
| `ron` | `to_string_pretty` / `from_str` | Rust-friendly format; pin the version you test. |
| `std::fs::File` | `create`, `write_all`, `sync_all` | `sync_all` flushes to disk before the rename. |
| `std::fs::rename` | `rename(from, to)` | Replaces `to` on Unix and Windows; same filesystem only. |
| `std::fs::copy` | `copy(from, to)` | Backup copy; does not preserve all metadata. |
| `std::fs::read_to_string` | `read_to_string(path)` | Fails on missing file or invalid UTF-8. |
| `directories::ProjectDirs` | `data_dir()`, `config_dir()` | Per-OS user directories. |
| `bevy::prelude::Resource` | `#[derive(Resource)]` | Since 0.19 `Resource` extends `Component`; derive only `Resource`. |
| `Commands::insert_resource` | `commands.insert_resource(value)` | Deferred insertion; applied at the next sync point. |
| `Local<T>` | `mut last: Local<u64>` | Per-system private state, not saved. |

## JSON versus RON

| | serde_json | ron |
|-|------------|-----|
| Readability | Good | Good, Rust-shaped |
| Ecosystem familiarity | High | Bevy-oriented |
| Enums | Externally tagged by default | Native syntax |
| Non-finite floats | Error | Not reliably portable |
| Schema tooling | Broad | Narrower |

Pick one and keep it for the project's lifetime; converting formats is a migration of its own.
`serde_json` is the safer default when saves may be inspected or edited by players.

## File layout

```text
<data dir>/
├── settings.json          -- small, written on change
└── saves/
    ├── slot1.json         -- current progress
    ├── slot1.json.bak     -- previous good copy
    └── slot2.json
```

- `path.with_extension("json.tmp")` keeps the temp file beside the target, so `rename` stays on
  one filesystem.
- Keep the backup name derived from the target (`with_extension("json.bak")`), so listing slots
  can skip it with a suffix check.
- Create the directory once with `create_dir_all`; `File::create` does not create parents.

## Write protocol

1. Serialize fully into a `String` (fail before touching the disk).
2. `File::create(tmp)`, `write_all`, `sync_all`.
3. If the target exists, `fs::copy(target, backup)`.
4. `fs::rename(tmp, target)`.
5. On any error, remove the temp file and surface the error; never leave a `.tmp` that later
   looks like a save.

A crash before step 4 leaves the old save; after step 4 the new save is complete. The backup
covers the case where the new save is complete but semantically wrong (for example a migration
bug discovered on the next load).

## Migration patterns

```rust
fn migrate(save: &mut SaveData) -> Result<(), String> {
    while save.version < SAVE_VERSION {
        match save.version {
            1 => {
                save.levels.retain(|_, record| record.stars > 0);
                save.version = 2;
            }
            2 => {
                save.gold = save.gold.saturating_mul(1);   // example: no-op change
                save.version = 3;
            }
            other => return Err(format!("no migration from version {other}")),
        }
    }
    Ok(())
}
```

- Migrate on load, not on save.
- Never reuse a version number.
- Keep old save fixtures in `tests/fixtures/` and load each in CI.
- A missing migration is an error, not a silent default: a half-migrated save is worse than a
  refused one.
- `#[serde(default)]` handles added fields; it does not handle renamed or retyped ones.

## Round-trip testing

```rust
#[test]
fn save_round_trip() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("slot1.json");
    let save = SaveData { gold: 42, ..SaveData::default() };

    write_save(&path, &save).unwrap();
    let loaded = load_save(&path).unwrap();

    assert_eq!(loaded, save);
    assert!(!path.with_extension("json.tmp").exists());
}
```

Add tests for: corrupt JSON falls back to `.bak`, a newer version is refused, every fixture
version migrates, and a `HashMap`-free save produces identical bytes on two runs.

## Engine notes

- Run the load in `Startup` or a dedicated loading state; systems that read the save then order
  after it. `Commands` insertion is deferred, so a system in the same schedule may still see the
  default resource — use `.chain()` or load in an earlier schedule.
- Do not save `Entity` or `Handle<T>`; store stable ids and rebuild handles/entities on load.
- Keep save DTOs separate from gameplay components: components gain fields and change types, and
  a save DTO is a compatibility boundary you can version.
- Autosave off the main thread for big saves: serialize on the main thread (the data lives in the
  ECS), then write on a worker and poll for completion.
- Bevy's asset folder is read-only in a packaged build; a save in `assets/` will fail or be
  discarded on update.
