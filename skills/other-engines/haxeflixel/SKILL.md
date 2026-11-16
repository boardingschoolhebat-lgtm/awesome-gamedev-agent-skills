---
name: haxeflixel
description: >
  Build 2D games in Haxe with HaxeFlixel 6.2: FlxGame/FlxState lifecycle, sprites and animation,
  input, collision, tilemaps, cameras, tweens, sound, save data and Lime builds for web/desktop/mobile.
  Use for a HaxeFlixel project.
---

# HaxeFlixel

HaxeFlixel is a 2D engine on OpenFL/Lime: states own the screen, sprites own motion and collision,
and `FlxG` is the global access point. It compiles Haxe to web, desktop, mobile and consoles. This
is an **engine** skill: pair it with genre and discipline skills.

## When to use

- Use for a HaxeFlixel project (`.hx`, `Project.xml`), or when porting a Flixel game.
- Use when sprites do not move, collisions never resolve, or a build misses assets.

**When *not* to use:** Godot/Unity/GameMaker → their skills; plain Haxe without Flixel → no engine
skill; a web game with JS → `phaser-game`/`pixijs-game`.

## Versions

- HaxeFlixel **6.2.1** (flixel 6.2.1, Nov 2026), OpenFL/Lime.
- Flixel 6 changed `FlxGame`'s initial state to a **constructor** (`PlayState.new`); the old
  `Class<FlxState>` form is deprecated. Match the version used by the project.
- Install: `haxelib install flixel`, plus `flixel-tools`, `flixel-ui`, `flixel-addons` as needed.
- Create a project with `flixel create` (Flixel Tools) or use an existing `Project.xml`.

## Project layout

```text
Project.xml          # window, assets, libraries
source/
  Main.hx            # entry point, new FlxGame(...)
  PlayState.hx
  Player.hx
assets/
  images/
  sounds/
  data/
```

- `Project.xml` declares assets; `AssetPaths` is generated at build time.
- `source/` is the Haxe class path; package names must match folders.
- `lime build html5`, `lime test windows`, `lime build android` are the usual commands.

## Entry point

```haxe
class Main extends Sprite {
    public function new() {
        super();
        addChild(new FlxGame(320, 180, PlayState.new, 60, 60, true));
    }
}
```

- `FlxGame` sets the design resolution, initial state and update/draw rates.
- Flixel 6 expects a state constructor (`PlayState.new`); see the project's version.
- `FlxG` exposes the camera, input, sound, save and state switching.

## States

```haxe
class PlayState extends FlxState {
    var player:Player;

    override public function create():Void {
        bgColor = 0xff101018;
        player = new Player(32, 32);
        add(player);
        add(new FlxText(8, 8, 200, "HP: 3"));
        super.create();
    }

    override public function update(elapsed:Float):Void {
        super.update(elapsed);
        FlxG.collide(player, walls);
    }
}
```

- `create()` builds the scene; `update(elapsed)` runs per frame (seconds).
- `add()` mounts objects; `remove()` detaches; destroyed objects should be nulled.
- Switch scenes with `FlxG.switchState(...)` using the form your Flixel version expects.
- One state per level/menu keeps memory and code scoped; reset state on restart.

## Sprites and animation

```haxe
var sprite = new FlxSprite(x, y);
sprite.loadGraphic("assets/images/player.png", true, 16, 16);
sprite.animation.add("idle", [0, 1], 6, true);
sprite.animation.play("idle");
```

- `loadGraphic(path, animated, frameWidth, frameHeight)`; `makeGraphic` for placeholders.
- `animation.add(name, frames, fps, loop, flipX, flipY)`; `play(name)`.
- Set `width`/`height`/`offset` for the collision box, independent of the art.
- `FlxSpriteGroup` composes multi-part objects; `FlxText`/`FlxBitmapText` for UI.

## Motion and collision

```haxe
player.velocity.x = 120;
player.acceleration.y = 900;   // gravity, px/s²
FlxG.collide(player, walls);
FlxG.overlap(player, coins, collect);
```

