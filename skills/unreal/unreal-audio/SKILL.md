---
name: unreal-audio
description: >
  Audio in Unreal Engine 5.8: PlaySound2D and PlaySoundAtLocation, UAudioComponent for looping and
  parameter control, USoundAttenuation falloff, USoundConcurrency limits, Sound Classes and
  Submixes, SetSoundMixClassOverride for volume sliders, MetaSounds parameters, and why
  server-only playback is silent on clients. Use when adding SFX, ambience, music or audio
  settings to an Unreal project.
---

# Unreal audio

Unreal audio is asset-driven: `USoundBase` assets (sound waves, cues, MetaSounds) played through
`UGameplayStatics` or a `UAudioComponent`, routed through Sound Classes and Submixes, shaped by
`USoundAttenuation`, and limited by `USoundConcurrency`. Targets **Unreal Engine 5.8**.

## When to use

- Use when adding SFX, ambience, music, audio settings or spatialized sound to Unreal.
- Use when a sound plays in the editor but not in multiplayer, is too loud/quiet, cuts out, or
  keeps playing after its actor dies.

**When *not* to use:** engine-neutral mixing/adaptive music design → `audio-design`; Unity audio →
`unity-audio`; Unreal replication rules → `unreal-replication`; packaging audio assets →
`unreal-packaging`.

## Core workflow

1. **Classify the sound**: UI/2D (`PlaySound2D`), world one-shot (`PlaySoundAtLocation`), attached
   loop (`UAudioComponent`), or music (component + Submix).
2. **Set attenuation** on world sounds: inner radius, falloff distance, attenuation shape,
   spatialization. Without it, 3D sounds do not fall off.
3. **Limit concurrency** per sound/group so 50 enemies do not stack 50 hit sounds.
4. **Route through Sound Classes** (SFX, Music, Voice, UI) and a Submix; volume sliders override
   the class with `SetSoundMixClassOverride`.
5. **Trigger on the right machine**: `PlaySoundAtLocation` is fire-and-forget and *not*
   replicated. Play it on clients via a multicast/Client RPC, or use a replicated component.
6. **Clean up**: stop attached loops when the actor is destroyed; do not leak audio components.
7. **Test with real mixes**: muted music, voice-only, 5.1 downmix, and a busy combat scene.

## Patterns

### 1. 2D vs world one-shots

```cpp
#include "Kismet/GameplayStatics.h"

// UI / non-spatial: ignores location and attenuation.
UGameplayStatics::PlaySound2D(this, UiClickSound);

// World one-shot with attenuation and concurrency.
UGameplayStatics::PlaySoundAtLocation(
    this,
    ExplosionSound,
    GetActorLocation(),
    FRotator::ZeroRotator,
    1.0f,          // volume multiplier
    1.0f,          // pitch multiplier
    0.0f,          // start time
    ExplosionAttenuation,
    ExplosionConcurrency,
    this);         // owning actor
```

`PlaySoundAtLocation` creates a fire-and-forget sound that does not follow any actor and does not
replicate. Use `SpawnSoundAtLocation` when you need the returned `UAudioComponent` to stop or
modify it.

### 2. Attached looping sound

```cpp
// In the actor's constructor or BeginPlay:
LoopAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("LoopAudio"));
LoopAudio->SetupAttachment(RootComponent);
LoopAudio->bAutoActivate = false;
LoopAudio->AttenuationSettings = EngineLoopAttenuation;

// Start/stop:
LoopAudio->Play();
LoopAudio->Stop();
```

- An attached component follows the actor and is the right tool for engines, ambience and
  loops.
- `bAutoActivate = false` prevents it starting before the actor is ready.
- `Stop()` in `EndPlay`/`Destroyed` for anything that can outlive its owner.
- For MetaSounds parameters: `LoopAudio->SetFloatParameter(TEXT("Speed"), Speed);` (via
  `ISoundParameterControllerInterface`).

### 3. Attenuation

`USoundAttenuation` fields that matter:

| Field | Effect |
|-------|--------|
| Attenuation (Inner Radius) | Full volume inside this radius. |
| Falloff Distance | Distance at which volume reaches its minimum. |
| Attenuation Function | Linear, logarithmic, inverse, custom curve. |
| Attenuation Shape | Sphere, capsule, box, cone. |
| Spatialization | Whether the sound pans with position. |
| Occlusion | Whether walls muffle it (if enabled in project settings). |
| Air Absorption | High-frequency loss over distance. |

Rules of thumb:

