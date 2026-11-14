---
name: roblox-audio
description: >
  Audio in Roblox: Sound objects, SoundId and preloading, Play/Stop/Pause/Resume, Looped music,
  PlaybackSpeed, 3D roll-off (RollOffMode, RollOffMinDistance/MaxDistance), SoundGroups as volume
  buses, SoundService:PlayLocalSound for client-only cues, and server vs client playback. Use when
  a Roblox experience needs SFX, music, ambience or volume settings.
---

# Roblox audio

Roblox audio is instance-based: a `Sound` carries `SoundId`, volume, loop and 3D roll-off, is
parented to a part or attachment for positional audio, and can be routed through a `SoundGroup`
for shared volume. Use `SoundService:PlayLocalSound` for cues only one client should hear.

## When to use

- Use when a Roblox experience needs SFX, music, ambience, UI clicks or volume sliders.
- Use when a sound is silent, plays for everyone when it should be local, or does not fall off
  with distance.

**When *not* to use:** engine-neutral mixing/adaptive music → `audio-design`; UI layout →
`roblox-ui`; replicating gameplay events → `roblox-networking`; saving volume settings →
`roblox-datastores`.

## Core workflow

1. **Preload** assets (`ContentProvider:PreloadAsync`) before the round starts to avoid first-play
   hitches.
2. **Choose the parent**: `SoundService` for non-positional (music/UI), a `BasePart`/`Attachment`
   for 3D.
3. **Set 3D roll-off**: `RollOffMode`, `RollOffMinDistance`, `RollOffMaxDistance`.
4. **Loop music** with `Looped = true` and manage one track at a time.
5. **Group volumes** under `SoundGroup` instances (Music, SFX, UI) and multiply their `Volume`.
6. **Respect the client**: sounds that only one player should hear use
   `SoundService:PlayLocalSound`.
7. **Persist settings** (music/SFX volume, mute) with `roblox-datastores`.

## Patterns

### 1. Create and play a sound

```lua
local sound = Instance.new("Sound")
sound.SoundId = "rbxassetid://9120386436"
sound.Volume = 0.6
sound.Looped = false
sound.Parent = workspace

if not sound.IsLoaded then
    sound.Loaded:Wait()
end
sound:Play()
```

- `SoundId` must be a valid asset id the experience has permission to use.
- `IsLoaded`/`Loaded` avoids a silent first play while streaming.
- `Play()` restarts from `TimePosition` 0 unless paused; `Resume()` continues after `Pause()`.
- `Stop()` resets position; `Pause()` keeps it.
- `Playing` is a property; prefer methods for intent.

### 2. Positional audio

```lua
local emitter = Instance.new("Part")
emitter.Anchored = true
emitter.CanCollide = false
emitter.Transparency = 1
emitter.Size = Vector3.new(1, 1, 1)
emitter.Position = Vector3.new(0, 5, 0)
emitter.Parent = workspace

local hum = Instance.new("Sound")
hum.SoundId = "rbxassetid://9120386436"
hum.Looped = true
hum.Volume = 0.5
hum.RollOffMode = Enum.RollOffMode.InverseTapered
hum.RollOffMinDistance = 10
hum.RollOffMaxDistance = 120
hum.Parent = emitter
hum:Play()
```

- A `Sound` parented to a `BasePart` emits from that part; parented to an `Attachment`, from the
  attachment.
- `RollOffMinDistance` is full volume; beyond `RollOffMaxDistance` the sound is inaudible.
- `RollOffMode` choices: `Inverse`, `InverseTapered`, `Linear`, `LinearSquare`.
- `EmitterSize` is deprecated; use the roll-off properties.
- Very large max distances waste voices; tune per sound.

### 3. Music with one track at a time

