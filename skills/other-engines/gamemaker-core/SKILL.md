---
name: gamemaker-core
description: >
  Build 2D games in GameMaker (LTS 2026.0) with GML: objects and event order, rooms and layers,
  structs and constructors, collisions, drawing, input, audio and JSON saves. Use for GameMaker
  projects (.yyp/.yy/.gml), GML code, or object/room behaviour bugs.
---

# GameMaker core

GameMaker is objects and events inside rooms, scripted in GML. The engine gives you a fast 2D
pipeline; the common bugs come from event order, draw ownership, and collision checks done at the
wrong time. This is the engine skill; pair it with genre and discipline skills for design.

## When to use

- Use when the project has a `.yyp`, `.yy` assets, or `.gml` scripts, or the user says GameMaker/GML.
- Use when creating objects, rooms, collisions, drawing, input, audio, or saves in GameMaker.

**When *not* to use:** Godot/Unity/Unreal projects → their engine skills; generic 2D design →
`platformer`/`game-feel`; shader authoring → GLSL/HLSL guidance.

## Project shape

```text
project.yyp
objects/obj_player/      Create/Step/Draw events + obj_player.yy
rooms/rm_level1/         instances + layers
sprites/spr_player/      frames, origin, collision mask
scripts/scr_helpers/     functions, constructors, macros
sounds/, fonts/, tilesets/
```

- Object = template, instance = runtime copy. `id` is the instance; the object asset is a constant.
- Rooms have layers (`Instances`, `Background`, `Tiles`); instances live on a layer.
- Use **rooms** for levels, not one giant room with teleports, unless streaming is the design.

## Events and order

| Event | Runs | Use |
|-------|------|-----|
| Create | once, on instance creation | initialize variables |
| Step | every frame, after Begin/Before | gameplay logic |
| Draw | every frame | drawing (must call `draw_self()` for the sprite) |
| Draw GUI | screen space | HUD, menus |
| Alarm | after N steps | timers |
| Collision | when masks overlap | reactions |
| Room Start/End | room transitions | setup/cleanup |
| Clean Up | instance destroyed/room end | free data structures |

- All instances' Step events run before all Draw events in the same frame.
- Do not draw in Step; do not run gameplay in Draw.
- Default room speed is 60 steps/s; keep gameplay in steps, not raw milliseconds.

## GML essentials

```gml
// Create
hp = 100;
spd = 3;
target = noone;

// Step
var _h = keyboard_check(vk_right) - keyboard_check(vk_left);
var _v = keyboard_check(vk_down) - keyboard_check(vk_up);
if (_h != 0 || _v != 0) {
    var _len = point_distance(0, 0, _h, _v);
    x += (_h / _len) * spd;
    y += (_v / _len) * spd;
}
```

- `var` is local to the event; bare names are instance variables.
- `keyboard_check` is held, `keyboard_check_pressed` is this step.
- Normalize diagonals (as above) or diagonal movement is faster.

## Collisions

```gml
// Move X then Y, checking before each axis (classic platformer).
var _dx = _h * spd;
if (!place_meeting(x + _dx, y, obj_wall)) x += _dx;

var _dy = _v * spd;
if (!place_meeting(x, y + _dy, obj_wall)) y += _dy;
```

- `place_meeting(x, y, obj)` tests a hypothetical position without moving.
- `instance_place(x, y, obj)` returns the instance or `noone`.
- `collision_rectangle`/`collision_circle` for melee and triggers.
- Prefer manual checks for movement; use Collision events for damage/pickup reactions.
- Move one axis at a time so a blocked X does not block Y (wall sliding).

## Instances, structs, constructors

```gml
// Spawn with initial variables applied before the Create event.
instance_create_layer(x, y, "Instances", obj_bullet, {
    direction: image_angle,
    speed: 8,
    owner: id
});
```

```gml
// Constructor: plain data, no events (use objects when you need Step/Draw).
function Enemy(_x, _y, _hp) constructor {
    x = _x;
    y = _y;
    hp = _hp;
    take_damage = function(_n) { hp -= _n; };
}

var _e = new Enemy(64, 64, 30);
_e.take_damage(10);
```

- `instance_create_depth` when layers are inconvenient; depth and layer are linked.
- Structs are data only; they do not run events.
- Destroy with `instance_destroy()`; check `instance_exists(obj)` before using a stored id.

## Drawing

```gml
// Draw event
draw_self();                       // draws sprite_index at x/y with image_angle etc.
draw_healthbar(20, 20, 120, 32, hp, c_black, c_red, c_lime, 0, true, true);

// Draw GUI (HUD, unaffected by camera)
draw_set_color(c_white);
draw_text(16, 16, "Score: " + string(score));
```

- If you write a Draw event, the sprite is not drawn automatically — call `draw_self()`.
- `draw_sprite_ext(sprite, subimg, x, y, xscale, yscale, rot, color, alpha)` for tint/alpha.
- GUI coordinates are screen pixels; use `display_get_gui_width()`/`height()` for layout.

## Rooms and transitions

```gml
room_goto(rm_level2);          // deferred until the end of the step
room_restart();
```

- Persist data across rooms in a global struct or a persistent object.
- `room_goto` is not instant; code after it still runs this step.
- Use Room Start for per-room setup; Clean Up for freeing buffers/maps.

## Audio and saves

```gml
audio_play_sound(snd_hit, 1, false);

// Save: file functions write inside the game's sandbox save area.
var _data = { hp: hp, room: room, x: x, y: y };
var _f = file_text_open_write("save.json");
file_text_write_string(_f, json_stringify(_data));
file_text_close(_f);
```

- Do not build the save path yourself; GameMaker redirects relative paths to the save area.
- `json_parse` returns a struct/array; validate fields before use.
- Version the save (`{v: 2, ...}`) and migrate.

## Pitfalls

- **Sprite invisible** → a Draw event exists without `draw_self()`.
- **Gameplay in Draw** → logic runs at render rate and after all Steps. Keep it in Step.
- **Diagonal speed boost** → no normalization.
- **Stuck on walls** → moving both axes with one check. Check X and Y separately.
- **Uses destroyed instance** → stale id after `instance_destroy()`. Guard with `instance_exists`.
- **Alarm never fires** → never set (`alarm[0] = 30;`) or set to `-1`.
- **Draw GUI uses room coordinates** → HUD drifts with the camera. Draw GUI is screen space.
- **Layer name typo** → `instance_create_layer` fails silently-ish. Use layer handles/constants.
- **Collision mask wrong** → sprite origin/mask edited after placement. Set the mask in the sprite editor.
- **Save loses data on update** → no version/migration. Add `v` and defaults.

## Composition

- **Genres:** `platformer`, `tower-defense`, `roguelike`, `stealth-game`, `horror-game`.
- **Feel/UI/audio:** `game-feel`, `game-ui-ux`, `audio-design`.
- **Saves:** `save-systems` for schema/migration beyond the basic JSON save.
- **Assets:** `create-game-assets` for sprite/tileset production.

## References

- Read `references/events-instances-and-gml.md` for the full event order, collision matrix,
  struct/constructor patterns, save format and a GameMaker test checklist.
