# Attenuation, mixes and networking (UE 5.8)

Depth for `unreal-audio`: the API surface, how attenuation and concurrency shape a mix, routing
through classes/submixes, and the multiplayer rules.

## API used by the skill

| API | Header / form | Notes |
|-----|---------------|-------|
| `UGameplayStatics::PlaySound2D` | `Kismet/GameplayStatics.h` | Non-spatial, fire-and-forget. |
| `UGameplayStatics::PlaySoundAtLocation` | same | Spatial one-shot; not replicated. |
| `UGameplayStatics::SpawnSoundAtLocation` | same | Returns `UAudioComponent` for control. |
| `UGameplayStatics::SpawnSoundAttached` | same | Component attached to a scene component. |
| `UAudioComponent` | `Components/AudioComponent.h` | `Play`, `Stop`, `SetFloatParameter`, attenuation override. |
| `USoundAttenuation` | `Sound/SoundAttenuation.h` | Falloff, shape, spatialization, occlusion. |
| `USoundConcurrency` | `Sound/SoundConcurrency.h` | Instance limits and resolution. |
| `USoundClass` | `Sound/SoundClass.h` | Volume/pitch group; parent/child hierarchy. |
| `USoundMix` | `Sound/SoundMix.h` | A set of class adjusters. |
| `UGameplayStatics::SetSoundMixClassOverride` | `(WorldContext, Mix, Class, Volume, Pitch, FadeInTime, bApplyToChildren)` | Volume sliders. |
| `UGameplayStatics::PushSoundMixModifier` / `PopSoundMixModifier` | `(WorldContext, Mix)` | Activate/deactivate a mix. |

## Attenuation settings

```text
InnerRadius       full volume within
FalloffDistance   distance to minimum volume
DistanceAlgorithm Linear / Logarithmic / Inverse / Custom curve
AttenuationShape  Sphere / Capsule / Box / Cone
Spatialization    on for world sounds, off for UI/music
Occlusion         needs project support; costs traces
AirAbsorption     high-frequency rolloff
```

- Set both inner radius and falloff; a falloff shorter than the inner radius is clamped/odd.
- Use logarithmic for natural outdoor decay, linear for stylized control, custom curves for
  designed moments.
- For cone shapes (fire alarms, spotlights), set the cone angle and falloff.
- Distance culling: do not use a 10 km falloff for a footstep.

## Concurrency

| Setting | Effect |
|---------|--------|
| Max Concurrent Count | Hard limit for the group. |
| Resolution | Stop oldest / stop quietest / reject new. |
| Limit to Owner | Per-actor budget. |
| Sound Group | Share a budget across different assets. |

Example budgets: footsteps 4, weapon impacts 8, explosions 3, UI 2. Tune against the busiest
combat scene, not a quiet test map.

## Class and submix routing

```text
Master
├── Music      -> MusicSubmix (compressor, reverb send)
├── SFX
│   ├── Weapons
│   └── Ambience
├── Voice      -> VoiceSubmix (ducking sidechain)
└── UI
```

- Every `USoundBase` needs a Sound Class; unassigned assets fall to the default class and cannot
  be mixed.
- Volume sliders override the class, not the asset.
- Duck music under dialogue with a Submix envelope follower or a manually pushed mix; avoid
  scripting per-line volume.
- `bApplyToChildren = true` on a class override makes children follow (SFX slider affects
  Weapons/Ambience).
- Pop a pushed mix when leaving the menu that pushed it, or its overrides leak into gameplay.

## MetaSounds

- Inputs are declared in the MetaSound graph; set them via `UAudioComponent::SetFloatParameter`
  (or the parameter controller interface).
- Parameters are the right way to vary engine RPM, wind intensity, weapon charge.
- Trigger inputs (e.g. "Play Cue") allow sample-accurate one-shots from a running graph.
- MetaSounds still respect attenuation, concurrency, class and submix routing.

## Networking rules

| Approach | Replicates? | Use |
|----------|-------------|-----|
| `PlaySoundAtLocation` on server | no | never for client-audible SFX |
| `NetMulticast, Unreliable` RPC | yes, to relevant clients | cosmetic one-shots |
| `NetMulticast, Reliable` | yes | rare, important cues (objective complete) |
| Replicated state + local component | yes | loops, music, charge sounds |

- Multicast is sent to actors relevant to the sound; far-away clients may not receive it, which
  is fine for cosmetics.
- Do not multicast per tick; send an event and let clients run the loop locally.
- The server should own gameplay decisions (did the shot hit); clients only render the sound.

## Test checklist

1. UI click is 2D: no attenuation, no panning.
2. World one-shot falls off; audible at inner radius, silent past falloff.
3. 20 simultaneous impacts: concurrency caps voices, no clipping.
4. Volume sliders: SFX/music/voice change independently and persist across restart.
5. Pause menu ducks music and restores on close (mix pushed/popped).
6. Multiplayer: client hears server-triggered explosion; server does not spam multicast.
7. Looping engine stops when the vehicle is destroyed.
8. Music continues across level transitions (persistent audio actor).
9. MetaSound parameters update continuously without per-frame Blueprint cost.
10. Occlusion (if enabled): sound muffles behind walls without audible pops.
