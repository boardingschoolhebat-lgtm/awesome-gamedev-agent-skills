---
name: threejs-ui
description: >
  Build UI for three.js scenes: HTML/CSS overlays and HUDs, CSS2DRenderer labels, CSS3DRenderer
  panels, raycasted 3D buttons, pointer coordinates, render order with the WebGL canvas,
  responsive sizing and pointer-events handling. Use when a three.js app needs a HUD, labels,
  menus, tooltips or clickable 3D objects. Targets three.js r187.
---

# three.js UI

three.js renders WebGL; UI is either **HTML layered over the canvas** (the default choice) or
**objects in the scene** (labels, panels, 3D buttons). Targets **three.js r187**.

## When to use

- Use when adding a HUD, menu, tooltip, label, settings panel or clickable 3D object.
- Use when HTML UI is hidden behind the canvas, clicks do not reach UI, labels drift, or 3D
  buttons miss clicks.

**When *not* to use:** scene, camera, renderer and loop basics → `threejs-scene-setup`; models →
`threejs-gltf-loading`; materials/lighting → `threejs-materials-lighting`; general UI/UX design →
`game-ui-ux`; accessibility → `accessibility`.

## Choose the layer

| Layer | Use for | Notes |
|-------|---------|-------|
| HTML/CSS overlay | HUD, menus, settings, tooltips | simplest, crisp text, accessible, no WebGL cost |
| `CSS2DRenderer` + `CSS2DObject` | labels attached to a 3D position | always face the screen, no perspective |
| `CSS3DRenderer` + `CSS3DObject` | panels/cards in 3D space | perspective, heavier, clipping limits |
| 3D meshes + `Raycaster` | in-world buttons, interactables | needs hit testing and hover feedback |
| Canvas texture / `Sprite` | diegetic labels inside the scene | blurry at distance, no DOM access |

Most games should use the HTML overlay for menus/HUD and reserve in-world objects for labels and
interactables.

## Core workflow

1. **Put the canvas and overlay in one positioned container.** `position: relative` parent,
   canvas filling it, overlay `position: absolute; inset: 0`.
2. **Decide pointer ownership.** Overlay `pointer-events: none` by default; enable
   `pointer-events: auto` only on interactive elements, or the overlay swallows orbit/click input.
3. **Size from the container.** `renderer.setSize(w, h, false)` with CSS size, update the
   projection aspect and the CSS2D renderer on resize.
4. **Render both.** `renderer.render(scene, camera)` then `labelRenderer.render(scene, camera)` in
   the same frame.
5. **Create labels** with `CSS2DObject(element)`, position them in the scene, and keep the DOM
   size independent of distance.
6. **Raycast 3D buttons** with normalized device coordinates from the canvas bounds, not
   `window.innerWidth`, when the canvas is not full-screen.
7. **Wire HTML buttons with DOM events**, not raycasting.

## Patterns

### 1. Canvas plus HTML HUD

```html
<div id="game">
  <canvas id="scene"></canvas>
  <div id="hud">
    <div class="bar"><div id="health"></div></div>
    <button id="pause">Pause</button>
  </div>
</div>
```

```css
#game { position: relative; width: 100%; height: 100vh; }
#scene { display: block; width: 100%; height: 100%; }
#hud {
  position: absolute; inset: 0;
  pointer-events: none;            /* clicks reach the canvas by default */
  font: 600 16px/1.4 system-ui, sans-serif;
  color: #fff;
}
#hud button { pointer-events: auto; }   /* only interactive elements capture input */
```

```js
const container = document.getElementById("game");
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById("scene"), antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
```

`setPixelRatio` above 2 costs fill rate for little gain; cap it. The overlay inherits the
container's size, so a resized canvas does not need a repositioned HUD.

### 2. Responsive sizing

```js
function resize() {
  const w = container.clientWidth;
  const h = container.clientHeight;
  renderer.setSize(w, h, false);          // false: do not set CSS size, CSS already does
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  labelRenderer.setSize(w, h);
}
new ResizeObserver(resize).observe(container);
```

- `ResizeObserver` beats `window.resize` when the canvas lives in a layout (sidebars, split
  views).
- Use the same width/height for both renderers, or labels drift from the scene.
- Cap `devicePixelRatio` and consider lowering it when a performance budget is tight.

### 3. HTML labels via CSS2DRenderer

