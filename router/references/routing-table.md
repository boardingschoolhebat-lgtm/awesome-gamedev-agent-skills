# Full routing table — every authored skill

The exhaustive `task → category → skill` lookup the router body summarizes. Every name here is
a real folder at `skills/<category>/<name>/SKILL.md`. Trigger words (`says:`) and file signals
(`files:`) are the cues that should select each skill. `*` in a binding is filled with the
**detected** engine (router body §1); where an engine lacks the exact skill, see "Binding gaps".

## Engine skills

### Godot (`skills/godot/`, target Godot 4.7) — read after `project.godot` is detected

| Skill | Pick it when the request says / file signal |
|-------|---------------------------------------------|
| `godot-gdscript` | "GDScript", `_ready`/`_process`, typing, `@export`, `await`; `*.gd` |
| `godot-nodes-scenes` | "scene", "node tree", "instance a scene", autoloads, `PackedScene`; `*.tscn` |
| `godot-signals-groups` | "signal", "emit", "connect", "groups", decoupling/observer |
| `godot-2d-movement` | "2D movement", "platformer controller", `CharacterBody2D`, `move_and_slide` |
| `godot-tilemap` | "tilemap", "tileset", "autotile", `TileMapLayer`; tileset `*.tres` |
| `godot-physics` | "rigidbody", "area2d", "collision layer", "raycast" (2D + 3D) |
| `godot-ui-control` | "UI", "Control node", "anchors", "theme", "HUD" |
| `godot-animation` | `AnimationPlayer`, `AnimationTree`, "blend", `Tween` |
| `godot-shaders` | "Godot shader", "gdshader", fragment/vertex, screen-reading; `*.gdshader` |
| `godot-3d-essentials` | "3D", `Camera3D`, `WorldEnvironment`, `GridMap`; `Node3D` |
| `godot-save` | "Godot save", save game/progress/settings, `FileAccess`, `user://`, `JSON.stringify`, `ConfigFile`, `ResourceSaver`, save migration |
| `godot-resources` | "custom Resource", "data resource", `.tres`, `ResourceLoader` |
| `godot-audio` | "Godot audio", "audio bus", "play sound/music", sync-to-beat |
| `godot-multiplayer` | "multiplayer", "RPC", "networked", `MultiplayerSpawner`; `@rpc` |
| `godot-export` | "export Godot", "build for web/windows", `export_presets.cfg` |
| `godot-csharp` | "Godot C#", "GodotSharp", "C# signals in Godot"; `*.cs` + `*.csproj` in a Godot project |
| `godot-gdscript-headless-testing` | "headless test", "run tests from CLI", `godot --headless --script`, CI job for `.gd` tests |

### Unity (`skills/unity/`, target Unity 6.3 LTS / 6000.3)

| Skill | Pick it when |
|-------|--------------|
| `unity-csharp-scripting` | "Unity script", `MonoBehaviour`, `Start`/`Update`, coroutines; `*.cs` + `*.asmdef` |
| `unity-3d-essentials` | "Unity 3D", first-person/third-person controller, 3D character controller, `CharacterController`, mouse look, orbit camera, slope/stair handling |
| `unity-input-system` | "Input System", `InputAction`, "action map"; `*.inputactions` |
| `unity-physics` | "Unity physics", `Rigidbody`, "collision layers", "joint" |
| `unity-2d-movement` | "Unity 2D movement", "2D character controller", `Rigidbody2D` platformer, `linearVelocity`, `MovePosition`, coyote time, jump buffer |
| `unity-animation` | "Animator", "state machine", "blend tree", "Mecanim"; `*.controller` |
| `unity-save` | "Unity save", save game/progress, `Application.persistentDataPath`, `JsonUtility`, `PlayerPrefs`, save migration, WebGL IndexedDB save |
| `unity-scriptableobjects` | `ScriptableObject`, "SO architecture", "data asset", event channels |
| `unity-tilemap-2d` | "Unity tilemap", "tile palette", "rule tile" |
| `unity-navmesh` | `NavMesh`, `NavMeshAgent`, "pathfinding in Unity" |
| `unity-build-pipeline` | "build Unity", "player settings", "IL2CPP", "Addressables" |

