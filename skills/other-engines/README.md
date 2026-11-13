# Other engine skills

Twenty-four Agent Skills for Bevy 0.20, pygame-ce 2.5.8, LÖVE 11.5, Defold 1.14.0, and Roblox.
Bevy adds serde save files and a texture-atlas tilemap on top of the ECS core; LÖVE and pygame coverage includes tile levels
on top of their core loop, and both add saves (LÖVE through `love.filesystem`, pygame through
stdlib JSON); Defold coverage includes core game structure, GUI scenes, tile levels, collision
objects and sprite flipbooks; Roblox coverage includes Luau, grid levels,
persistence, UI, networking, characters, physics, Studio workflow, and simulator economy
balancing.

Each subdirectory is one skill. Existing projects keep their pinned engine or
dependency version; see [`VERSION-SUPPORT.md`](../../docs/VERSION-SUPPORT.md).

See [`docs/SKILL-FORMAT.md`](../../docs/SKILL-FORMAT.md) for the authoring standard.
