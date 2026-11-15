# Other engine skills

Thirty-four Agent Skills for MonoGame 3.8.6, GameMaker LTS 2026.0, Bevy 0.20, pygame-ce 2.5.8,
LÖVE 11.5, Defold 1.14.0, and Roblox. MonoGame coverage starts with the C# game loop, SpriteBatch,
the 3.8.6 Content Builder, input, collision and publishing; GameMaker coverage starts with GML
objects, events, rooms, collisions, drawing and JSON saves.
Bevy adds serde save files and a texture-atlas tilemap on top of the ECS core; LÖVE and pygame coverage includes tile levels
on top of their core loop, and both add saves (LÖVE through `love.filesystem`, pygame through
stdlib JSON) and cameras; Defold coverage includes core game structure, GUI scenes, tile levels, collision
objects and sprite flipbooks; Roblox coverage includes Luau, grid levels,
persistence, UI, networking, characters, physics, Studio workflow, and simulator economy
balancing.

Each subdirectory is one skill. Existing projects keep their pinned engine or
dependency version; see [`VERSION-SUPPORT.md`](../../docs/VERSION-SUPPORT.md).

See [`docs/SKILL-FORMAT.md`](../../docs/SKILL-FORMAT.md) for the authoring standard.