### Unreal (`skills/unreal/`, target UE 5.8)

| Skill | Pick it when |
|-------|--------------|
| `unreal-blueprints` | "Blueprint", "BP graph", "event graph"; Blueprint `*.uasset` |
| `unreal-cpp-gameplay` | "Unreal C++", `GameMode`, `Pawn`, `ACharacter`; `Source/**/*.cpp` + `*.Build.cs` |
| `unreal-2d-movement` | "Unreal 2D", "Paper2D", `PaperCharacter`, `PaperFlipbook`, plane constraint, 2D platformer/top-down character in Unreal; Paper 2D assets |
| `unreal-enhanced-input` | "Enhanced Input", "Input Mapping Context", `IA_`/`IMC_` |
| `unreal-behavior-trees` | "Behavior Tree", "Blackboard", `AIController`, `BTTask`; `BT_`/`BB_` |
| `unreal-niagara` | "Niagara", "VFX", "particle system"; `NS_`/`NE_` |
| `unreal-save` | "Unreal save", save slot, `USaveGame`, `SaveGameToSlot`, `LoadGameFromSlot`, `DoesSaveGameExist`, `AsyncSaveGameToSlot`, `.sav` |
| `unreal-packaging` | "package Unreal", "cook content", "shipping build" |

### Ebitengine (`skills/ebitengine/`, target v2.10.5 / Go 1.25+)

| Skill | Pick it when |
|-------|--------------|
| `ebitengine-game` | "Ebitengine", "Ebiten", "2D game in Go", `Update`/`Draw`/`Layout`, action input, sprites, text, audio, scenes, testing or builds in an Ebitengine game; `go.mod` requiring `github.com/hajimehoshi/ebiten/v2` plus game imports |

### Web engines (`skills/web-engines/`) — detected from `package.json` + imports

| Skill | Pick it when |
|-------|--------------|
| `phaser-core` | "Phaser", "Phaser scene", `preload`/`create`/`update`; dep `phaser` |
| `phaser-arcade-physics` | "Arcade Physics", "collider", "overlap", world bounds |
| `phaser-tilemap` | "Phaser tilemap", Tiled map, `createLayer`, `setCollisionByProperty`, tile collision, `addTilesetImage`, `putTileAt`; `*.json` Tiled maps |
| `pixijs-rendering` | "PixiJS", "Pixi sprite", "stage", `Container`; dep `pixi.js` |
| `threejs-scene-setup` | "three.js", `THREE.Scene`, `WebGLRenderer`, render loop; dep `three` |
| `threejs-gltf-loading` | "load gltf", `GLTFLoader`, `AnimationMixer`; `*.gltf`/`*.glb` |
| `threejs-materials-lighting` | `MeshStandardMaterial`, "lighting", "shadows", env maps |

### Other engines (`skills/other-engines/`)