- `velocity` is px/s; `acceleration`, `drag`, `maxVelocity` are px/s² and px/s.
- `FlxG.collide` separates objects; `FlxG.overlap` only reports.
- `FlxObject.isTouching(FlxObject.FLOOR)` for grounded checks.
- Groups (`FlxGroup`, `FlxTypedGroup<T>`) manage many objects and collisions.
- `FlxTilemap` for grid levels; load CSV/array and set collision indices.

## Input

```haxe
if (FlxG.keys.justPressed.SPACE) jump();
var axis = (FlxG.keys.pressed.D ? 1 : 0) - (FlxG.keys.pressed.A ? 1 : 0);
```

- `justPressed` edges, `pressed` held, `justReleased` release.
- Gamepad: `FlxG.gamepads.getFirstActiveGamepad()`; touch: `FlxG.touches`.
- Bind actions in one place; never scatter raw keys through gameplay code.
- Pause input on focus loss; Flixel handles some of this, verify.

## Cameras

```haxe
FlxG.camera.follow(player, LOOKAHEAD, 0.12);
FlxG.camera.setBounds(0, 0, levelWidth, levelHeight, true);
FlxG.cameras.add(minimap, false);
```

- `follow(target, style, lerp)`; styles include `LOCKON`, `PLATFORMER`, `TOPDOWN`.
- `setBounds` clamps the camera to the level.
- Multiple cameras: HUD camera with `bgColor = 0` and `FlxG.cameras.add(cam, false)`.
- Screen shake: `FlxG.camera.shake(intensity, duration)`.

## Tweens, sound, save

```haxe
FlxTween.tween(sprite, {alpha: 0}, 0.3, {onComplete: _ -> sprite.kill()});
FlxG.sound.play(AssetPaths.hit__wav, 0.8);
FlxG.sound.playMusic(AssetPaths.theme__ogg, 0.6, true);

FlxG.save.bind("my_game");
FlxG.save.data.highScore = 1200;
FlxG.save.flush();
```

- `FlxTween` for property animation; `FlxTimer` for delayed calls.
- `AssetPaths` names are generated (`file__png`, `file__wav`); do not hardcode paths.
- `FlxG.save` is a typed key-value store; bind once at startup, flush after writes.
- Version saved data and migrate; never store live objects.

## Camera, UI and resolution

- Design at a fixed resolution (e.g. 320×180) and scale with `FlxG.scaleMode`.
- Pixel art: `FlxG.camera.antialiasing = false`, integer scaling where possible.
- HUD text uses `FlxText` or `flixel-ui`; keep it on a separate camera.
- Test at 16:9 and 4:3; letterbox rather than stretch.

## Build

- `lime build html5`, `lime build windows`, `lime build mac`, `lime build linux`, `lime build android`.
- Assets declared in `Project.xml` are embedded; missing assets fail at build/runtime.
- Test the HTML5 build over HTTP, and mobile on a device for touch and safe areas.
- `lime build` with `-debug` for the debugger overlay; `FlxG.debugger.visible`.

## Pitfalls

- **Nothing updates** → objects added to the wrong state or `super.update` missing.
- **Sprite invisible** → asset not declared or `loadGraphic` path wrong. Use `AssetPaths`.
- **Collision box wrong** → `width`/`height`/`offset` not set after loading a graphic.
- **Movement frame-dependent** → using per-frame speed. Use `elapsed`/velocity.
- **State leaks** → objects/listeners not removed on switch. Reset in `create`/`destroy`.
- **Input repeats** → using `pressed` where `justPressed` is needed.
- **Camera stuck** → bounds smaller than the viewport or follow target removed.
- **Audio missing on HTML5** → browser requires a user gesture; unlock audio.
- **Save lost** → no `flush()` or bound to a different key.
- **Build fails on assets** → file not in `Project.xml` or wrong path case.

## Composition

- **Genres:** `platformer`, `bullet-hell`, `roguelike`, `puzzle`.
- **Disciplines:** `game-feel`, `camera-systems`, `animation-systems`, `save-systems`,
  `performance-optimization`, `game-ui-ux`.
- **Architecture:** `game-architecture` for state boundaries and data-driven content.

## References

- Read `references/states-collision-and-builds.md` for lifecycle, collision, camera, save and
  build snippets plus a HaxeFlixel test checklist.
