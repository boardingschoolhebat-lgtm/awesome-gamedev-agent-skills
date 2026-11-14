# Editor tools and undo

Depth for `editor-tooling`: undo, handles, validation, build hooks and tests.

## Undo patterns

Unity:

```csharp
Undo.RecordObject(target, "Set radius");
radius = newValue;
EditorUtility.SetDirty(target);
```

- Record before the change; one record per user action.
- `Undo.RegisterCreatedObjectUndo(obj, "Create")` for new objects.
- `Undo.DestroyObjectImmediate(obj)` for deletes.

Godot:

```gdscript
var undo := UndoRedo.new()
undo.create_action("Move spawner")
undo.add_do_method(node, "set_position", new_pos)
undo.add_undo_method(node, "set_position", old_pos)
undo.commit_action()
undo.free()
```

- Use methods, not lambdas, for serializable undo steps.
- One action per gesture (drag start → drag end).

## Handles / gizmos

```text
draw radius:  Handles.DrawWireDisc(pos, normal, radius)      // Unity
              draw_arc(center, radius, 0, TAU, 64, color)    // Godot
snap:         pos = round(pos / grid) * grid
normal align: rotation = Quaternion.FromToRotation(Vector3.up, hit.normal)
```

- Preview with a translucent mesh/ghost, commit on click.
- Draw only when the tool/object is selected (cheap).
- Scale handles with `HandleUtility.GetHandleSize` so they stay clickable.

## Validation rules

| Rule | Example | Severity |
|------|---------|----------|
| Required | id non-empty | error |
| Unique | no duplicate ids | error |
| Resolves | prefab/scene path exists | error |
| Range | weight > 0, chance 0–1 | error |
| Convention | naming, folder | warning |
| Coverage | every key localized | warning |

- Report `asset path → field → message → fix`.
- Exit non-zero on errors in CI.
- Store rules with the data schema, not duplicated per tool.

## Build hooks

```text
pre-build:  validate content, bump version, write build info
build:      compile, cook/export, package
post-build: smoke test, checksum, upload artifact
```

- Build info: version, commit, timestamp, platform.
- Smoke test: launch headless or run a minimal scene; fail on error logs.
- Keep artifacts out of version control.

## Test checklist

1. Tool opens/closes without errors; dock restores.
2. Every mutation is one undo step; redo restores exactly.
3. Multi-select does not crash.
4. Tool is idempotent when run twice.
5. `@tool` script does not modify scenes on load.
6. Validation catches a deliberately broken asset.
7. Build fails on validation errors with a readable log.
8. Editor-only code absent from player build.
9. Tool works after domain reload/editor restart.
10. Large content folders validate in reasonable time.