| Skill | Pick it when |
|-------|--------------|
| `bevy-ecs` | "Bevy", "ECS system/query", `Commands`, "Bevy plugin"; `Cargo.toml` dep `bevy` |
| `pygame-core` | "pygame", "blit", "sprite group", game loop; `import pygame` |
| `pygame-tilemap` | "pygame tilemap", "blitting tiles", "tileset", tile collision, layer surface, camera offset, `subsurface`, `pytmx` |
| `love2d-core` | "LÖVE", "love2d", `love.draw`, `love.update(dt)`; `main.lua`/`conf.lua`/`*.love` |
| `love2d-tilemap` | "LÖVE tilemap", "sprite batch", "quad", "tileset", tile layers, tile collision, scrolling tile level, `newSpriteBatch`, `newQuad`; `*.lua` + tileset image |
| `love2d-save` | "LÖVE save", save file, save slots, `love.filesystem`, `getSaveDirectory`, settings file, save migration, corrupt save |
| `defold-core` | "Defold", collection/game object/component, `msg.post`, `on_message`, `on_input`, `acquire_input_focus`, `go.property`, `factory.create`, collection proxy, `bob.jar`, Defold build error; `game.project` + `*.collection`/`*.go`/`*.script` (target Defold 1.14.0) |
| `defold-ui` | "Defold GUI", "Defold HUD", menu/dialog/inventory screen, `.gui`, `gui_script`, `gui.new_text_node`, `gui.animate`, `gui.pick_node`, `gui.clone`, layout, anchor, adjust mode; `*.gui`/`*.gui_script` |
| `defold-tilemap` | "Defold tilemap", paint tiles, tile layers, tile collision, tilesource collision group, `tilemap.get_tile`, `tilemap.set_tile`, `tilemap.get_bounds`, world-to-tile; `*.tilemap`/`*.tilesource` |
| `defold-collision` | "Defold collision", `.collisionobject`, collision shape, collision group/mask, `collision_response`, `contact_point_response`, `trigger_response`, `physics.raycast`, falls through floor, trigger zone |
| `defold-sprite` | "Defold sprite", flipbook animation, atlas animation, `sprite.play_flipbook`, `animation_done`, `set_hflip`, pivot, sprite offset, playback rate; `*.sprite`/`*.atlas` |
| `roblox-luau` | "Roblox", "Luau", `RemoteEvent`, services; `*.luau` + `*.rbxl(x)` / Rojo |
| `roblox-datastores` | "DataStore", "save player data", `GetDataStore`; `DataStoreService` |
| `roblox-ui` | Roblox HUD/menu/inventory/shop, `ScreenGui`, `PlayerGui`, `UDim2`, `AutomaticSize`, `GuiService`, UI clipping/respawn, touch/gamepad focus, generic generated UI |
| `roblox-networking` | Roblox remotes/security/replication, `RemoteEvent`, `RemoteFunction`, `UnreliableRemoteEvent`, exploit, request spam, server authority, desync |
| `roblox-characters` | Roblox character/respawn/rig/movement/animation, `CharacterAdded`, `Humanoid`, `Animator`, R6/R15, Tool, stale character reference |
| `roblox-physics` | Roblox assembly/constraint/collision/query/ownership, `RaycastParams`, overlap, `CanQuery`, impulse, BodyMover, projectile/vehicle/knockback |
| `roblox-studio-workflow` | edit/inspect/test a Roblox place in Studio, Explorer, Script/LocalScript/ModuleScript placement, tags/Attributes, duplicate remotes/systems, Server & Clients, Output |
| `roblox-simulator-economy` | Roblox simulator/tycoon/clicker/idle economy, upgrade cost curve, `costGrowth`, buy max, income per second, rebirth/prestige requirement or multiplier, offline earnings, big-number suffixes (K/M/B/Qa), "1000K" display bug, currency exploit, save repair, paid eggs/crates/spins odds, `PolicyService` paid random items; pairs with `roblox-networking` + `roblox-datastores` |

## Disciplines (`skills/disciplines/`) — cross-engine concepts, load **with** the engine skill

