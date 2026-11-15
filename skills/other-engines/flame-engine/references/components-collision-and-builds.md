# Components, collision and builds

Depth for `flame-engine`: lifecycle, camera, collision, input and tests.

## Lifecycle

```text
constructor -> onLoad (async, once) -> onMount -> update(dt)/render ...
                                              -> onRemove
```

- `onLoad` is the async constructor: load images/audio, set size, add hitboxes.
- `onMount` runs when attached and sized; use it for parent-dependent setup.
- `onRemove` releases listeners/timers you created.
- `future` / `loaded` let other code await readiness.

## Scene skeleton

```dart
class MyGame extends FlameGame with HasCollisionDetection, HasKeyboardHandlerComponents {
  @override
  Future<void> onLoad() async {
    final player = Player(position: Vector2(100, 100));
    world.addAll([player, ...enemies]);
    camera.follow(player, maxSpeed: 400);
    camera.setBounds(Rectangle.fromLTRB(0, 0, 3200, 1800));
    camera.viewport.add(ScoreHud());
  }
}
```

- HUD components added to `viewport` stay fixed on screen.
- `world.add` after `onLoad` is fine; children mount on the next tick.

## Sprite and animation

```dart
final image = await Flame.images.load('player.png');
final sprite = Sprite(image, srcPosition: Vector2.zero(), srcSize: Vector2(32, 32));
add(SpriteComponent(sprite: sprite, size: Vector2.all(32), anchor: Anchor.center));
```

- `SpriteAnimationData.sequenced(amount: 4, stepTime: 0.1, textureSize: Vector2(32, 32))`.
- Change animation on state; do not create a new animation every frame.

## Collision

```dart
class Bullet extends PositionComponent with CollisionCallbacks {
  @override
  Future<void> onLoad() async {
    size = Vector2.all(8);
    anchor = Anchor.center;
    add(CircleHitbox());
  }

  @override
  void onCollisionStart(Set<Vector2> points, PositionComponent other) {
    if (other is Enemy) removeFromParent();
    super.onCollisionStart(points, other);
  }
}
```

- `RectangleHitbox`, `CircleHitbox`, `PolygonHitbox`, `ScreenHitbox`.
- Set `collisionType` (`active`, `passive`, `inactive`) to control pairs.
- Debug: `debugMode = true` on the game or component.

## Input

```dart
class Player extends PositionComponent with KeyboardHandler {
  @override
  bool onKeyEvent(KeyEvent event, Set<LogicalKeyboardKey> keysPressed) {
    if (event is KeyDownEvent && keysPressed.contains(LogicalKeyboardKey.space)) {
      jump();
      return true;
    }
    return false;
  }
}
```

- `TapCallbacks` gives local position relative to the component.
- Add `HasKeyboardHandlerComponents` to the game; give the `GameWidget` focus.

## Save pattern

```dart
final dir = await getApplicationDocumentsDirectory();
final file = File('${dir.path}/save.json');
await file.writeAsString(jsonEncode(state.toJson()));
```

- Write `save.tmp`, then `rename` over `save.json`.
- Version the JSON and migrate before constructing components.

## Checklist

1. Gameplay components live in `world`; HUD lives in the viewport.
2. `onLoad` is async and awaited assets are ready before first render.
3. Camera follows the player and clamps to level bounds.
4. Hitboxes match sprites; collision callbacks fire once per pair.
5. Both keyboard and touch input work; focus loss does not stick keys.
6. `dt` is seconds; movement is frame-rate independent.
7. No asset loads or allocations in the hot loop.
8. Audio preloads and pauses with the game.
9. Save/load round-trips and survives a corrupt file.
10. Web and one mobile target build and run.
