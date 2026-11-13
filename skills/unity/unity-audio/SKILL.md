---
name: unity-audio
description: >
  Implement Unity 6.3 audio: AudioSource and AudioListener setup, 2D versus 3D spatial sound,
  AudioMixer groups and exposed volume parameters with dB conversion, snapshots for pause and
  ducking, pooled one-shots, music crossfades, and mobile/WebGL import settings. Use when a
  Unity project needs sound effects, music, mixer volume sliders, spatial audio, or audio that is
  silent, clipped, or distorted. Targets Unity 6.3 LTS (6000.3).
---

# Unity audio

Route every sound through an `AudioMixer`, keep sources pooled, and convert player-facing volume
to decibels before touching a mixer parameter. Targets **Unity 6.3 LTS (6000.3)**.

## When to use

- Use when adding SFX, music, ambience, UI sounds, spatial audio or volume settings.
- Use when audio is silent, too loud, distorted, non-spatial, or keeps playing while paused.

**When *not* to use:** sound design and adaptive-music structure → `audio-design`; input for
volume sliders → `unity-input-system`; audio-reactive visuals → `unity-ui` plus this skill;
engine-neutral mixing concepts → `audio-design`.

## Core workflow

1. **One AudioListener.** It usually lives on the main camera. Two active listeners produce
   warnings and unpredictable attenuation.
2. **Build a mixer.** Create an `AudioMixer` asset with groups (`Master`, `Music`, `SFX`, `UI`,
   `Ambience`), expose each group's `Volume` in dB, and route sources with
   `AudioSource.outputAudioMixerGroup`.
3. **Choose 2D or 3D per source.** `spatialBlend = 0` for music/UI, `1` for world sounds, with
   `minDistance`/`maxDistance` and a rolloff curve that matches the world scale.
4. **Convert volume once.** Sliders are linear 0–1; mixer volume is dB. Use
   `Mathf.Log10(Mathf.Clamp(value, 0.0001f, 1f)) * 20f` and set the exposed parameter.
5. **Pool one-shots.** A small pool of `AudioSource`s with `PlayOneShot(clip, volumeScale)` avoids
   creating and destroying objects per shot.
6. **Crossfade music with two sources.** Fade one out and the other in over a coroutine; do not
   restart the same source with a new clip mid-fade.
7. **Pause deliberately.** `AudioListener.pause = true` stops all audio; a mixer snapshot can
   instead low-pass and duck the game while the menu keeps its own sounds.
8. **Verify on the target platform.** Check import settings, voice count and the WebGL/user-gesture
   rule in a build, not only in the editor.

## Patterns

### 1. Mixer volume from a linear slider

```csharp
using UnityEngine;
using UnityEngine.Audio;
using UnityEngine.UI;

public sealed class VolumeSlider : MonoBehaviour
{
    [SerializeField] private AudioMixer mixer;
    [SerializeField] private string parameter = "MusicVolume";   // an exposed parameter name
    [SerializeField] private Slider slider;

    private void Awake()
    {
        slider.minValue = 0.0001f;      // log(0) is -infinity; keep a floor
        slider.maxValue = 1f;
        slider.onValueChanged.AddListener(SetVolume);
    }

    private void OnDestroy() => slider.onValueChanged.RemoveListener(SetVolume);

    private void SetVolume(float linear)
    {
        var db = Mathf.Log10(Mathf.Clamp(linear, 0.0001f, 1f)) * 20f;
        mixer.SetFloat(parameter, db);   // returns false if the parameter is not exposed
    }
}
```

`SetFloat` needs the parameter exposed in the Audio Mixer window (right-click the volume → *Expose
to script*). Once exposed, snapshots no longer control that parameter — it is script-owned until
`ClearFloat` is called.

### 2. Route sources to groups

```csharp
[SerializeField] private AudioMixerGroup sfxGroup;
[SerializeField] private AudioMixerGroup musicGroup;

void Awake()
{
    sfxSource.outputAudioMixerGroup = sfxGroup;
    musicSource.outputAudioMixerGroup = musicGroup;
    musicSource.loop = true;
    musicSource.spatialBlend = 0f;       // music is 2D
    sfxSource.spatialBlend = 0f;         // UI/2D SFX
}
```

A source with no mixer group bypasses the mixer and ignores its volume and effects.

### 3. Pooled one-shots

```csharp
using System.Collections.Generic;
using UnityEngine;

public sealed class SfxPool : MonoBehaviour
{
    [SerializeField] private AudioSource prefab;
    [SerializeField] private int size = 12;

    private readonly List<AudioSource> _sources = new();

    private void Awake()
    {
        for (var i = 0; i < size; i++)
        {
            var source = Instantiate(prefab, transform);
            source.playOnAwake = false;
            _sources.Add(source);
        }
    }

    public void Play(AudioClip clip, float volume = 1f, float pitch = 1f)
    {
        var source = _sources.Find(s => !s.isPlaying);
        if (source == null) return;             // pool exhausted: drop, do not allocate
        source.pitch = pitch;
        source.PlayOneShot(clip, volume);       // overlapping shots on one source are allowed
    }
}
```

