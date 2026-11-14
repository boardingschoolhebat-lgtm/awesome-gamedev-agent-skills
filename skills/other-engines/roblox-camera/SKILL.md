---
name: roblox-camera
description: >
  Roblox camera control from LocalScripts: workspace.CurrentCamera, CameraType.Scriptable,
  CFrame/lookAt, follow and orbit rigs, TweenService cutscenes, first-person and shoulder views,
  camera shake, field of view, and world↔screen conversion with ScreenPointToRay and
  WorldToViewportPoint. Use when a Roblox experience needs a custom camera, cutscene or aiming.
---

# Roblox camera

The camera is per-client: each player has `workspace.CurrentCamera` in their local Workspace, and
only a `LocalScript` should drive it. Set `CameraType` to `Scriptable` to take control from the
default scripts, then write `CFrame` each frame or tween it. 

## When to use

- Use when building a custom follow/orbit camera, cutscene, first-person view, or aim ray.
- Use when the default camera fights your script, or a cutscene does not restore control.

**When *not* to use:** character movement → `roblox-characters`; input remapping →
`input-systems`; UI → `roblox-ui`; engine-neutral camera design → `camera-systems`.

## Core workflow

1. **Run on the client**: `LocalScript` in `StarterPlayerScripts`/`StarterCharacterScripts`.
2. **Get the camera** with `workspace.CurrentCamera` and wait for it if nil.
3. **Take control**: `camera.CameraType = Enum.CameraType.Scriptable` (or `Custom` to keep some
   default behavior).
4. **Compute a target `CFrame`** with `CFrame.lookAt(position, target)`; smooth with
   `CFrame:Lerp(alpha)` in `RenderStepped` or `BindToRenderStep`.
5. **Add effects** (shake, FOV kick) as offsets on top of the base CFrame.
6. **Restore** the previous `CameraType`/`CameraSubject`/`CFrame` when a cutscene ends.
7. **Test on low-end mobile and with VR** (`GetRenderCFrame` differs from `CFrame`).

## Patterns

### 1. Scriptable follow camera

```lua
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local player = Players.LocalPlayer
local camera = workspace.CurrentCamera

local OFFSET = Vector3.new(0, 8, 14)
local SMOOTH = 8

camera.CameraType = Enum.CameraType.Scriptable

local current = camera.CFrame

RunService.RenderStepped:Connect(function(dt)
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not root then return end

    local desired = CFrame.lookAt(root.Position + OFFSET, root.Position + Vector3.new(0, 1, 0))
    local alpha = 1 - math.exp(-SMOOTH * dt)   -- frame-rate independent
    current = current:Lerp(desired, alpha)
    camera.CFrame = current
end)
```

- `CFrame:Lerp` handles position and rotation; do not lerp components separately.
- `1 - exp(-k*dt)` is frame-rate independent; a raw `0.1` is not.
- Read the character each frame; it can respawn.
- Set `CameraType` once, not every frame.

### 2. Cutscene with TweenService

```lua
local TweenService = game:GetService("TweenService")

local function playCutscene(camera, targetCFrame, seconds)
    local previousType = camera.CameraType
    local previousCFrame = camera.CFrame
    camera.CameraType = Enum.CameraType.Scriptable

    local tween = TweenService:Create(
        camera,
        TweenInfo.new(seconds, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut),
        { CFrame = targetCFrame }
    )
    tween:Play()
    tween.Completed:Wait()

    return function()
        camera.CFrame = previousCFrame
        camera.CameraType = previousType
    end
end
```

- Save and restore both `CameraType` and `CFrame`; otherwise the player is left staring at the
  cutscene angle.
- `TweenService` on `CFrame` interpolates position and rotation together.
- Cancel the tween (`tween:Cancel()`) if the player skips.
- Do not tween `CameraType`; set it directly.

### 3. First-person and shoulder views

```lua
-- First person: lock the camera to the head and hide the character's local parts.
camera.CameraType = Enum.CameraType.Scriptable
RunService.RenderStepped:Connect(function()
    local head = player.Character and player.Character:FindFirstChild("Head")
    if head then
        camera.CFrame = head.CFrame * CFrame.new(0, 0.5, 0)
    end
end)

-- Shoulder: offset to the right and slightly up.
local shoulder = CFrame.new(2.5, 1.5, 0)
camera.CFrame = root.CFrame * shoulder
```

