---
name: pico-8
description: >
  Build games for PICO-8 0.2.7: 128x128/16-color constraints, 8192-token Lua, _init/_update/_draw,
  sprites/map, btn/btnp, sfx/music, cart data, token golf and exports. Use for a PICO-8 cart or a
  tiny fantasy-console game.
---

# PICO-8

PICO-8 is a fantasy console with hard limits that are the design: 128×128, 16 colors, 8192
tokens, 32 KB carts, four audio channels. You write Lua, draw with a small API, and ship a PNG
cartridge. This is an **engine** skill: pair it with genre skills scaled to its constraints.

## When to use

- Use for a `.p8`/`.p8.png` cart, a game jam entry, or a deliberately tiny game.
- Use when a cart is over token budget, runs at 30 fps unexpectedly, or input repeats.

**When *not* to use:** a full-size 2D game → `love2d-core`/`pygame-core`/`phaser-game`;
pixel-art asset production only → `create-game-assets`.

## Versions and limits

- PICO-8 **0.2.7** (Aug 2025), Lua 5.2 dialect.
- Display 128×128, fixed 16-color palette; 8×8 sprites (128 bank + 128 shared).
- Code: **8192 tokens** (comments/whitespace free; brackets and strings count as one).
- Cart: 32 KB; sound: 4 channels, 64 SFX; map: 128×32 tiles (+128×32 shared).
- CPU budget: 4M VM instructions/sec. The token limit is a design tool, not an obstacle.

## Cartridge structure

```lua
function _init()
  x=64 y=64
end

function _update()
  if btn(0) then x-=1 end
  if btn(1) then x+=1 end
  if btn(2) then y-=1 end
  if btn(3) then y+=1 end
end

function _draw()
  cls(0)
  spr(1,x,y)
end
```

- `_init` once; `_update` at 30 fps; `_draw` every frame.
- Define `_update60` instead of `_update` for 60 fps; do not define both.
- Without the callbacks, call `flip()` yourself.
- `? "text"` is shorthand for `print("text")`.

## Input

```lua
if btnp(4) then jump() end     -- O/Z, edge
if btn(5) then shoot() end     -- X, held
```

- Buttons: `0` left, `1` right, `2` up, `3` down, `4` O/Z, `5` X.
- `btn(i)` held; `btnp(i)` pressed edge (auto-repeats after a delay; pass repeat args if needed).
- Player 2 uses `btn(i, 1)`; menu/pause via `menuitem`.
- Add touch/keyboard fallbacks only if the target supports them; the cart is gamepad-first.

## Graphics

```lua
cls(1)
spr(16, x, y)                 -- 8x8
spr(16, x, y, 2, 2)           -- 16x16 from 2x2 sprites
sspr(0,0,16,16, x,y,32,32)    -- scaled
rectfill(0,0,127,7,0)
print("score:"..score, 2, 2, 7)
```

- `pset`/`pget` for pixels; `circ`/`circfill`, `rect`/`rectfill`, `line`, `oval`.
- `camera(x,y)` offsets the world; `clip()` limits drawing.
- `pal(c0,c1)` swaps palette colors; `palt(c,t)` toggles transparency.
- `map(cel_x,cel_y,sx,sy,cel_w,cel_h)` draws tilemaps; `mget`/`mset` read/write cells.
- Screen coordinates are 0–127; keep sprites on integer pixels.

## Sprites and map

- Draw sprites in the sprite editor; `spr(n,x,y,[w,h,flip_x,flip_y])`.
- Flags `fget(n,f)`/`fset(n,f,v)` store per-sprite metadata (solid, hazard, etc.).
- The map shares sprites above 127; plan the atlas before adding art.
- Use `map` for static levels and a collision lookup via flags or `mget`.

## Sound

```lua
sfx(3)              -- play on the next free channel
sfx(3, 0)           -- force channel 0
music(0)            -- start pattern 0
music(-1)           -- stop
```

- Four channels total; reserve one for music and one for UI if needed.
- `sfx(n, channel, offset)`; `music(n, fade_len, channel_mask)`.
- Chip blerps are short; layer noise + tone for impact.
- Stop/duck music on pause; keep a mute option in the pause menu.

## Cart data (saves)

```lua
cartdata("my_game")   -- call once, ideally in _init

function _init()
  high = dget(0)
end

function save_score()
  dset(0, high)
end
```

- 64 numbers (256 bytes) per cart id; `dset(idx,val)`, `dget(idx)`.
- No strings/objects; encode flags as numbers or bitfields.
- Call `cartdata` once; changing the id resets access to old data.
- There is no file system in a cart; cart data is the save.

## Token budget

- Use short locals, tables and loops; avoid duplicated blocks.
- `?` for print, `+=`/`-=` operators, `for i=0,n do`.
- Precompute constants in `_init`; avoid long string concatenation each frame.
- Reuse sprite indices and map data instead of code.
- Check the token count in the editor; cut features, not readability, when close to 8192.

## Performance

- Avoid allocating tables/strings in `_update`; reuse tables.
- `cls()` once per frame; batch primitives; avoid per-pixel loops over 128×128.
- `map()` is cheaper than drawing tiles individually.
- Profile with `stat(0)` (CPU) and reduce draw calls first.
- 30 fps is often the right target for the scope; use `_update60` only if needed.

## Pause menu and reset

```lua
menuitem(1, "reset score", function() score=0 end)
```

- `menuitem(index, label, callback)` adds entries to the pause menu.
- `reset()` restarts the cart; confirm destructive actions.
- Keep pause logic out of `_update` when the menu is open.

## Export and share

- `save @clip` / `load @clip` move carts via clipboard.
- `export game.html` for a web build; `export game.p8.png` for a cartridge image.
- `folder` opens the carts directory; `ls` lists carts.
- Test the exported HTML in a browser and the PNG cart in a clean PICO-8.
- Label and title screen matter: 128×128 is the storefront.

## Pitfalls

- **30 fps surprise** → `_update` is 30; define `_update60` for 60.
- **Input repeats** → using `btn` for a single action. Use `btnp`.
- **Over token limit** → duplicated code and long names. Refactor and reuse.
- **Invisible sprite** → wrong sheet index or transparent color. Check `palt`.
- **Map collision misses** → sprite flags not set or wrong tile index.
- **Music cuts SFX** → all four channels busy. Reserve channels.
- **Save not persisting** → `cartdata` not called or different id.
- **Slow draw** → per-pixel loops; use `map`/`spr` and fewer primitives.
- **Cart won't load elsewhere** → exported PNG vs HTML confusion; test both.
- **Scope creep** → 8192 tokens is the budget. Cut to the core loop.

## Composition

- **Genres:** `platformer`, `bullet-hell`, `puzzle`, `roguelike`.
- **Disciplines:** `game-feel`, `level-design`, `audio-design`, `puzzle-design`.
- **Assets:** `create-game-assets` for a compact palette-first sprite set.

## References

- Read `references/api-tokens-and-exports.md` for an API cheat sheet, token-saving patterns,
  cart-data recipes, export steps and a PICO-8 checklist.
