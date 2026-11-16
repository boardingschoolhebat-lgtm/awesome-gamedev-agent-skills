# States, collision and builds

Depth for `haxeflixel`: lifecycle, patterns, tests.

## Lifecycle

```text
new FlxGame(w, h, State.new, updateFps, drawFps, skipSplash)
State.create -> State.update(elapsed) -> State.draw
switchState -> destroy old -> create new
```

- `create()` runs once; `update` per tick; `destroy()` releases listeners/timers.
- Reset per-run fields in `create`, not in the constructor, so a restart is clean.

## Collision patterns

```haxe
FlxG.collide(player, walls);
FlxG.overlap(player, enemies, (p, e) -> hurt(e));

// one-way platform
if (player.velocity.y >= 0 && player.isTouching(FLOOR)) { ... }
```

- Separate solids (`collide`) from triggers (`overlap`).
- `FlxTypedGroup<Bullet>` for pooled projectiles; `kill()`/`revive()` instead of allocating.
- `FlxTilemap.loadMapFromCSV(csv, tileset, tileSize, autoTile)`.

## Camera and HUD

```haxe
FlxG.camera.follow(player, LOCKON, 0.1);
FlxG.camera.setBounds(0, 0, 3200, 1800, true);

var hud = new FlxCamera();
hud.bgColor = 0;
FlxG.cameras.add(hud, false);
hud.add(scoreText);
```

- HUD cameras render after the world; set their scroll to 0.
- Shake only the world camera, never the HUD.

## Save schema

```haxe
FlxG.save.bind("my_game");
FlxG.save.data.version = 2;
FlxG.save.data.unlocked = ["forest", "cave"];
FlxG.save.flush();
```

- Migrate on load: check `version`, fill defaults, then save.
- Keep save keys stable; rename with a migration, not silently.

## Test checklist

1. State switch creates a clean scene and releases listeners.
2. Sprite collision boxes match the art; offsets are correct.
3. Collisions separate solids and only report triggers.
4. Camera follows and clamps; HUD stays fixed.
5. Input uses edges where needed; focus loss pauses.
6. Tweens/timers are cancelled on state exit.
7. Audio unlocks after a gesture on HTML5.
8. Save/load round-trips and migrates an old version.
9. HTML5 and one native target build and run.
10. Debug overlay toggles and shows no per-frame errors.
