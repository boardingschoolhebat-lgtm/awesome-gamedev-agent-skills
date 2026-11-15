---
name: flame-engine
description: >
  Build 2D games in Dart/Flutter with Flame 1.38: FlameGame and the component tree, World and
  CameraComponent, sprites and animation, collision detection, keyboard/tap input, audio, assets
  and web/mobile builds. Use for a Flutter Flame project.
---

# Flame engine

Flame is a component framework on top of Flutter: Flutter owns the app, widgets and lifecycle;
Flame owns the game loop and the component tree. You compose small components instead of one
giant game class. This is an **engine** skill: pair it with genre and discipline skills.

## When to use

- Use for a Dart/Flutter game using `flame`, or when adding a game screen to a Flutter app.
- Use when components do not update, collisions never fire, or the camera shows nothing.

**When *not* to use:** a Flutter app without a game loop → plain Flutter; a web game →
`phaser-game`/`pixijs-game`; Godot/Unity → their engine skills.

## Versions

- Flame **1.38.2** stable (Dart 3.11+). `2.0.0-dev` exists — do not adopt it for a production
  project without an explicit migration request.
- Optional packages: `flame_audio`, `flame_tiled`, `flame_forge2d`, `flame_spine`.

## Setup

```yaml
dependencies:
  flutter:
    sdk: flutter
  flame: ^1.38.2
  flame_audio: ^2.11.0   # check pub.dev for the current compatible version
```

```dart
void main() => runApp(GameWidget(game: MyGame()));

class MyGame extends FlameGame with HasCollisionDetection {
  @override
  Future<void> onLoad() async {
    world.add(Player(position: Vector2.zero()));
    camera.follow(world.children.query<Player>().first, maxSpeed: 300);
  }
}
```

- `GameWidget` is a normal Flutter widget; menus, settings and overlays can be Flutter widgets.
- Do not construct the game inside `build` — it is recreated on every rebuild. Use a field or
  `GameWidget.controlled(gameFactory: MyGame.new)`.
- `FlameGame` already owns a `world` and a `camera`; add gameplay to `world`, HUD to
  `camera.viewport`.

## Component tree

```text
FlameGame
├── World            # gameplay components, camera renders it
│   ├── Player
│   └── Enemy
└── CameraComponent
    ├── Viewport     # HUD components
    └── Viewfinder
```

- `Component` has `onLoad` (once, async), `onMount`, `update(dt)`, `render`, `onRemove`.
- `PositionComponent` adds `position`, `size`, `scale`, `angle`, `anchor`.
- `add`/`addAll` mount children; `removeFromParent()` detaches; `findGame()` reaches the game.
- Use `HasGameReference<MyGame>` for a typed game field instead of casting.
- `priority` controls update/render order; lower renders first.

## Coordinates and rendering

- World coordinates are independent of screen pixels; the default camera centers `(0,0)`.
- `anchor` decides which point `position` refers to (`Anchor.center` for characters).
- `Flame.images.load('player.png')` caches images; wrap in `Sprite`.
- `SpriteComponent(sprite: sprite, size: Vector2.all(32), anchor: Anchor.center)`.
- Animation: `SpriteAnimation.fromFrameData(image, SpriteAnimationData.sequenced(...))` and
  `SpriteAnimationComponent(animation: ..., size: ...)`.
- Batch static art into a tileset/atlas; avoid loading the same asset in every component.
- Declare assets under `flutter: assets:` in `pubspec.yaml`; paths are package-relative.

## Update loop

```dart
@override
void update(double dt) {
  super.update(dt);            // children update after you unless priority says otherwise
  position += velocity * dt;   // dt is in SECONDS
}
```

- `dt` is seconds, not milliseconds; cap large values after a pause.
- Do physics/movement in `update`, drawing in `render`; keep `render` allocation-free.
- For deterministic simulation, accumulate `dt` and step at a fixed rate.
- Pause the game via `pauseEngine()`/`resumeEngine()`; pause audio separately.

## Camera

```dart
camera.follow(player, maxSpeed: 300);
camera.setBounds(Rectangle.fromLTRB(0, 0, levelWidth, levelHeight));
camera.viewfinder.zoom = 2;
camera.viewport.add(HudComponent());
```

