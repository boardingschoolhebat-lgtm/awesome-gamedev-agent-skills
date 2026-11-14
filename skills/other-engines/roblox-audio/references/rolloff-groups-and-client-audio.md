# Roll-off, groups and client audio (Roblox)

Depth for `roblox-audio`: Sound properties, 3D attenuation, SoundGroup routing, server vs client
playback and test checks.

## Sound API

| Member | Type | Notes |
|--------|------|-------|
| `SoundId` | ContentId | `rbxassetid://...`; permissions are per experience. |
| `Volume` | number | 0–10, multiplicative. |
| `Looped` | boolean | Repeat forever. |
| `PlaybackSpeed` | number | Pitch and speed together. |
| `Playing` | boolean | Read/write playback state. |
| `IsLoaded` / `IsPlaying` / `IsPaused` | boolean | Read-only status. |
| `Loaded` | event | Fires when the asset is ready. |
| `TimePosition` / `TimeLength` | number | Seconds. |
| `Play()` / `Pause()` / `Resume()` / `Stop()` | method | `Stop` resets position; `Pause` keeps it. |
| `SoundGroup` | SoundGroup | Volume/effect bus. |
| `RollOffMode` | Enum | `Inverse`, `InverseTapered`, `Linear`, `LinearSquare`. |
| `RollOffMinDistance` | number | Full-volume radius (studs). |
| `RollOffMaxDistance` | number | Inaudible beyond (studs). |
| `PlayOnRemove` | boolean | Play when the instance is removed. |

Deprecated: `Pitch`, `MinDistance`, `MaxDistance`, `EmitterSize`, lowercase `play`/`stop`/`pause`,
`isPlaying`.

## 3D attenuation

```text
distance <= RollOffMinDistance          full volume
RollOffMinDistance..RollOffMaxDistance  attenuated by RollOffMode
distance >= RollOffMaxDistance          inaudible
```

| Mode | Curve |
|------|-------|
| `Inverse` | 1/d, natural but long tail |
| `InverseTapered` | 1/d with a taper to zero at max |
| `Linear` | straight line to zero |
| `LinearSquare` | squared falloff, quicker drop |

- Parent to a `BasePart` or `Attachment` for positional audio; `SoundService` is non-positional.
- `RollOffMaxDistance` too large keeps voices alive; tune per sound.
- `SoundService.ListenerType`/listener is the camera by default; `SetListener` can override for
  custom views.

## SoundGroup routing

```lua
local sfx = Instance.new("SoundGroup")
sfx.Name = "SFX"
sfx.Volume = 0.8
sfx.Parent = SoundService

sound.SoundGroup = sfx
```

- Effective volume = `Sound.Volume × SoundGroup.Volume`.
- Group volume range 0–10.
- `SoundEffect` children of the group process all sounds in it (reverb, EQ, compressor).
- Sliders set group volume once; per-sound volume stays as authored.
- Create groups at startup; do not create a group per sound.

## Server vs client

| Call | Who hears it |
|------|--------------|
| `sound:Play()` on the server | clients per normal replication |
| `sound:Play()` in a LocalScript | that client |
| `SoundService:PlayLocalSound(sound)` | calling client only |
| `PlayOnRemove` on a server sound | per replication |

- Player-specific cues (UI, local stingers) belong on the client.
- Gameplay events that everyone should hear can be played on the server; for precise timing,
  replicate the event and play locally.
- Do not trust a client to play a sound that implies gameplay state (e.g. a hit confirm); the
  server owns the event.

## Preloading

```lua
ContentProvider:PreloadAsync({ "rbxassetid://1", "rbxassetid://2" })
```

- Preload music and common SFX before the round.
- `PreloadAsync` yields; call it during loading screens.
- Audio permissions: test on a published place; unauthorized assets are silent or warn.

## Performance

- Pool emitters for frequent SFX instead of creating parts per shot.
- Cap concurrent 3D sounds; destroy finished non-looped sounds.
- Avoid `while true do ... wait()` volume loops; use `TweenService` or a stepped fade.
- Streaming: long tracks can stream; short SFX should be preloaded.

## Test checklist

1. UI click plays locally; other players do not hear it.
2. World SFX attenuate with distance and are silent past max.
3. Music loops, switches cleanly, and only one track plays.
4. Volume sliders change the group; mute works; settings persist.
5. Published server: all assets authorized and audible.
6. Preload removes first-play hitch.
7. Destroying an emitter stops its sound.
8. No more than a handful of concurrent 3D emitters in combat.
9. Mobile: audio does not stutter or leak.
10. Accessibility: captions/visual cues exist for important sounds.
