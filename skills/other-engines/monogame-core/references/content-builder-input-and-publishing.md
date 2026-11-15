# Content Builder, input and publishing

Depth for `monogame-core`: content rules, loop patterns, input and tests.

## Content rule table

| Asset | Rule | Runtime type |
|-------|------|--------------|
| `Textures/*.png` | `Include<WildcardRule>` | `Texture2D` |
| `Sounds/*.wav` | `Include<WildcardRule>` | `SoundEffect` |
| `Music/*.ogg` | `Include<WildcardRule>` | `Song` |
| `Fonts/*.spritefont` | `Include<WildcardRule>` | `SpriteFont` |
| `Data/*.json` | `IncludeCopy` | read yourself |
| `Effects/*.fx` | `Include<WildcardRule>` | `Effect` |

- `Include` picks importer/processor by extension; pass instances to override settings.
- `content.Include("Textures/hero.png", new TextureImporter(), new TextureProcessor
  { PremultiplyAlpha = false, GenerateMipmaps = false });`
- `SetContentRoot("Content/Graphics")` changes where later rules write; keep `Content` in it.
- `--compress` and `GraphicsProfile` (`Reach`/`HiDef`) come from `ContentBuilderParams`.

## Fixed timestep loop

```csharp
protected override void Update(GameTime gameTime)
{
    double dt = gameTime.ElapsedGameTime.TotalSeconds;
    _accumulator += dt;
    while (_accumulator >= FixedDt)
    {
        Step(FixedDt);
        _accumulator -= FixedDt;
    }
    base.Update(gameTime);
}
```

- Render interpolation: `alpha = _accumulator / FixedDt`.
- Clamp catch-up steps per frame (e.g. max 5) to avoid a spiral of death.

## Camera and screen-to-world

```csharp
Matrix inverse = Matrix.Invert(view);
Vector2 world = Vector2.Transform(mouse.Position.ToVector2(), inverse);
```

- Zoom about the cursor: adjust camera position by the delta between pre/post zoom world points.
- Clamp the camera to level bounds after lerping, not before.

## Input edge detection

```csharp
bool Pressed(Keys key) =>
    _keyboard.IsKeyDown(key) && !_prevKeyboard.IsKeyDown(key);
```

- Repeat for mouse buttons and gamepad buttons.
- On `IsActive == false`, copy current state into previous and skip gameplay input.

## Collision patterns

```csharp
// AABB
if (a.Bounds.Intersects(b.Bounds)) { /* narrow phase */ }

// Circle
float r = a.Radius + b.Radius;
if (Vector2.DistanceSquared(a.Position, b.Position) <= r * r) { }
```

- Move X, resolve, then move Y to avoid corner sticking.
- Spatial hash cell size ≈ 2× the largest entity.

## Save pattern

```csharp
string dir = Path.Combine(
    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MyGame");
Directory.CreateDirectory(dir);
string tmp = Path.Combine(dir, "save.tmp");
File.WriteAllText(tmp, JsonSerializer.Serialize(state));
File.Move(tmp, Path.Combine(dir, "save.json"), overwrite: true);
```

## Checklist

1. `dotnet build` runs the Content Builder and produces `.xnb` files.
2. Every `Content.Load` path exists without extension; no runtime content exceptions.
3. Movement is dt-based and identical at 60/144 Hz.
4. Edge-triggered actions fire once per press.
5. Pixel art is sharp at integer zoom and non-integer window sizes.
6. Camera clamps to bounds and converts mouse coordinates correctly.
7. Pause stops simulation and audio; focus loss clears input.
8. Save/load round-trips and survives a corrupt file.
9. No per-frame allocations in the hot path (measure with the GC counter).
10. Release publish runs on a clean machine with the `Content` folder present.
