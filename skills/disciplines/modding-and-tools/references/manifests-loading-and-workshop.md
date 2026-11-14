# Manifests, loading and Workshop

Depth for `modding-and-tools`: validation, load order, Workshop states and tests.

## Manifest validation

```text
required: id, version, game_version, min_game_version, entry/content
id:       reverse-domain or author.slug, stable forever
version:  semver
check:    duplicate ids, dependency cycles, missing deps, incompatible game version
```

- Reject with a readable error: `mods/foo/mod.json: dependency bar.ui-kit >= 2.0 missing`.
- Allow "load anyway" only for data-only mods, never native code.

## Load order

```text
mods = scan(mods_dir)
graph = {m.id: m.dependencies + m.load_after}
order = topological_sort(graph)      # stable tiebreak by id
for m in order: mount(m)
```

- Cycles → disable the cycle, keep the rest.
- Later mods override earlier ones only in explicit override paths.
- Record the resolved order in the log and the save.

## Content mounting

```text
base assets at priority 0
mod assets at priority 10 + index
lookup: highest priority wins; log shadowed base paths
```

- Never allow writes to the base install directory.
- Validate paths (no `..`, no absolute paths) to prevent traversal.

## Workshop states

```text
state = GetItemState(id)
if state & k_EItemStateNeedsUpdate: DownloadItem(id)
if state & k_EItemStateInstalled: folder = GetItemInstallInfo(id)
else: wait for DownloadItemResult_t
```

- Poll on a timer during a loading screen; do not block the main thread.
- Handle unsubscribe while installed: remove from active set, keep files until restart.
- Show download progress per item.

## Test checklist

1. Fresh install with 0 mods works.
2. Mod with missing dependency fails gracefully.
3. Dependency cycle does not hang startup.
4. Load order honored; overrides logged.
5. Malformed manifest rejected with path + reason.
6. Broken mod does not crash the game.
7. Save with mods loads without them (warn + substitute).
8. Save without mods loads with them (no corruption).
9. Workshop subscribe/download/update flow works; unsubscribe cleans up.
10. "Disable all mods" safe mode starts cleanly.
