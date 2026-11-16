# API, tokens and exports

Depth for `pico-8`: cheat sheet, budget, saves, tests.

## API cheat sheet

| Area | Calls |
|------|-------|
| Lifecycle | `_init`, `_update`, `_update60`, `_draw`, `flip` |
| Input | `btn`, `btnp`, `menuitem` |
| Draw | `cls`, `pset`, `pget`, `spr`, `sspr`, `map`, `rect`, `rectfill`, `circ`, `circfill`, `line`, `print` |
| State | `camera`, `clip`, `pal`, `palt`, `color` |
| Map | `mget`, `mset`, `map` |
| Sound | `sfx`, `music` |
| Save | `cartdata`, `dget`, `dset` |
| Misc | `time`, `t`, `rnd`, `flr`, `mid`, `sin`, `cos`, `atan2`, `abs` |

## Token-saving patterns

```lua
-- instead of repeating draw code
function blit(n,x,y) spr(n,x,y) end

-- tables for entities
ents={}
function _init()
  for i=1,8 do add(ents,{x=rnd(128),y=rnd(128)}) end
end

-- short, still readable
for e in all(ents) do
  e.x=(e.x+1)%128
end
```

- Localize hot globals once: `local rnd,flr= rnd,flr`.
- Use `#t`, `all(t)`, `add`, `del`, `count`.
- Merge flags into bitfields: `f = f|1`, `f&1`.
- Avoid string formatting per frame; precompute labels.

## Cart data layout

| Index | Meaning |
|-------|---------|
| 0 | high score |
| 1 | unlocked level |
| 2 | flags bitfield |
| 3–63 | reserved |

- Store booleans as 0/1; bitfields for many flags.
- Migrate by checking a version index first.

## Export checklist

1. Title screen with controls.
2. Pause menu with mute/reset.
3. Token count under 8192; no debug prints.
4. Cart data initialized once; high score persists.
5. Export HTML and PNG; test both.
6. Test with a real gamepad/keyboard layout.
7. Include a cart label and description for sharing.

## Test checklist

1. `_init` runs once; restart resets state.
2. Movement is frame-rate appropriate (30 or 60).
3. `btnp` actions fire once per press.
4. Sprites and map tiles align; no transparent holes.
5. Map collision matches visible solids.
6. Audio channels do not cut each other unintentionally.
7. Cart data persists across runs; reset works.
8. Token count has headroom for the last feature.
9. Exported build runs in a clean environment.
10. Pause menu works and does not advance the game.
