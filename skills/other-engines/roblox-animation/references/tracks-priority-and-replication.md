# Tracks, priority and replication (Roblox)

Depth for `roblox-animation`: the Animator/AnimationTrack API, priority layering, events and
networking rules.

## API

| Item | Notes |
|------|-------|
| `Animator` | Child of `Humanoid` (or `AnimationController`); loads and plays tracks. |
| `Animator:LoadAnimation(Animation)` | Returns a new `AnimationTrack`; must be in Workspace. |
| `Animator:GetTrackByAnimationId(id)` | Look up an existing track instead of reloading (when available). |
| `Animator:GetPlayingAnimationTracks()` | Active tracks for state checks. |
| `Animation` | Asset wrapper; set `AnimationId`. |
| `AnimationTrack:Play(fadeTime, weight, speed)` | Blend in and play. |
| `AnimationTrack:Stop(fadeTime)` | Blend out. |
| `AnimationTrack:AdjustSpeed(speed)` | Live playback rate. |
| `AnimationTrack:AdjustWeight(weight, fadeTime)` | Layer strength. |
| `AnimationTrack.Priority` | `Enum.AnimationPriority`. |
| `AnimationTrack.Length` | Seconds; may be 0 until loaded. |
| `AnimationTrack.Speed` / `TimePosition` | Read/write playback state. |
| `AnimationTrack.Looped` | Loop flag. |
| `AnimationTrack:GetMarkerReachedSignal(name)` | Keyframe marker event. |
| `AnimationTrack.Ended` / `DidLoop` | Completion events. |
| `AnimationController` | Animator host for non-humanoid rigs. |

Deprecated: `Humanoid:LoadAnimation`, `AnimationController:LoadAnimation`, `Pitch`-era APIs.

## Priority

Low to high:

```text
Idle < Movement < Action < Action2 < Action3 < Action4 < Core
```

- Locomotion uses `Idle`/`Movement` (default animation scripts).
- Attacks/interactions use `Action`; stack reactions with `Action2`–`Action4`.
- `Core` overrides everything; reserve for full-body replacements.
- Equal priority tracks blend by weight; separate by priority for predictable overrides.

## Blending

- `Play(fadeTime, weight, speed)`: `fadeTime` 0 snaps, 0.1–0.3 blends.
- `Stop(fadeTime)`: blend out; the track remains loaded.
- `AdjustWeight` for additive-style layering (aim, upper body).
- Foot sliding: `run:AdjustSpeed(humanoid.WalkSpeed / baseSpeed)`.
- Retargeting between R6/R15 is not automatic; author per rig.

## Events

| Event | Use |
|-------|-----|
| `GetMarkerReachedSignal("Hit")` | Hit frame, footstep, VFX |
| `Ended` | Track stopped/finished |
| `DidLoop` | Each loop iteration |
| `Stopped` | Stopped (including manual) |

- Markers must exist on the animation asset.
- Server-side gameplay should not trust client marker timing for damage.
- Disconnect connections when the track is discarded to avoid leaks.

## Replication

| Where | Effect |
|-------|--------|
| Server `Animator:LoadAnimation` + `Play` | Replicates to clients for that character |
| Client (LocalScript) on owned character | Plays locally; server informed for network-owned characters |
| Client on another character | Local only; not authoritative |
| Remote event → server Play | Validated, shared playback |

- Player-triggered emotes: client requests → server validates cooldown/ownership → server plays.
- Do not play the same track on server and client; it can double-play.
- Respawning creates a new character/Animator; rebuild tracks after `CharacterAdded`.
- `AnimationTrack` instances are not shared across characters.

## Test checklist

1. Idle/walk/run play and blend without fighting.
2. Attack overrides locomotion, then locomotion resumes.
3. Marker fires exactly once per play at the right frame.
4. `Ended` cleans up state; interrupted stop does not grant rewards.
5. Emote triggered by one player is visible to others.
6. Local UI animation is not replicated.
7. Respawn rebuilds tracks; no stale track references.
8. R6 and R15 rigs each play their own animations.
9. Speed matches `WalkSpeed`; no foot sliding.
10. No `LoadAnimation` calls inside a loop/heartbeat.
