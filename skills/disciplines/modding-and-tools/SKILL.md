---
name: modding-and-tools
description: >
  Support mods and user content: manifest and versioning, load order/dependencies, content
  mounting, scripting sandboxes, saves with mods, Workshop/UGC publishing and moderation. Use for
  a modding API, Workshop integration, or when game updates break mods.
---

# Modding and tools

Mod support is an API contract with strangers. Design the contract (manifest, load order, content
paths, sandbox), version it, and make failures non-fatal. This is a **compositional** skill: pair
with `save-systems`, `editor-tooling` and `steam-publish`.

## When to use

- Use when adding mod loading, a modding API, Workshop/UGC publishing, or mod compatibility.
- Use when updates break mods or modded saves corrupt.

**When *not* to use:** in-game level editor for players (that is gameplay tooling); internal
designer tools only → `editor-tooling`; server plugins for your own backend → backend docs.

## Contract first

```json
{
  "id": "foo.combat-overhaul",
  "version": "1.4.2",
  "game_version": "1.12.0",
  "min_game_version": "1.10.0",
  "dependencies": [{ "id": "bar.ui-kit", "min": "2.0.0" }],
  "load_after": ["bar.ui-kit"],
  "entry": "scripts/main.lua",
  "content": ["data/", "textures/"]
}
```

- Stable `id`, semver `version`, explicit `game_version` compatibility.
- Fail closed on malformed manifests; log the mod path and reason.
- Resolve dependencies and load order before loading anything.

## Loading strategy

| Approach | Risk | Use when |
|----------|------|----------|
| Pure data (JSON/CSV/images) | low | balance, maps, skins |
| Content packs (PCK/pak/assetbundles) | medium | maps, models, audio |
| Sandboxed scripts (Lua/WASM) | medium | gameplay mods |
| Native assemblies/DLLs | high | trusted total conversions |

- Prefer data and content packs; they cannot execute arbitrary code.
- Sandbox scripts: no filesystem/network by default; expose a narrow API.
- Native code: require explicit user opt-in and warn about trust.
- Mount content into a virtual filesystem so base assets cannot be overwritten silently.

## Engine bindings

- **Godot**: load `.pck` with `ProjectSettings.load_resource_pack(path)`; scan `user://mods/*`;
  parse `mod.json`; add resource paths. Untrusted GDScript is not a sandbox — prefer data.
- **Unity**: Addressables/AssetBundles for content; Mono assemblies via reflection only with
  explicit consent; `Application.persistentDataPath/mods`.
- **Unreal**: `.pak` mounting with `FPakPlatformFile`; DataTables/DataAssets for data mods;
  Blueprint mods require editor-built assets.
- **Web/Electron**: JSON + image assets; JS mods need a sandboxed iframe/worker.

## Steam Workshop

Verified flow (`ISteamUGC`):

```text
create:  CreateItem(app_id, k_EWorkshopFileTypeCommunity) -> PublishedFileId
upload:  StartItemUpdate(app_id, file_id)
         SetItemTitle / SetItemDescription / SetItemContent(path)
         SetItemVisibility / SetItemTags
         SubmitItemUpdate(change_note) -> poll status
consume: GetNumSubscribedItems / GetSubscribedItems
         GetItemState -> k_EItemStateInstalled / k_EItemStateNeedsUpdate
         DownloadItem -> DownloadItemResult_t -> GetItemInstallInfo(folder)
```

- Enable Workshop + "ISteamUGC for file transfer" in the app settings first.
- Content lives in the returned folder; mount it as a mod root.
- Subscribe/unsubscribe from in-game UI (`SubscribeItem`/`UnsubscribeItem`).
- Validate the manifest inside the downloaded folder before loading.

## Compatibility and versioning

- Declare `min_game_version`; reject or warn on newer/older games.
- Keep a stable mod API; deprecate with warnings for one release before removal.
- On game update: mark incompatible mods, disable them, keep saves loadable.
- Never let one broken mod crash startup; isolate and report.

## Saves with mods

- Record active mod ids + versions in the save.
- On load, missing mods → warn and substitute defaults; do not silently delete content.
- Modded saves should be marked; achievements may be disabled by policy.
- Version the save schema; migrate per mod where possible.

## Moderation and safety

- Report/hide UGC; rate-limit uploads; scan filenames and sizes.
- Do not auto-execute downloaded code; opt-in per mod with a clear warning.
- Respect platform rules and local law for user content.
- Provide a "disable all mods" safe mode.

## Pitfalls

- **No manifest** → folder scanning, guessed load order, crashes. Require one.
- **Silent overwrite of base assets** → mods corrupt the game. Mount with priority and warn.
- **Hard dependency on load order** → undefined behavior. Topological sort by `load_after`.
- **Arbitrary code by default** → malware vector. Sandbox or opt in.
- **Mods break saves irreversibly** → missing-content handling. Substitute and warn.
- **No API versioning** → every update breaks mods. Semver + deprecation window.
- **One bad mod kills startup** → no isolation. Per-mod error boundary.
- **Workshop folder assumed stable** → path changes. Always query install info.

## Composition

- **Data/assets:** `godot-resources`, `unity-scriptableobjects`.
- **Saves:** `save-systems` for mod-aware schema and migration.
- **Publishing:** `steam-publish` for Workshop setup; `itch-publish` for manual mod packs.
- **Tools:** `editor-tooling` for a mod validator/packer.
- **Security:** `multiplayer-netcode` for server-side mod validation (never trust client mods).

## References

- Read `references/manifests-loading-and-workshop.md` for manifest validation, load-order
  pseudocode, Workshop state handling and a mod-support test checklist.