| Concept skill | `says:` triggers | Pairs with (engine API skill) |
|---------------|------------------|-------------------------------|
| `create-game-assets` | art direction, game assets, sprite/sprite sheet, tileset, texture, icon, concept art, 3D prop, consistent style | engine importer/rendering skill; installed `imagegen` for raster generation when available |
| `game-ai` | enemy AI, behavior tree, state machine, steering, pathfinding | `unity-navmesh` / `unreal-behavior-trees` / Godot nav (`godot-nodes-scenes` + `godot-physics`) |
| `ai-behavior-trees-utility-ai` | behavior tree runtime, blackboard, action/condition node, selector/sequence/parallel, decorator, utility AI, scoring/response curve, consideration, hybrid AI | `game-ai` (FSM/BT/steering choice) / `unreal-behavior-trees` (engine BT/Blackboard assets) |
| `procedural-gen` | procedural generation, perlin/simplex noise, random seed, dungeon generator, wave function collapse (WFC) | engine tilemap/grid: `godot-tilemap` / `unity-tilemap-2d` / `godot-3d-essentials` |
| `dialogue-systems` | dialogue system, branching dialogue, Yarn Spinner, Ink, conversation tree; `*.yarn`/`*.ink` | engine UI: `godot-ui-control` / Unity UI |
| `save-systems` | save system, save/load, persistence, save slots; `save*.json`/`*.sav` | `roblox-datastores` / Godot IO / engine serialization |
| `audio-design` | audio design, adaptive music, audio mixer, ducking, SFX | `godot-audio` / Unity AudioMixer |
| `shader-programming` | shader, fragment shader, dissolve/outline effect, GLSL/HLSL; `*.gdshader`/`*.shader`/`*.hlsl` | `godot-shaders` / engine material docs |
| `physics-tuning` | physics feel, jitter/tunneling, fixed timestep, collision tuning | `godot-physics` / `unity-physics` |
| `level-design` | level design, whitebox/blockout, tilemap layout, pacing | `godot-tilemap` / `unity-tilemap-2d` / `godot-3d-essentials` (GridMap) |
| `input-systems` | input mapping, rebind controls, gamepad support, input buffering; `*.inputactions`/IMC | `unity-input-system` / `unreal-enhanced-input` / Godot InputMap |
| `game-feel` | game feel, juice, screen shake, hit-stop/freeze frame, squash & stretch, knockback, "make it punchy/satisfying" | engine animation/tween (`godot-animation`/`unity-animation`) + `camera-systems` (shake) + `audio-design` |
| `camera-systems` | camera follow, follow camera, deadzone, look-ahead, camera bounds/limits, third-person/orbit camera, first-person look, Cinemachine, camera jitter | `godot-2d-movement`/`godot-3d-essentials` / Unity Cinemachine 3 / Godot `Camera2D`/`Camera3D` |
| `game-ui-ux` | HUD, health bar, main/pause/settings menu, UI layout, anchors, UI scaling, aspect ratio, safe area, controller/keyboard menu nav | `godot-ui-control` / Unity UI (UGUI/UI Toolkit) |
| `performance-optimization` | performance, optimize, low/dropping FPS, frame drops, stutter, lag, frame budget, draw calls, batching, GC spikes, object pooling, profiler | engine profiler (Godot Monitors / Unity Profiler / Unreal `stat unit`) + `physics-tuning` |

## Genres (`skills/genres/`) — whole-game templates, **compose** engine + disciplines

| Genre skill | `says:` triggers | composes (bind `*` to the detected engine) |
|-------------|------------------|---------------------------------------------|
| `platformer` | platformer, jump mechanic, double jump, wall jump, wall slide, Mario-like | `godot-2d-movement`/`unity-2d-movement` (or engine physics) + `godot-tilemap`/`unity-tilemap-2d` + `level-design` + `camera-systems` + `game-feel` |
| `roguelike` | roguelike, procedural dungeon, permadeath, turn-based grid | `procedural-gen` + `godot-tilemap`/`unity-tilemap-2d` + `game-ai` + `save-systems` + `game-feel` |
| `rpg` | RPG, stats/leveling, inventory, quest system | `godot-resources`/`unity-scriptableobjects` + `dialogue-systems` + `save-systems` + `game-ui-ux` |
| `fps-shooter` | FPS, first-person shooter, hitscan, aim/shoot | `godot-3d-essentials`/`unity-3d-essentials`/`unreal-cpp-gameplay` + `input-systems` + `game-ai` + `camera-systems` + `game-feel` |
| `tower-defense` | tower defense, wave spawner, enemy path, tower targeting | `game-ai` + `godot-2d-movement`/engine movement + `level-design` + `game-ui-ux` |
| `card-game` | card game, deckbuilder, hand/deck/discard, TCG | `godot-resources`/`unity-scriptableobjects` + `game-ui-ux` + `godot-ui-control` (engine UI) |
| `visual-novel` | visual novel, VN, branching story, choice menu, Ren'Py; `*.ink`/`*.yarn`/`*.rpy` | `dialogue-systems` + `save-systems` + `game-ui-ux` |
| `survival-crafting` | survival game, crafting system, inventory, resource gathering | `save-systems` + `godot-resources`/`unity-scriptableobjects` + `procedural-gen` + `game-ui-ux` |
| `puzzle` | puzzle game, match-3, grid logic, tile-matching | `godot-tilemap`/`unity-tilemap-2d` + `level-design` + `game-feel` |

