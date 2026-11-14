---
name: bevy-audio
description: >
  Audio in Bevy 0.20: AudioPlayer and PlaybackSettings, one-shot SFX and looping music, volume
  with the Volume type, controlling playback through AudioSink/AudioSinkPlayback, spatial audio
  with SpatialAudioSink and AudioListener, despawn-on-finish, and grouping volumes for settings.
  Use when a Bevy game needs sound effects, music or audio settings. Targets Bevy 0.20.
---

# Bevy audio

Bevy audio is ECS: spawn an entity with `AudioPlayer` and `PlaybackSettings`; Bevy adds an
`AudioSink` (or `SpatialAudioSink`) once playback starts, and that sink is how you control volume,
pause, speed and position. Targets **Bevy 0.20**.

## When to use

- Use when a Bevy game needs SFX, music, ambience, UI sounds or volume settings.
- Use when audio does not stop, cannot be paused, or plays at the wrong place.

**When *not* to use:** mixing/adaptive-music design → `audio-design`; ECS basics → `bevy-ecs`;
UI sliders → `bevy-ui`; persistence of volume → `bevy-save`.

## Core workflow

1. **Spawn** `(AudioPlayer::new(handle), PlaybackSettings::DESPAWN)` for one-shots and
   `PlaybackSettings::LOOP` for music.
2. **Set initial options** in `PlaybackSettings` (`volume`, `speed`, `paused`, `muted`, `spatial`).
3. **Find the sink** with `Query<&AudioSink, With<Music>>` once it exists (it appears after the
   asset loads).
4. **Control playback** through the sink: `pause`, `play`, `toggle_playback`, `set_volume`,
   `set_speed`.
5. **Spatial audio**: `with_spatial(true)`, an `AudioListener` on the camera, and a `Transform` on
   the emitter.
6. **Group volumes** with your own `MusicVolume`/`SfxVolume` resources and apply the product.
7. **Test** with the audio feature enabled and on a machine with a device.

## Patterns

### 1. One-shot SFX and looping music

```rust
use bevy::prelude::*;

#[derive(Component)]
struct Music;

fn play_sfx(mut commands: Commands, assets: Res<AssetServer>) {
    commands.spawn((
        AudioPlayer::new(assets.load("sounds/hit.ogg")),
        PlaybackSettings::DESPAWN,          // entity removed when the sound ends
    ));
}

fn play_music(mut commands: Commands, assets: Res<AssetServer>) {
    commands.spawn((
        Music,
        AudioPlayer::new(assets.load("music/theme.ogg")),
        PlaybackSettings::LOOP.with_volume(Volume::Linear(0.5)),
    ));
}
```

- `PlaybackSettings::DESPAWN` avoids leaking one-shot entities.
- `PlaybackSettings::LOOP` loops forever; `PlaybackMode::Once` plays once.
- Changing `PlaybackSettings` after playback starts has no effect; use the sink.
- The asset can still be loading when spawned; playback begins when it is ready.

### 2. Volume, speed and pause

```rust
fn controls(
    keys: Res<ButtonInput<KeyCode>>,
    music: Query<&AudioSink, With<Music>>,
) {
    let Ok(sink) = music.single() else { return };

    if keys.just_pressed(KeyCode::Space) {
        sink.toggle_playback();
    }
    if keys.just_pressed(KeyCode::Equal) {
        sink.set_volume(sink.volume().increase_by_percentage(10.0));
    }
    if keys.just_pressed(KeyCode::Minus) {
        sink.set_volume(sink.volume().increase_by_percentage(-10.0));
    }
}
```

- `AudioSink` implements `AudioSinkPlayback`: `volume`, `set_volume`, `speed`, `set_speed`,
  `play`, `pause`, `is_paused`, `toggle_playback`, `position`, `mute`/`unmute`.
- `Volume` can be linear or decibels; prefer linear values from sliders.
- The sink exists only after the audio starts; a `single()` that fails on the first frames is
  normal — guard with `let Ok(...)`.
- To stop permanently, despawn the audio entity.

### 3. Music switching

```rust
fn switch_track(
    mut commands: Commands,
    assets: Res<AssetServer>,
    current: Query<Entity, With<Music>>,
    request: Res<ChangeTrack>,
) {
    for e in &current {
        commands.entity(e).despawn();
    }
    commands.spawn((
        Music,
        AudioPlayer::new(assets.load(request.0.clone())),
        PlaybackSettings::LOOP.with_volume(Volume::Linear(0.5)),
    ));
}
```

- One music entity at a time; despawn the old one before spawning the new.
- For a fade, step the sink volume in a system with `Time` then swap.
- Do not spawn a new track every frame from an input system.

### 4. Spatial audio

```rust
fn setup_listener(mut commands: Commands) {
    commands.spawn((
        Camera3d::default(),
        Transform::from_xyz(0.0, 2.0, 8.0),
        AudioListener,                 // required for spatial playback
    ));
}

fn spawn_emitter(mut commands: Commands, assets: Res<AssetServer>) {
    commands.spawn((
        Transform::from_xyz(4.0, 1.0, 0.0),
        AudioPlayer::new(assets.load("sounds/engine.ogg")),
        PlaybackSettings::LOOP.with_spatial(true),
    ));
}
```

- Spatial playback needs an `AudioListener` (usually on the camera); without it, audio is silent
  or non-positional.
- `SpatialAudioSink` is the control component for spatial sounds.
- `PlaybackSettings.spatial_scale` tunes distance units; set it deliberately for large worlds.
- Update the emitter `Transform`; the sink follows the entity.

### 5. Volume groups and settings

```rust
#[derive(Resource)]
struct AudioSettings {
    master: f32,
    music: f32,
    sfx: f32,
}

fn apply_music_volume(
    settings: Res<AudioSettings>,
    music: Query<&AudioSink, With<Music>>,
) {
    if !settings.is_changed() { return; }
    let Ok(sink) = music.single() else { return };
    sink.set_volume(Volume::Linear(settings.master * settings.music));
}
```

- Apply the product on settings change; SFX apply theirs when spawned.
- Persist with `bevy-save`; a resource alone resets on restart.
- Mute is separate from volume so unmute restores the old level.

## Pitfalls

- **Silence** → audio feature/plugin missing, no audio device, or a spatial sound without an
  `AudioListener`.
- **Cannot control playback** → querying `AudioPlayer` instead of `AudioSink`; the sink appears
  only after loading.
- **Settings changes ignored** → mutating `PlaybackSettings` on a playing entity. Use the sink.
- **One-shots leak entities** → no `PlaybackSettings::DESPAWN`. Despawn when finished.
- **Music restarts** → respawning the track on state changes. Keep it alive or move it to a
  persistent entity.
- **Pause resumes from the start** → despawned/restarted instead of `sink.pause()`.
- **Spatial audio is mono/flat** → listener missing or not on the camera; check `Transform`.
- **Headless/CI tests hang or fail** → audio device unavailable. Gate audio systems or use a
  feature/test profile without `bevy_audio`.
- **Volume slider jumps** → setting absolute values from relative deltas; keep a single source of
  truth in a resource.

## References

- Read `references/players-sinks-and-spatial.md` for the audio component table, sink methods,
  spatial setup, volume math and an audio test checklist.

## Related skills

- `bevy-ecs` — entities, components and resources this audio uses.
- `bevy-ui` — volume sliders and mute toggles.
- `bevy-save` — persisting audio settings.
- `audio-design` — mixing, ducking and adaptive music design.
- `ebitengine-audio` / `roblox-audio` — equivalent patterns in other engines.