```js
import { CSS2DRenderer, CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(container.clientWidth, container.clientHeight);
Object.assign(labelRenderer.domElement.style, {
  position: "absolute",
  top: "0",
  left: "0",
  pointerEvents: "none",          // labels must not block canvas input
});
container.appendChild(labelRenderer.domElement);

const div = document.createElement("div");
div.className = "world-label";
div.textContent = "Health Station";
const label = new CSS2DObject(div);
label.position.set(2, 1.5, 0);
scene.add(label);

renderer.setAnimationLoop(() => {
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);   // same scene and camera, after WebGL
});
```

CSS2D labels are DOM elements, so they stay crisp and can be styled with CSS; they always face
the camera and ignore perspective. They also always draw **on top** of the WebGL canvas, even
when the anchor is behind a wall — hide the label yourself when occluded.

### 4. Clickable 3D objects with a raycaster

```js
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

function updatePointer(event) {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

renderer.domElement.addEventListener("pointerdown", (event) => {
  updatePointer(event);
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(interactables, false);
  if (hits.length > 0) {
    hits[0].object.userData.onClick?.();
  }
});
```

- Use the canvas rectangle, not the window, when the canvas does not fill the screen.
- `intersectObjects(list, true)` recurses into children; keep the list small and use layers if the
  scene is large.
- Give hover feedback (outline, scale, cursor) before the click, or the object does not read as
  interactive.
- Touch: `pointerdown` covers mouse and touch; do not also listen for `click` on the same target.

### 5. Interactive CSS3D panels

```js
import { CSS3DRenderer, CSS3DObject } from "three/addons/renderers/CSS3DRenderer.js";

const cssRenderer = new CSS3DRenderer();
cssRenderer.setSize(container.clientWidth, container.clientHeight);
cssRenderer.domElement.style.position = "absolute";
cssRenderer.domElement.style.top = "0";
cssRenderer.domElement.style.pointerEvents = "none";
container.appendChild(cssRenderer.domElement);

const card = document.createElement("div");
card.className = "card";
card.innerHTML = "<h2>Station</h2><button>Repair</button>";
card.querySelector("button").addEventListener("click", repair);

const panel = new CSS3DObject(card);
panel.position.set(0, 1.6, -2);
panel.scale.set(0.01, 0.01, 0.01);     // CSS pixels -> world units
scene.add(panel);
```

CSS3D panels participate in perspective and can look like diegetic screens; they are heavier than
CSS2D and have clipping/ordering limitations. Scale them from pixels to world units deliberately.

## Pitfalls

- **HUD clicks pass through to the scene, or the scene stops receiving input** → `pointer-events`
  is inverted. Overlay `none`, interactive children `auto`.
- **Canvas is blurry or stretched** → `setSize` changed the CSS size, or the pixel ratio is
  uncapped. Use `setSize(w, h, false)` with CSS sizing and cap DPR.
- **Labels drift after resize** → the CSS renderer was not resized, or the canvas and overlay use
  different containers.
- **Raycast hits the wrong place** → pointer coordinates computed from `window` instead of the
  canvas rect, or the camera aspect was not updated after resize.
- **Label visible through walls** → CSS2D always draws on top. Raycast or distance-check and hide
  it yourself.
- **Render order flicker** → CSS overlays are DOM, not depth-tested; `renderOrder` on WebGL
  objects does not reorder DOM. Manage z-index/visibility explicitly.
- **Two renderers fight over the container** → append the CSS renderer's `domElement` once, after
  the canvas, and keep it non-interactive unless it holds interactive UI.
- **Performance drops with many labels** → each CSS2DObject is a DOM node. Reuse/pool labels and
  hide distant ones.
- **HTML UI invisible in fullscreen** → the overlay is outside the fullscreen element. Request
  fullscreen on the container, not the canvas.
- **Text unreadable over bright scenes** → HUD needs a backing panel, outline or shadow; a
  semi-transparent scrim is the cheapest fix.

## References

- Read `references/overlays-css-and-raycasting.md` for the renderer/API table, layering and
  pointer rules, label performance, raycast details and a responsive test checklist.

## Related skills

- `threejs-scene-setup` — renderer, camera and loop this UI attaches to.
- `threejs-gltf-loading` / `threejs-materials-lighting` — the scene the UI overlays.
- `game-ui-ux` — hierarchy, feedback and readability.
- `accessibility` — keyboard focus, ARIA and reduced motion for the HTML layer.
- `phaser-ui` — the same HUD concerns in a canvas-first engine.
