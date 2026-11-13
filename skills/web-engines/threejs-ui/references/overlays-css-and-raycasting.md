# Overlays, CSS renderers and raycasting (three.js r187)

Depth for `threejs-ui`: how the DOM and WebGL layers compose, the exact APIs, and the checks that
catch pointer and sizing bugs.

## API used by the skill

| API | Import / form | Notes |
|-----|---------------|-------|
| `WebGLRenderer` | `three` | Main WebGL renderer; `setSize(w, h, updateStyle)`. |
| `CSS2DRenderer` | `three/addons/renderers/CSS2DRenderer.js` | DOM overlay for labels; translation + 2D rotation only. |
| `CSS2DObject` | same module | Wraps an `HTMLElement` as a scene object; `center`, `element`, `rotation2D`. |
| `CSS3DRenderer` | `three/addons/renderers/CSS3DRenderer.js` | DOM overlay with perspective. |
| `CSS3DObject` | same module | Wraps an element in 3D space. |
| `Raycaster` | `three` | `setFromCamera(pointer, camera)`, `intersectObjects(objects, recursive)`. |
| `Vector2` | `three` | Normalized device coordinates for the pointer. |
| `ResizeObserver` | browser | Re-layout on container size changes. |
| `setAnimationLoop` | renderer | `renderer.setAnimationLoop(cb)` replaces a manual rAF loop. |

## Layering model

```text
container (position: relative)
├── canvas (WebGL)              z-index auto
├── CSS2D/CSS3D renderer div    position: absolute; inset: 0
└── HUD div                     position: absolute; inset: 0
```

- The canvas and the overlay share a parent; the overlay uses `inset: 0`.
- `pointer-events: none` on the overlay, `auto` on buttons/inputs.
- CSS overlays are not depth-tested against WebGL; they composite on top.
- Request fullscreen on the **container**, so the overlay stays visible.
- One CSS renderer per container; appending twice creates duplicate DOM trees.

## CSS2D vs CSS3D

| | CSS2D | CSS3D |
|-|-------|-------|
| Transforms | translation + 2D rotation | full 3D perspective |
| Text crispness | always screen-aligned | perspective-scaled |
| Cost | one DOM node per label | heavier, CSS transforms per frame |
| Use for | labels, markers, nameplates | in-world panels, screens |
| Clipping | always on top | limited/awkward |

Both only transform their own DOM element; they do not occlude or get occluded by WebGL geometry.

## Pointer coordinates

```js
const rect = renderer.domElement.getBoundingClientRect();
pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
```

- `clientX/Y` are viewport coordinates; subtract the canvas rect.
- Do not use `window.innerWidth/Height` when the canvas is not full-screen.
- On high-DPR screens the CSS rect is the right reference; the drawing buffer size is not.
- For touch, pointer events cover both; handle `pointercancel` to clear hover state.

## Raycast details

- `intersectObjects(objects, true)` includes descendants; pass a curated array for performance.
- Use `raycaster.layers` to restrict hits to an interaction layer.
- Sort by distance and pick the first hit; stop at walls if the scene uses occluders.
- Invisible `Mesh` with `visible = false` is skipped; use `material.opacity = 0` or a separate
  hit-proxy mesh when you need an invisible target.
- Update hover on `pointermove`, click on `pointerdown` (or `pointerup` for drag disambiguation).
- Recompute the ray after any camera or canvas change, not once at startup.

## Label performance

- One DOM node per label; 200 labels is already a lot. Pool and reuse.
- Hide labels by distance/angle instead of keeping hundreds of off-screen nodes.
- Avoid layout-triggering CSS inside labels (no width/height reads per frame).
- For dense text in the world, consider a canvas texture atlas instead of DOM labels.

## Responsive checklist

1. Full-screen and embedded in a 400 px panel: HUD and labels align, no scrollbars.
2. Resize while running: canvas, projection, label renderer and HUD all update.
3. Device pixel ratio 1, 2 and 3: text crisp, no giant canvas.
4. Fullscreen: HUD remains visible (fullscreen the container).
5. Overlay clicks do not reach the scene; scene clicks still work outside interactive HUD.
6. Labels hide when their anchor is occluded or far away.
7. 3D buttons: hover and click land exactly on the mesh at every aspect ratio.
8. Keyboard: tab reaches HTML buttons; Escape closes panels; focus visible.
