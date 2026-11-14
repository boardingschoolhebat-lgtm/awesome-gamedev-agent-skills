---
name: editor-tooling
description: >
  Build editor and authoring tools: custom inspectors, gizmos/handles, editor windows, undo/redo,
  data validation, asset pipelines and one-click build scripts. Use for level/data authoring
  tools, designer workflows, or editor code that breaks builds.
---

# Editor tooling

Tools are force multipliers: a designer-facing inspector or placement tool saves hours per
content pass. The rules are different from runtime code — editor code must be isolated, undoable
and safe to run on every selection change. This is a **compositional** skill.

## When to use

- Use when building custom inspectors, gizmos, editor windows, validators or build scripts.
- Use when designers hand-edit JSON/CSV and make mistakes, or a workflow is repeated manually.

**When *not* to use:** runtime debug UI → `game-ui-ux`; in-game level editor for players →
gameplay systems; CI pipeline configuration → the project's CI docs.

## Principles

1. **Editor-only code never ships.** Isolate it in an `Editor/` folder (Unity), `addons/`
   (Godot), or `Editor` modules (Unreal); guard with `#if UNITY_EDITOR` / `@tool` carefully.
2. **Every mutation is undoable.** Use the engine's undo system, not direct field writes.
3. **Tools validate, not just edit.** Catch broken data before it reaches the game.
4. **Fast feedback.** Tools should run in under a frame for the common case; defer heavy work.
5. **Idempotent actions.** Running the tool twice produces the same result.

## Engine bindings

### Unity — custom inspector

```csharp
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(SpawnTable))]
public class SpawnTableEditor : Editor {
    public override void OnInspectorGUI() {
        DrawDefaultInspector();
        var table = (SpawnTable)target;
        if (GUILayout.Button("Validate entries")) {
            foreach (var e in table.entries)
                if (e.weight <= 0) Debug.LogWarning($"{e.id}: weight must be > 0", table);
        }
        if (GUILayout.Button("Normalize weights")) {
            Undo.RecordObject(table, "Normalize spawn weights");
            table.Normalize();
            EditorUtility.SetDirty(table);
        }
    }
}
```

- `Undo.RecordObject` before mutation, `EditorUtility.SetDirty` after.
- `targets` + `serializedObject` for multi-object editing.
- `[MenuItem("Tools/...")]` for commands; `EditorWindow.GetWindow<T>()` for dockable tools.
- `OnSceneGUI` + `Handles` for placement; `Handles.DrawWireDisc` for radii.

### Godot — `@tool` + EditorPlugin

```gdscript
@tool
extends Node2D

@export var radius := 100.0:
    set(value):
        radius = value
        queue_redraw()

func _draw() -> void:
    if Engine.is_editor_hint():
        draw_circle(Vector2.ZERO, radius, Color(1, 1, 0, 0.2))
```

```gdscript
@tool
extends EditorPlugin

var dock: Control

func _enter_tree() -> void:
    dock = preload("res://addons/spawner/spawner_dock.tscn").instantiate()
    add_control_to_dock(DOCK_SLOT_RIGHT_UL, dock)

func _exit_tree() -> void:
    remove_control_from_docks(dock)
    dock.queue_free()
```

- `@tool` scripts run in the editor: guard runtime-only logic with `Engine.is_editor_hint()`.
- Undo: `var u := UndoRedo.new()`, `u.create_action("Move")`, `u.add_do_method(...)`,
  `u.add_undo_method(...)`, `u.commit_action()`; free it after use.
- `EditorInterface` (Godot 4.2+) for selection, inspected object, and scene access.
- Never call `get_tree().reload_current_scene()` from a tool script.

### Unreal — details customization / editor utility

- `UCLASS` + `UCLASS(BlueprintType)` data assets; `IDetailCustomization` or
  `UEditorUtilityWidget` for designer tools.
- `FScopedTransaction` for undo; `Modify()` on objects before changes.
- Editor-only modules in `.Build.cs` with `if (Target.bBuildEditor)`.

## Patterns

### 1. Validation pass (before build)

```text
for each asset in content folder:
    check required fields, id uniqueness, references resolve, ranges sane
    log asset path + field + fix hint
fail the build on errors, warn on style
```

- Run from a menu item, a pre-build hook and CI.
- Every message names the asset and how to fix it.
- Keep rules in one place; runtime and editor share the same constraints.

### 2. Placement tool with snapping

```text
on scene GUI event:
    raycast to ground
    snap to grid (or to surface normal)
    draw ghost preview
    on click: Undo.RecordObject + instantiate + set transform
```

- Preview before commit; Esc cancels.
- One undo step per placement, not per property.
- Respect selection/pivot and local vs global space.

### 3. Data authoring instead of hand-edited files

- Prefer a custom asset/inspector over raw JSON for designers.
- Provide import/export when external tools are needed; validate on import.
- Keep stable ids; renaming should not break references (use GUIDs or explicit id fields).

### 4. One-click build script

```text
clean -> validate -> compile -> cook/export -> package -> smoke test -> report
```

- Same script locally and in CI; no manual steps in the middle.
- Fail fast with a non-zero exit code and a readable log.
- Write version + commit hash into the build.

## Pitfalls

- **Editor code in builds** → compile errors or bloat. Isolate and guard.
- **Lost undo** → direct field writes. Always use undo APIs.
- **`@tool` side effects** → scripts that spawn/delete on load corrupt scenes. Guard with
  `Engine.is_editor_hint()` and make tools idempotent.
- **Slow inspectors** → heavy work in `OnInspectorGUI` every frame. Cache, defer, or use a button.
- **Renaming breaks references** → path/index references. Use stable ids.
- **Validation only in the editor** → bad data ships via a different build path. Run the same
  validator in CI.
- **Non-reproducible builds** → timestamps, uncommitted assets. Record version and inputs.
- **Tool assumes one selection** → crashes on multi-select. Handle `targets.Length`.
- **Undo grouping wrong** → one action per click, not per sub-step.

## Composition

- **Data assets:** `godot-resources`, `unity-scriptableobjects`.
- **UI for tools:** `ui-architecture` for editor windows/docks.
- **Validation targets:** `save-systems` (schema versioning), `localization` (key coverage).
- **Builds:** `steam-publish`, `itch-publish` for packaging steps.
- **QA:** `playtest-qa` for smoke tests after build.

## References

- Read `references/editor-tools-and-undo.md` for undo patterns, gizmo math, validation rules and
  an editor-tool test checklist.
