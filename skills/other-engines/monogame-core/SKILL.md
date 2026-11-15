---
name: monogame-core
description: >
  Build 2D/3D games in C# with MonoGame 3.8.6: Game lifecycle, fixed timestep, SpriteBatch,
  Content Builder pipeline, input, cameras, collision, audio, save data and desktop publishing.
  Use for a MonoGame/FNA-style framework project.
---

# MonoGame core

MonoGame is a code-first framework: you own the loop, the draw order and the content build.
There is no editor and no scene graph, so architecture is your job. This is an **engine** skill:
pair it with genre and discipline skills.

## When to use

- Use for a C# MonoGame project (DesktopGL/WindowsDX), or when porting XNA/FNA code.
- Use when content is missing at runtime, input repeats, or pixel art is blurry.

**When *not* to use:** Unity/Godot projects → their engine skills; a web game → `phaser-game` /
`pixijs-game`; plain C# without a game loop → no engine skill.

## Versions

- MonoGame **3.8.6.1** (Nov 2026), .NET **10** SDK.
- 3.8.6 replaces the `.mgcb` workflow with a **Content Builder** console project. Legacy
  `.mgcb` projects still build; new projects should use the Content Builder.
- Templates: install `MonoGame.Templates.CSharp`, then create a DesktopGL project and run
  `dotnet new list` to confirm the template short name for your SDK.

## Project layout

```text
MyGame.sln
MyGame.DesktopGL/        # platform project (entry point)
MyGame.Content/          # Content Builder + Assets
  Assets/
  Builder/Builder.cs
  BuildContent.targets
```

- Keep game code in a shared class library once you target more than one platform.
- Import `BuildContent.targets` in each platform project so content builds with the game.
- `Content.RootDirectory = "Content"`; built files land in `Content/` next to the executable.

## Game lifecycle

```csharp
public sealed class Game1 : Game
{
    private readonly GraphicsDeviceManager _graphics;
    private SpriteBatch _spriteBatch = null!;
    private Texture2D _hero = null!;
    private Vector2 _position = new(400, 240);

    public Game1()
    {
        _graphics = new GraphicsDeviceManager(this)
        {
            PreferredBackBufferWidth = 1280,
            PreferredBackBufferHeight = 720
        };
        Content.RootDirectory = "Content";
        IsMouseVisible = true;
        IsFixedTimeStep = true;
        TargetElapsedTime = TimeSpan.FromSeconds(1d / 60d);
    }

    protected override void LoadContent()
    {
        _spriteBatch = new SpriteBatch(GraphicsDevice);
        _hero = Content.Load<Texture2D>("Textures/hero");
    }

    protected override void Update(GameTime gameTime)
    {
        var dt = (float)gameTime.ElapsedGameTime.TotalSeconds;
        // input + simulation
        base.Update(gameTime);
    }

    protected override void Draw(GameTime gameTime)
    {
        GraphicsDevice.Clear(Color.CornflowerBlue);
        _spriteBatch.Begin(samplerState: SamplerState.PointClamp);
        _spriteBatch.Draw(_hero, _position, Color.White);
        _spriteBatch.End();
        base.Draw(gameTime);
    }
}
```

- `Update` runs before `Draw`; with fixed timestep it may run multiple times per frame.
- Do not put gameplay in `Draw`; it is skipped when the window is minimized.
- Unload/dispose textures and audio you create yourself.

## Timing

- Fixed timestep 60 Hz by default; use `gameTime.ElapsedGameTime` for movement.
- `IsFixedTimeStep = false` for variable dt, but then clamp `dt` (e.g. max 0.1 s).
- Accumulate a timer for animations instead of counting frames.
- For determinism, step simulation at a fixed rate and interpolate rendering.

## Input

```csharp
private KeyboardState _prevKeyboard;

var keyboard = Keyboard.GetState();
if (keyboard.IsKeyDown(Keys.Space) && !_prevKeyboard.IsKeyDown(Keys.Space))
    Jump();
_prevKeyboard = keyboard;

var mouse = Mouse.GetState();
var pad = GamePad.GetState(PlayerIndex.One);
if (pad.Buttons.A == ButtonState.Pressed && _prevPad.Buttons.A == ButtonState.Released)
    Confirm();
```

- Edge detection needs the previous state; store it per device.
- `Mouse.GetState().Position` is in window pixels; convert with the camera matrix.
- Handle focus loss: clear held input so the player does not keep moving.

## Rendering

- `SpriteBatch.Begin`/`End` once per layer; changing blend/sampler forces extra batches.
- Pixel art: `SamplerState.PointClamp`, integer positions, and a virtual resolution.
- Draw order: `SpriteSortMode.BackToFront` with `layerDepth` in `[0,1]`, or sort yourself.
- Camera:

