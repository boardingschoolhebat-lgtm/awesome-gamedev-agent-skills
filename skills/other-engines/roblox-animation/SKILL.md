---
name: roblox-animation
description: >
  Animation in Roblox: Animator and AnimationTrack, loading animations correctly (not deprecated
  Humanoid:LoadAnimation), Play/Stop/AdjustSpeed/AdjustWeight, priority layering, marker events and
  Ended, R6 vs R15 rigs, custom rigs with AnimationController, and server/client replication of
  emotes and attacks. Use when a Roblox experience needs character or rig animations.
---

# Roblox animation

Roblox animation is track-based: an `Animator` loads an `Animation` asset into an
`AnimationTrack`, and gameplay calls `Play`, `Stop`, `AdjustSpeed` and `AdjustWeight` on tracks.
`Humanoid:LoadAnimation` is deprecated; always go through the `Animator`. Targets current Roblox
engine APIs.

## When to use

- Use when adding walk/run/idle overrides, attacks, emotes, hit reactions or animated props.
- Use when animations do not play, fight each other, or only play for one player.

**When *not* to use:** character movement/state → `roblox-characters`; UI → `roblox-ui`; audio →
`roblox-audio`; remotes for triggering emotes → `roblox-networking`.

## Core workflow

1. **Get the Animator** (`Humanoid:WaitForChild("Animator")` or an `AnimationController`'s
   `Animator` for non-humanoid rigs).
2. **Create `Animation` instances** once with `AnimationId`; load each into a track once at
   startup, not per play.
3. **Play with intent**: `track:Play(fadeTime, weight, speed)`; `Stop(fadeTime)` to blend out.
4. **Set `Priority`** so actions override locomotion instead of being overridden.
5. **Tune speed** to movement (`AdjustSpeed`) to avoid foot sliding.
6. **Handle events** with `GetMarkerReachedSignal`, `Ended` and `DidLoop`.
7. **Replicate deliberately**: play on the server for everyone, or on the client for local
   feedback; use remotes for player-triggered emotes.

## Patterns

### 1. Load tracks once

```lua
local character = script.Parent
local humanoid = character:WaitForChild("Humanoid")
local animator = humanoid:WaitForChild("Animator")

local function track(id: string): AnimationTrack
    local animation = Instance.new("Animation")
    animation.AnimationId = id
    return animator:LoadAnimation(animation)
end

local idle = track("rbxassetid://507766666")
local run = track("rbxassetid://507767714")
local attack = track("rbxassetid://1234567890")
```

- `Animator` must be in the Workspace; `LoadAnimation` errors otherwise.
- Load once and reuse; `LoadAnimation` always creates a new track, so calling it per play leaks
  memory and hurts performance.
- To find an already-loaded track, use `Animator:GetTrackByAnimationId` (when available) instead
  of reloading.

### 2. Play, blend and stop

```lua
run:Play(0.2)                 -- fade in over 0.2 s
run:AdjustSpeed(humanoid.WalkSpeed / 16)  -- match movement speed

attack:Play(0.1, 1, 1)        -- fadeTime, weight, speed
attack.Stopped:Connect(function()
    -- optional cleanup
end)
attack:Stop(0.15)             -- blend out
```

- `Play(fadeTime, weight, speed)`; `fadeTime` 0 is an instant snap.
- `Stop(fadeTime)` blends out; `IsPlaying` tells you whether it is active.
- `AdjustSpeed` changes rate live; `Speed` reads it back.
- `AdjustWeight(weight, fadeTime)` layers a pose (aim/upper body) without stopping the track.
- `TimePosition` and `Length` are useful for sync and UI; `Length` can be 0 until loaded.

### 3. Priority layering

```lua
attack.Priority = Enum.AnimationPriority.Action
idle.Priority = Enum.AnimationPriority.Idle
run.Priority = Enum.AnimationPriority.Movement
```

Priority order (low to high): `Idle`, `Movement`, `Action`, `Action2`, `Action3`, `Action4`,
`Core`. Higher-priority tracks override lower ones on shared joints.

- Use `Action` for attacks/interactions; `Action2`–`Action4` for stacking (e.g. hit reaction over
  attack).
- `Core` is for engine-level poses; avoid unless you are replacing the whole rig.
- Two tracks with the same priority blend by weight, which can look muddy; separate by priority.

### 4. Marker events and completion

```lua
attack:GetMarkerReachedSignal("Hit"):Connect(function()
    -- apply damage / spawn VFX at the hit frame
end)

attack.Ended:Connect(function()
    attacking = false
end)

attack.DidLoop:Connect(function()
    -- fires each loop for looping tracks
end)
```

- Marker names must match the keyframe markers authored on the animation asset.
- `Ended` fires when the track stops (including manual `Stop`); check `IsPlaying` if you only care
  about natural completion.
- For gameplay, prefer server-side timing for damage; markers are cosmetic unless validated.

### 5. Custom rigs and R6/R15

```lua
-- Non-humanoid rig: AnimationController + Animator
local controller = rig:FindFirstChildOfClass("AnimationController")
    or Instance.new("AnimationController", rig)
local animator = controller:FindFirstChildOfClass("Animator")
    or Instance.new("Animator", controller)

local track = animator:LoadAnimation(animation)
track:Play()
```

- Humanoid characters use the Humanoid's `Animator`; props/vehicles use `AnimationController`.
- R6 and R15 rigs need animations authored for that rig type; a mismatched animation will not
  play correctly.
- Custom rigs need the same joint names the animation targets.

### 6. Replication

```lua
-- Server: everyone sees the emote.
local emote = animator:LoadAnimation(emoteAnimation)
emote:Play()

-- Client: local-only feedback.
local localTrack = localAnimator:LoadAnimation(uiPulse)
localTrack:Play()
```

- Tracks loaded/played on the server replicate to clients for that character.
- For a player-triggered emote, validate the request on the server, then play there; do not trust
  a client to decide gameplay-affecting animation state.
- Client-owned characters: `Animator:LoadAnimation` on the client also informs the server for that
  character.
- Avoid playing the same emote on both server and client (double playback).

## Pitfalls

- **`Humanoid:LoadAnimation` used** → deprecated and can break replication. Use the `Animator`.
- **Animation does not play** → no `Animator`, Animator not in Workspace, wrong rig type, or the
  asset is not owned/authorized.
- **Only one player sees it** → played in a LocalScript. Play on the server for shared animation.
- **Animation fights locomotion** → default `Idle`/`Movement` priorities; set `Action` for
  one-shots.
- **Foot sliding** → fixed playback speed. Scale with `WalkSpeed` via `AdjustSpeed`.
- **Memory growth** → `LoadAnimation` called every play. Load once and reuse.
- **Marker never fires** → marker name typo or missing keyframe marker in the asset.
- **Animation stuck after death** → tracks not stopped/cleaned on respawn; tracks are per-Animator,
  recreate after respawn.
- **R6 animation on R15** → rig mismatch; author per rig type.
- **Emote double-plays** → both server and client call `Play`.

## References

- Read `references/tracks-priority-and-replication.md` for the Animator/AnimationTrack API table,
  priority levels, marker events, replication rules and an animation test checklist.

## Related skills

- `roblox-characters` — Humanoid state and character lifecycle.
- `roblox-networking` — remotes and server validation for emotes/attacks.
- `roblox-luau` — scripting conventions.
- `roblox-audio` — syncing sounds to animation markers.
- `unreal-animation` / `unity-animation` — equivalent track/state-machine workflows.