## Workflows (`skills/workflows/`) — process & shipping, engine-independent

| Workflow skill | `says:` / `files:` triggers |
|----------------|------------------------------|
| `game-jam` | game jam, 48-hour game, Ludum Dare / GMTK, jam submission |
| `prototype-fast` | prototype fast, vertical slice, MVP game, greybox |
| `steam-publish` | publish on Steam, Steamworks, store page, depot/build upload, Steam Deck compatibility review; `steam_appid.txt` |
| `itch-publish` | publish on itch, itch.io page, `butler push`, upload build; `.itch.toml` |

## Binding gaps (be honest; do not fabricate a skill)

For a **custom, proprietary, in-house, or unsupported engine**, keep the engine and use the
router's `custom-engines.md` reference. Load the relevant genre/discipline skills; replace
catalog engine bindings with verified project APIs. Engine-specific names in composition
tables are examples, not mandatory dependencies for portable genre systems.

The collection does not yet have a skill for every engine × concept. Several cross-cutting
concerns are now covered **engine-neutrally** by disciplines that pair with any detected engine —
camera work (`camera-systems`), HUD/menus (`game-ui-ux`), juice/feedback (`game-feel`), and
performance (`performance-optimization`) — so those are no longer gaps; bind them on top of the
engine. The remaining true gaps are engine-specific primitives. When a genre binding names a slot
the detected engine lacks, load the closest skill(s) and **state the gap** plainly:

- **No `*-2d-movement` for web.** A 2D Unreal character uses `unreal-2d-movement`; for Phaser,
  bind movement to `phaser-arcade-physics` and say there is no dedicated `phaser-2d-movement`
  skill.
- **3D essentials exist for Godot, Unity and Unreal.** Unity 3D characters and cameras use
  `unity-3d-essentials`; Unreal FPS work binds to `unreal-cpp-gameplay`; Godot uses
  `godot-3d-essentials`. No other engine has a dedicated 3D-essentials skill.
- **No `*-tilemap` for Bevy or Roblox.** Tile levels are covered by `godot-tilemap`,
  `unity-tilemap-2d`, `defold-tilemap`, `phaser-tilemap`, `love2d-tilemap` and
  `pygame-tilemap`; for Bevy and Roblox use `level-design` for the concept and the engine's
  rendering skill for drawing, and note the missing engine tilemap skill.
- **Engine-specific save skills exist for Godot, Unity, Unreal, LÖVE and Roblox.** `godot-save`
  covers `user://` and FileAccess formats, `unity-save` covers `persistentDataPath` and
  JsonUtility, `unreal-save` covers `USaveGame` slots, `love2d-save` covers `love.filesystem`
  identity and backups, and `roblox-datastores` covers DataStores; `save-systems` owns the design
  for other engines, including pygame.
- **Ebitengine uses one engine skill with focused references.** Bind engine movement,
  collision, rendering/camera, UI, audio, data/save and build slots to `ebitengine-game`;
  open only the matching reference. A puzzle/card request does not require a platformer
  scaffold. The Tiled loader is deliberately constrained, not a complete editor importer.
  Networking guidance does not supply transport/matchmaking; native 3D is outside this
  2D skill. Never substitute another engine's API to hide one of these gaps.
- **Defold has core, GUI, tilemap, collision and sprite skills.** Bind movement, input,
  spawning, level loading and build slots to `defold-core`, HUD/menus to `defold-ui`
  (+ `game-ui-ux`), tile levels to `defold-tilemap` (+ `level-design`), collision objects to
  `defold-collision` (+ `physics-tuning`), and flipbooks to `defold-sprite` (+ `game-feel`).
  These are the documented Defold primitives; movement stays engine-core + `input-systems`,
  and there is no Defold-specific save or camera skill.