```csharp
var view = Matrix.CreateTranslation(-_camera.Position.X, -_camera.Position.Y, 0f)
         * Matrix.CreateScale(_camera.Zoom, _camera.Zoom, 1f)
         * Matrix.CreateTranslation(_viewport.Width / 2f, _viewport.Height / 2f, 0f);
_spriteBatch.Begin(transformMatrix: view, samplerState: SamplerState.PointClamp);
```

- Update `_viewport` on `Window.ClientSizeChanged`; recompute projection for 3D.
- Cull off-screen sprites; atlas sprites to cut texture switches.

## Collision

- AABB: `Rectangle.Intersects` for broadphase, then precise math if needed.
- Circle: compare squared distance to squared radii; avoid `Vector2.Distance` in hot loops.
- Separate axes for tile collision to prevent corner snagging.
- Spatial hash/grid for hundreds of entities; do not test all pairs.

## Content Builder (3.8.6+)

`Builder/Builder.cs` is a console entry point plus rules:

```csharp
using Microsoft.Xna.Framework.Content.Pipeline;
using MonoGame.Framework.Content.Pipeline.Builder;

var defaults = new ContentBuilderParams
{
    Mode = ContentBuilderMode.Builder,
    WorkingDirectory = $"{AppContext.BaseDirectory}../../",
    SourceDirectory = "Assets",
    Platform = TargetPlatform.DesktopGL
};
var builder = new Builder();
if (args is { Length: > 0 }) builder.Run(args); else builder.Run(defaults);
return builder.FailedToBuild > 0 ? -1 : 0;

public sealed class Builder : ContentBuilder
{
    public override IContentCollection GetContentCollection()
    {
        var content = new ContentCollection();
        content.Include<WildcardRule>("Textures/*.png");
        content.Include<WildcardRule>("Sounds/*.wav");
        content.Include<WildcardRule>("Fonts/*.spritefont");
        content.Exclude<WildcardRule>("Fonts/*.ttf"); // source for the .spritefont
        content.IncludeCopy("Data/levels.json");
        return content;
    }
}
```

- Nothing is built unless a rule includes it. Last matching rule wins.
- `*` also matches `/`; brace patterns like `*.{png,jpg}` do **not** work.
- Built paths keep their relative path and get `.xnb`; load without the extension.
- `IncludeCopy` for JSON/text you read yourself; custom importers validate data at build time.
- Fonts: `.spritefont` references a `.ttf`; exclude the `.ttf` or it is built twice.
- Legacy `.mgcb`: `dotnet tool install -g dotnet-mgcb`, then `mgcb /rebuild /platform:DesktopGL`.

## Audio

- `SoundEffect` for short one-shots; `SoundEffectInstance` for looping/pitch/volume control.
- `Song` + `MediaPlayer` for streaming music; `MediaPlayer.IsRepeating` for loops.
- Cap simultaneous one-shots; reuse instances instead of creating per shot.
- Pause audio on focus loss and when the game pauses.

## Save data

- JSON via `System.Text.Json`; write to a temp file then replace atomically.
- Use `Environment.GetFolderPath(SpecialFolder.ApplicationData)` plus your game folder.
- `TitleContainer.OpenStream` for read-only files shipped with the game.
- Version the save; migrate on load; never deserialize into game objects directly.

## Publishing

- `dotnet publish -c Release -r win-x64 --self-contained true` for a desktop build.
- Test on a clean machine: content folder next to the executable, no SDK installed.
- Trim/AOT only if your dependencies support it; verify reflection-based serializers.
- Set the content platform per target; content is not portable across all platforms.

## Pitfalls

- **Content not found** → path includes extension or `Content/` prefix. Load `"Textures/hero"`.
- **Input repeats every frame** → no previous-state edge detection.
- **Game runs too fast on 144 Hz** → movement per frame. Multiply by `dt`.
- **Pixel art blurry** → default linear sampler. Use `PointClamp` and integer camera.
- **GC stutter** → allocations in `Update`/`Draw` (LINQ, `string` concat, `new` lists).
- **SpriteBatch state leaks** → unbalanced `Begin`/`End`; one pair per pass.
- **Content builds twice/pipeline error** → `.ttf` included alongside `.spritefont`.
- **Window resize breaks UI** → viewport/projection not updated on `ClientSizeChanged`.
- **Audio clicks** → creating/disposing effects per shot. Pool instances.
- **Save corruption** → writing in place. Temp file + atomic replace.

## Composition

- **Genres:** `platformer`, `bullet-hell`, `rpg`, `tower-defense`.
- **Disciplines:** `game-feel`, `camera-systems`, `animation-systems`, `save-systems`,
  `performance-optimization`, `game-ui-ux`.
- **Content:** `create-game-assets` for sprites/tilesets; `procedural-audio` for synth SFX.

## References

- Read `references/content-builder-input-and-publishing.md` for the full content rule table,
  input/camera snippets, fixed-timestep patterns and a MonoGame test checklist.