- `CameraComponent.withFixedResolution(width: 800, height: 600)` gives a stable design resolution.
- `camera.setBounds` keeps the view inside the level; test at the edges.
- Convert screen→world with `camera.viewport.globalToLocal` / `camera.globalToLocal` as appropriate
  for the coordinate space you are in.
- A second camera can render a minimap from the same world.

## Collision detection

```dart
class Player extends PositionComponent with CollisionCallbacks {
  @override
  Future<void> onLoad() async {
    size = Vector2.all(32);
    anchor = Anchor.center;
    add(RectangleHitbox());
  }

  @override
  void onCollisionStart(Set<Vector2> points, PositionComponent other) {
    if (other is Enemy) takeDamage(1);
    super.onCollisionStart(points, other);
  }
}
```

- The game needs `HasCollisionDetection` (or a subtree with it).
- Hitboxes are children; they follow the parent transform. Match hitbox size to the sprite.
- Callbacks: `onCollisionStart`, `onCollision`, `onCollisionEnd`.
- Fast movers can tunnel; use `Raycast`/swept checks or smaller steps.
- Broadphase first; avoid O(n²) logic in `onCollision`.

## Input

- Game-level keys: `KeyboardEvents` + `onKeyEvent(KeyEvent, Set<LogicalKeyboardKey>)`.
- Component-level keys: `KeyboardHandler` + `HasKeyboardHandlerComponents` on the game
  (do not mix with `KeyboardEvents`).
- Pointer: `TapCallbacks` (`onTapDown`, `onTapUp`, `onTapCancel`), `DragCallbacks` for drag.
- Use `LogicalKeyboardKey` and `KeyDownEvent`/`KeyUpEvent`; never hardcode key codes.
- On mobile, provide touch controls; test both input paths.

## Audio

```dart
await FlameAudio.play('hit.wav');
await FlameAudio.bgm.play('theme.mp3');
final pool = await AudioPool.createFromAsset(path: 'shot.wav', maxPlayers: 8);
```

- Short SFX via `FlameAudio.play`/`AudioPool`; music via `FlameAudio.bgm`.
- Preload at startup; creating players per shot causes hitches.
- Pause/resume with the game; respect a mute setting and platform silent mode.

## Save data

- Flame has no save system: use `shared_preferences` for small values or `path_provider` + JSON
  for a full save.
- Serialize a plain state object, version it, write to a temp file, then rename.
- Never serialize `Component` trees; rebuild components from data.
- Test load with a missing/corrupt file and an old version.

## Build and ship

- `flutter build web`, `flutter build apk --release`, `flutter build windows`, `flutter build ipa`.
- Web: keep the first asset bundle small; show a loading screen during `onLoad`.
- Verify on a real device for touch, safe areas and audio focus.
- `flutter test` for pure logic; golden tests for UI if already used.

## Pitfalls

- **Nothing renders** → components added to `game` instead of `world`. Add to `world`.
- **Game recreated** → constructed in `build`. Hold it in a field/`controlled`.
- **Movement too fast/slow** → `dt` treated as ms. It is seconds.
- **Collisions never fire** → missing `HasCollisionDetection` or hitbox child.
- **Hitbox offset** → anchor/size mismatch. Center the anchor and size the hitbox.
- **Camera stuck** → bounds smaller than viewport, or following a component not in `world`.
- **Asset not found** → not declared in `pubspec.yaml` or wrong path.
- **Keyboard dead** → `KeyboardHandler` without `HasKeyboardHandlerComponents`.
- **Jank** → allocations/image loads in `update`/`render`; preload and pool.
- **Audio keeps playing after pause** → pause `FlameAudio.bgm` with the engine.

## Composition

- **Genres:** `platformer`, `bullet-hell`, `roguelike`, `puzzle`.
- **Disciplines:** `game-feel`, `camera-systems`, `animation-systems`, `save-systems`,
  `performance-optimization`, `game-ui-ux`.
- **Flutter UI outside the game:** plain Flutter widgets and navigation.

## References

- Read `references/components-collision-and-builds.md` for the component lifecycle, camera/HUD
  setup, collision and input snippets, save pattern and a Flame test checklist.