- Inner radius ≈ the distance where the player should hear it at full volume.
- Falloff ≈ 2–4× the inner radius for natural decay; test in the actual level scale.
- Very large falloff distances waste voices; use concurrency and distance culling.
- UI and music use no attenuation; do not attach a 3D attenuation to a 2D cue.

### 4. Concurrency

`USoundConcurrency` limits how many instances of a sound (or group) play at once:

- Max Concurrent Count, with a resolution: stop oldest, stop quietest, or reject new.
- Limit by Sound Group so different weapons share a budget.
- Set `bLimitToOwner` for per-actor limits (one engine loop per vehicle).
- Without concurrency, a spawner can stack dozens of identical one-shots and clip the mix.

### 5. Sound Classes, Submixes and volume settings

```text
Master
├── SFX
│   ├── Weapons
│   └── Ambience
├── Music
├── Voice
└── UI
```

- Assign each `USoundBase` a Sound Class; children inherit volume/pitch.
- Route classes to Submixes for DSP (reverb, EQ, compression).
- Volume slider:

```cpp
UGameplayStatics::SetSoundMixClassOverride(
    this,
    MasterMix,
    SFXClass,
    0.6f,     // volume
    1.0f,     // pitch
    0.2f,     // fade-in seconds
    true);    // apply to children
UGameplayStatics::PushSoundMixModifier(this, MasterMix);
```

- Push the mix once when the override is set; pop it when the menu that owns it closes, or the
  override persists.
- Save the slider value and reapply it on load; a sound class override is not persisted.
- Use `SetSoundMixClassOverride` with a fade for pause menus and ducking, not per-frame sets.

### 6. MetaSounds

- A MetaSound Source is a DSP graph asset; play it like any `USoundBase`.
- Expose input parameters (e.g. `Speed`, `Intensity`) and set them on the audio component:
  `AudioComponent->SetFloatParameter(TEXT("Speed"), Value)`.
- Prefer parameters over swapping assets for continuous variation (engine pitch, wind, weapon
  charge).
- MetaSounds are sample-accurate but still need attenuation/concurrency when spatialized.
- Do not set parameters every frame from Blueprint if a timer or threshold update is enough.

### 7. Multiplayer

`PlaySoundAtLocation` on the server does not reach clients. Options:

```cpp
// Server decides, clients play:
if (HasAuthority())
{
    MulticastPlayExplosion(Location);
}

UFUNCTION(NetMulticast, Unreliable)
void MulticastPlayExplosion(FVector Location);

void AMyActor::MulticastPlayExplosion_Implementation(FVector Location)
{
    UGameplayStatics::PlaySoundAtLocation(this, ExplosionSound, Location);
}
```

- Use `Unreliable` multicast for cosmetic sounds; a dropped sound is better than a hitch.
- Do not multicast looping/attached sounds every tick; replicate the state and start/stop locally.
- Audio does not need `DOREPLIFETIME` unless the sound choice is gameplay state; replicate the
  event, play locally.

## Pitfalls

- **Sound is silent in multiplayer** → played on the server only. Play on clients via multicast.
- **3D sound has no falloff** → no `USoundAttenuation` assigned, or spatialization disabled.
- **Audio clips and distorts in combat** → no concurrency limits; identical one-shots stack.
- **Volume slider does nothing** → class override set without pushing the mix, wrong sound class,
  or the asset is routed to a different class.
- **Slider resets on restart** → override not saved/reapplied; save the setting and push it on
  load.
- **Loop keeps playing after death** → attached component not stopped in `EndPlay`.
- **Music restarts on level change** → music component lives on a level actor. Use a persistent
  audio actor/GameInstance-owned component.
- **2D sound attenuates** → `PlaySound2D` with a 3D attenuation asset; 2D ignores attenuation, so
  the bug is usually using `PlaySoundAtLocation` for UI.
- **MetaSound parameter ignored** → parameter name typo or not exposed as an input; verify in the
  MetaSound editor.
- **Too many voices** → long falloff + no culling. Check the audio stats and set concurrency.

## References

- Read `references/attenuation-mixes-and-networking.md` for the API table, attenuation/concurrency
  settings, sound class/submix routing, MetaSound parameters and an audio test checklist.

## Related skills

- `audio-design` — mixing, adaptive music, ducking and SFX design.
- `unreal-replication` — multicast/Client RPC rules this audio relies on.
- `unreal-cpp-gameplay` — actors and components that own audio.
- `unreal-packaging` — cooking audio assets and project settings.
- `unity-audio` — the equivalent mixer/spatial workflow in Unity.