```lua
local Music = {}
Music.current = nil

local function playTrack(id: string, volume: number)
    if Music.current then
        Music.current:Destroy()
    end
    local track = Instance.new("Sound")
    track.SoundId = id
    track.Looped = true
    track.Volume = volume
    track.Parent = SoundService
    track:Play()
    Music.current = track
end

function Music.fadeOut(seconds: number)
    if not Music.current then return end
    local track = Music.current
    task.spawn(function()
        for i = 10, 0, -1 do
            track.Volume = track.Volume * (i / 10)
            task.wait(seconds / 10)
        end
        track:Destroy()
    end)
    Music.current = nil
end
```

- Keep one music `Sound`; creating a new one per track leaks instances if you forget to destroy.
- Fade by stepping `Volume` with `task.wait`, not a tight loop.
- `PlaybackSpeed` changes pitch and speed together; there is no separate pitch control.
- Music lives under `SoundService` so it is non-positional.

### 4. Sound groups as buses

```lua
local function group(name: string, volume: number): SoundGroup
    local g = Instance.new("SoundGroup")
    g.Name = name
    g.Volume = volume
    g.Parent = SoundService
    return g
end

local sfxGroup = group("SFX", 0.8)
local musicGroup = group("Music", 0.5)

-- assign per sound:
sound.SoundGroup = sfxGroup
```

- `SoundGroup.Volume` is a multiplier (0–10) applied to every child sound.
- Effective volume = `Sound.Volume × SoundGroup.Volume`.
- Add `SoundEffect` instances (reverb, EQ, compressor) under the group to process all its sounds.
- Sliders should set the group volume, not every sound.

### 5. Client-only playback

```lua
-- LocalScript: only this client hears it.
local cue = Instance.new("Sound")
cue.SoundId = "rbxassetid://9120386436"
cue.Volume = 0.7
SoundService:PlayLocalSound(cue)
```

- `PlayLocalSound` plays a copy for the calling client only, regardless of parent.
- Use it for UI clicks, local feedback, and per-player music stingers.
- Server `Sound:Play()` is heard by clients per normal replication; do not use it for
  player-specific cues.
- A LocalScript should not create sounds on the server; keep the split explicit.

### 6. Preloading and permissions

```lua
local assets = {
    "rbxassetid://9120386436",
    "rbxassetid://9120386437",
}

ContentProvider:PreloadAsync(assets)
```

- Preload before gameplay; first-play decode can hitch.
- Audio permissions are per-experience; a sound that works in Studio may be muted in a published
  game if the asset is not authorized.
- Test on a published server, not only Studio Play.

## Pitfalls

- **Silent sound** → invalid/unauthorized `SoundId`, or the sound was never `Play()`ed. Check
  `IsLoaded` and output warnings.
- **Everyone hears a local cue** → played on the server. Use `PlayLocalSound` or a LocalScript.
- **No distance falloff** → `RollOffMaxDistance` left at default or sound parented to
  `SoundService`. Parent to a part and set roll-off.
- **Music overlaps** → multiple tracks playing; keep one current track and destroy the old.
- **Volume slider does nothing** → setting `Sound.Volume` per sound instead of the group, or
  `SoundGroup` not assigned.
- **First play hitches** → no preload. Use `ContentProvider:PreloadAsync`.
- **Sound continues after part removal** → destroying the parent should stop it; explicitly
  `:Stop()` and `:Destroy()` for pooled emitters.
- **Pitch and speed coupled** → `PlaybackSpeed` changes both; pre-render variants if you need
  independent pitch.
- **Too many 3D emitters** → every footstep as a part-parented sound. Pool emitters and cap
  concurrent sounds.
- **Settings reset on rejoin** → volume not saved; persist via `roblox-datastores`.

## References

- Read `references/rolloff-groups-and-client-audio.md` for the Sound API table, roll-off modes,
  group routing, server/client rules and an audio test checklist.

## Related skills

- `roblox-ui` — volume sliders and mute buttons.
- `roblox-networking` — remote events that trigger client audio.
- `roblox-datastores` — persisting audio settings.
- `audio-design` — mixing, ducking and adaptive music.
- `unreal-audio` / `unity-audio` — engine mixer equivalents.
