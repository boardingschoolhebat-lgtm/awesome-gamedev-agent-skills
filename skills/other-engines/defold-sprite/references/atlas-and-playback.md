# Defold atlases, flipbooks and sprite properties

Reference material for `SKILL.md`. Targets **Defold 1.14.0**.

## Atlas anatomy

An `.atlas` packs images (or tile-source tiles) into one texture. Each entry has:

| Property | Meaning |
|----------|---------|
| Id | Image id, read-only |
| Size | Width and height in pixels, read-only |
| Pivot | Normalized origin: `(0,0)` top-left, `(1,1)` bottom-right, default `(0.5, 0.5)`; values outside 0–1 are allowed |
| Sprite Trim Mode | Off draws a rectangle; trimmed draws a non-rectangular mesh for mostly transparent art. Trim and slice-9 cannot be combined |
| Image | Source image path |

Animation groups add:

| Property | Meaning |
|----------|---------|
| Id | Animation name used by `sprite.play_flipbook` |
| Fps | Playback speed in frames per second |
| Flip horizontal / vertical | Flips the whole animation |
| Playback | `None` (first frame only), `Once Forward`, `Once Ping Pong`, `Loop Forward`, `Loop Ping Pong` |
| Frames | 1-based indices into the geometries table; entries may repeat, reorder or skip |

Because frames are indices, two animations can share the same images without duplicating texture
space. A "drive" animation and a "reverse" animation can point at the same geometry list in
different orders.

## Playback modes

| Mode | Behavior | Completion callback |
|------|----------|---------------------|
| None | First frame held | No |
| Once Forward | Plays first → last once | Yes, at the end |
| Once Ping Pong | First → last → back to the second frame | Yes, when it stops |
| Loop Forward | Repeats first → last | Never |
| Loop Ping Pong | Repeats the ping-pong cycle | Never |

`Once Ping Pong` deliberately stops on the second frame; if the animation must end where it
started, add a duplicate of the first frame at the end.

## Playing from script

```lua
sprite.play_flipbook(url, id, [complete_function], [play_properties])
```

- `complete_function(self, message_id, message, sender)` — `message_id` is
  `hash("animation_done")`, `message.id` is the finished animation, `message.current_tile` the
  last tile, and `sender` the sprite component.
- Without a callback, the same data arrives as an `animation_done` message to the script that
  started the animation.
- `play_properties`: `offset` (normalized start cursor) and `playback_rate` (positive number).

Flipping:

```lua
sprite.set_hflip("#sprite", true)
sprite.set_vflip("#sprite", false)
```

Flips are applied on top of the animation's own flip flags.

## Sprite component properties

| Property | Type | Notes |
|----------|------|-------|
| `image` | hash | Atlas or tile source; assign with `go.set` and a `resource.atlas` / `resource.tile_source` property |
| `material` | hash | Render material; assign a `resource.material` |
| `animation` | hash | Current animation |
| `cursor` | number | Normalized playback position |
| `frame_count` | number | Frames in the current animation |
| `playback_rate` | number | Playback speed multiplier |
| `scale` | vector3 | Non-uniform component scale |
| `size` | vector3 | Pixel size; settable only with manual size mode |
| `slice` | vector4 | Left, top, right, bottom slice values; settable only with manual size mode |

The component also has editor-side `Blend Mode` and `Size Mode` settings; automatic size derives
from the image and blocks runtime size/slice edits.

## Multiple textures

A material with several samplers gives the sprite several image slots. Animation data — fps and
frame names — is taken from the first texture, the "driving animation", so all textures must
share compatible frame layouts.

## Visual QA checklist

1. Every animation plays at its intended speed in the editor preview.
2. Pivot lines the art up with the collision shape at rest and while flipped.
3. Facing flips do not double-apply an atlas flip.
4. Loop animations do not visibly pop at the seam; ping-pong ends on the intended frame.
5. Completion chains (attack → idle) fire once and never get stuck after interrupting.
6. Slice-9 panels scale without stretching their borders and trim mode is off.
7. Blending against the background matches the material (alpha, additive).
8. Desktop bundle check: headless runs skip rendering entirely.
