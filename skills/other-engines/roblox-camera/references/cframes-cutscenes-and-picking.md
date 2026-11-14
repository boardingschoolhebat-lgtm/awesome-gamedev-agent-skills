# CFrames, cutscenes and picking (Roblox)

Depth for `roblox-camera`: camera API, CFrame math, render-loop priorities, tweening and
screen-space conversion.

## Camera API

| Member | Notes |
|--------|-------|
| `workspace.CurrentCamera` | This client's camera; may be nil briefly at startup. |
| `Camera.CFrame` | Position + orientation. |
| `Camera.CameraType` | `Custom`, `Scriptable`, `Fixed`, `Follow`, `Orbital`, `Attach`, `Watch`, `Track`, `CameraToggle`. |
| `Camera.CameraSubject` | Humanoid/BasePart the default scripts follow. |
| `Camera.FieldOfView` | Vertical FOV, 1–120, default 70. |
| `Camera.Focus` | Look-at point for scripts. |
| `Camera:GetRenderCFrame()` | Actual rendered CFrame (VR/head tracking). |
| `Camera:ScreenPointToRay(x, y, depth)` | Ray including GUI inset. |
| `Camera:ViewportPointToRay(x, y, depth)` | Ray without GUI inset. |
| `Camera:WorldToViewportPoint(p)` | `(Vector3, onScreen)` without inset. |
| `Camera:WorldToScreenPoint(p)` | `(Vector3, onScreen)` with inset. |
| `Camera:ZoomToExtents(cframe, size)` | Frame a volume. |

## CFrame math

```lua
-- Look from a position at a target:
local cf = CFrame.lookAt(cameraPos, targetPos)

-- Offset in camera space (right, up, back):
local offset = CFrame.new(2.5, 1.5, 12)
local desired = root.CFrame * offset

-- Lerp position + rotation:
local alpha = 1 - math.exp(-speed * dt)
current = current:Lerp(desired, alpha)

-- Shake without accumulating:
camera.CFrame = current * CFrame.new(shakeOffset)
```

- `CFrame.lookAt` handles arbitrary up vectors only if the direction is not parallel to up.
- Multiplying CFrames composes transforms; `* CFrame.new(...)` offsets in local space.
- Store the unshaken `current` separately; never feed shake back into it.

## Render loop

| Loop | Use |
|------|-----|
| `RunService.RenderStepped` | Camera and anything that must match the frame. |
| `RunService:BindToRenderStep(name, priority, fn)` | Ordered camera updates; use a priority after `Enum.RenderPriority.Camera.Value` for shake. |
| `RunService.Heartbeat` | Gameplay that does not need frame sync. |
| `RunService.Stepped` | Physics-step logic. |

- Camera work belongs on the client and in the render step.
- Disconnect `RenderStepped` connections when the mode ends, or multiple cameras fight.

## Cutscenes

1. Save `CameraType`, `CFrame`, `CameraSubject`, `FieldOfView`.
2. Set `Scriptable`.
3. Tween `CFrame` (and optionally FOV) with `TweenService`.
4. On finish or skip: `tween:Cancel()`, restore saved values.
5. Re-enable the default camera by restoring `Custom` and the humanoid subject.

Do not tween `CameraType`; it is an enum, not a numeric property.

## Screen-space conversion

```lua
local screenPos, visible = camera:WorldToViewportPoint(worldPos)
-- screenPos.X/Y in pixels; screenPos.Z depth
```

- `WorldToScreenPoint` accounts for the GUI inset; `WorldToViewportPoint` does not. Use the one
  matching your UI coordinate space.
- `ScreenPointToRay` accounts for the inset; `ViewportPointToRay` does not.
- `ScreenPointToRay(x, y, depth)` starts the ray at the given depth; default 0.
- Raycast with `workspace:Raycast(ray.Origin, ray.Direction * range, params)` and ignore the
  character.

## Test checklist

1. Scriptable camera holds its CFrame; no snap-back.
2. Follow is smooth at 30/60/144 fps and after respawn.
3. Cutscene starts, skips and restores the camera fully.
4. First person hides the local head; shoulder aim lines up with the crosshair.
5. Shake decays, does not drift, respects the accessibility toggle.
6. FOV kick restores.
7. Aim ray hits the cursor position under the topbar on desktop and mobile.
8. World markers align with parts and hide when off-screen.
9. VR: `GetRenderCFrame` used where needed.
10. No duplicate camera loops after switching modes.