- First-person: hide the local character's head/body (`LocalTransparencyModifier`) or the view is
  blocked.
- Keep the humanoid's `CameraOffset` in mind if you use the default `Custom` camera.
- For over-the-shoulder aiming, offset the target point, not only the camera position, or the
  crosshair misaligns.

### 4. Shake and FOV kick

```lua
local shakeTime, shakeStrength = 0, 0

local function shake(strength, duration)
    shakeStrength = math.max(shakeStrength, strength)
    shakeTime = math.max(shakeTime, duration)
end

RunService:BindToRenderStep("CameraShake", Enum.RenderPriority.Camera.Value + 1, function(dt)
    local base = camera.CFrame
    if shakeTime > 0 then
        shakeTime -= dt
        local falloff = math.clamp(shakeTime / 0.25, 0, 1)
        local offset = Vector3.new(
            (math.random() * 2 - 1) * shakeStrength * falloff,
            (math.random() * 2 - 1) * shakeStrength * falloff,
            0
        )
        camera.CFrame = base * CFrame.new(offset)
    end
end)
```

- Apply shake after the base camera update; use `BindToRenderStep` with a priority after
  `Enum.RenderPriority.Camera.Value`.
- Decay with `dt`; cap the strength; gate it behind an accessibility setting.
- FOV kick: tween `FieldOfView` (1–120) and restore it.

### 5. World ↔ screen (aiming and markers)

```lua
-- Screen point → ray for mouse aim (accounts for GUI inset).
local mouse = player:GetMouse()
local ray = camera:ScreenPointToRay(mouse.X, mouse.Y)

-- Viewport point → ray (no GUI inset).
local vpRay = camera:ViewportPointToRay(mouse.X, mouse.Y)

-- World → screen for markers; z is depth (negative/behind handling needed).
local screenPos, onScreen = camera:WorldToViewportPoint(part.Position)
if onScreen then
    label.Position = UDim2.fromOffset(screenPos.X, screenPos.Y)
end
```

- `ScreenPointToRay` accounts for the topbar inset; `ViewportPointToRay` does not.
- `WorldToViewportPoint` returns `(Vector3, boolean)`; the boolean is on-screen.
- `WorldToScreenPoint` includes the GUI inset.
- Use `Raycast` from the ray origin along `ray.Direction` to find the aim point.

### 6. Restoring and multiple camera modes

- Store `CameraType`, `CameraSubject`, `CFrame`, `FieldOfView` before overriding; restore all.
- Default `CameraType` is `Custom`, which follows `CameraSubject` (Humanoid). Set `Scriptable` only
  while you own the camera.
- For a spectator camera, set `CameraSubject` to the target Humanoid and keep `Custom`, or drive
  `Scriptable` yourself.
- `Camera:ZoomToExtents(cframe, size)` frames a model for cutscenes/maps.

## Pitfalls

- **Camera snaps back** → `CameraType` is not `Scriptable`; default scripts overwrite `CFrame`.
- **Only the local player sees it** → expected: the camera is client-side. Do not try to set
  another player's camera from the server.
- **Cutscene leaves the camera stuck** → `CameraType`/`CFrame` not restored.
- **Jitter** → setting `CFrame` in `Stepped` instead of `RenderStepped`, or lerping with a
  frame-dependent alpha.
- **First-person sees the head** → local transparency not applied.
- **Aim ray misses under the topbar** → using `ViewportPointToRay` where `ScreenPointToRay` is
  needed.
- **Marker offset on mobile** → GUI inset/safe area; use the same coordinate space as the UI.
- **Shake accumulates** → adding to the stored base CFrame instead of offsetting a copy.
- **FOV stuck after sprint** → restore the original `FieldOfView`.
- **VR mismatch** → use `GetRenderCFrame()` for the actual rendered view.

## References

- Read `references/cframes-cutscenes-and-picking.md` for the camera API table, CFrame math,
  RenderStepped priorities, screen-space conversion and a camera test checklist.

## Related skills

- `roblox-characters` — Humanoid and character lifecycle the camera follows.
- `roblox-ui` — markers and screen-space UI.
- `roblox-luau` — LocalScript structure and services.
- `camera-systems` — engine-neutral follow/shake design.
- `godot-camera` / `defold-camera` — equivalent 2D/3D camera work.