`PlayOneShot` mixes on top of the source's current clip; a source can play several one-shots at
once. The pool caps simultaneous voices, which is the usual fix for mobile crackle.

### 4. Music crossfade

```csharp
using System.Collections;
using UnityEngine;

public sealed class MusicPlayer : MonoBehaviour
{
    [SerializeField] private AudioSource a;
    [SerializeField] private AudioSource b;

    public void Crossfade(AudioClip next, float seconds = 1.5f)
    {
        StartCoroutine(CrossfadeRoutine(next, seconds));
    }

    private IEnumerator CrossfadeRoutine(AudioClip next, float seconds)
    {
        var incoming = a.isPlaying ? b : a;
        var outgoing = incoming == a ? b : a;

        incoming.clip = next;
        incoming.volume = 0f;
        incoming.Play();

        for (var t = 0f; t < seconds; t += Time.unscaledDeltaTime)
        {
            var k = t / seconds;
            incoming.volume = k;
            outgoing.volume = 1f - k;
            yield return null;
        }

        outgoing.Stop();
        outgoing.volume = 1f;
        incoming.volume = 1f;
    }
}
```

Use `unscaledDeltaTime` so a fade completes while the game is paused; both sources must be routed
to the same music group.

### 5. Pause and ducking with snapshots

```csharp
[SerializeField] private AudioMixerSnapshot gameplay;
[SerializeField] private AudioMixerSnapshot paused;

public void SetPaused(bool value)
{
    var snapshot = value ? paused : gameplay;
    snapshot.TransitionTo(0.15f);      // seconds
}
```

A paused snapshot can low-pass the Music/SFX groups and keep a UI group audible. This is usually
better than `AudioListener.pause`, which silences menu sounds too. Call `TransitionTo` once on the
state change, not every frame, and give the mixer's `updateMode` a sensible value for scaled or
unscaled transitions.

### 6. 3D sound setup

```csharp
source.spatialBlend = 1f;              // fully 3D
source.rolloffMode = AudioRolloffMode.Logarithmic;
source.minDistance = 2f;               // full volume inside this radius
source.maxDistance = 40f;              // beyond this the source is inaudible in practice
source.dopplerLevel = 0f;              // disable unless the project models doppler
```

`minDistance`/`maxDistance` are in world units (metres by Unity convention). A 3D source with
`spatialBlend` left at 0 is the usual "why is this sound everywhere" bug.

## Pitfalls

- **No sound at all** → no `AudioListener`, the source is muted/not playing, the mixer group is
  muted, or the clip's import settings produced silence. Check the Audio Mixer window and the
  source's group.
- **Volume slider does nothing** → the mixer parameter is not exposed, or `SetFloat` returns false
  because snapshots currently control it. Expose the parameter and call `ClearFloat` if a snapshot
  should hand control back.
- **Slider feels wrong** → linear amplitude was written straight to a dB parameter. Convert with
  `20 * log10(value)` and floor the zero case.
- **Clip is distorted** → too many voices at once, summed amplitude above 0 dB, or the clip was
  imported compressed at a high volume. Cap voices with a pool and leave headroom on Master.
- **3D sound has no direction** → `spatialBlend = 0`, or the listener is not on the camera. Set
  the blend and verify listener placement.
- **Audio continues during pause** → `AudioListener.pause` was not set, or the source uses
  `ignoreListenerPause`. Prefer mixer snapshots for partial pause.
- **Menu sounds cut off by pause** → `AudioListener.pause` pauses everything. Use a snapshot and
  keep UI sounds on an un-paused group.
- **Two listeners warning** → a second camera or prefab carries an `AudioListener`. Keep exactly
  one enabled.
- **WebGL is silent until a click** → browsers require a user gesture to start audio. Initialize
  or resume audio from a click/keypress in the game's start flow.
- **Mobile crackle or dropouts** → too many simultaneous compressed clips, a too-small DSP
  buffer, or `Load In Memory` on large music files. Use streaming for music, compressed in memory
  for SFX, and lower the voice count.
- **`PlayClipAtPoint` leaves objects around** → it creates a temporary object per call. For
  repeated sounds, use a pool instead.

## References

- Read `references/mixers-spatial-and-imports.md` for the audio API table, mixer routing and
  snapshot rules, spatial curves, import settings and a platform test checklist.

## Related skills

- `audio-design` — adaptive music, layering, ducking design and mixing goals.
- `unity-ui` — volume sliders and settings screens.
- `unity-csharp-scripting` — coroutines, lifetime and serialization for audio components.
- `godot-audio` / `unreal-niagara`-adjacent audio work — other engines' audio pipelines.
