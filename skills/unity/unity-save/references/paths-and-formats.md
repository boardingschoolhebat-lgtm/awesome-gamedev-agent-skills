# Unity saves: paths, formats and failure modes

Reference material for `SKILL.md`. Targets **Unity 6.3 LTS (6000.3)**.

## Format comparison

| Format | API | Strengths | Limits | Use for |
|--------|-----|-----------|--------|---------|
| JsonUtility | `JsonUtility.ToJson` / `FromJson` | Built in, fast, text | Fields only, no dictionaries, no polymorphism, no top-level arrays | Simple save models |
| Newtonsoft JSON | `com.unity.nuget.newtonsoft-json` | Dictionaries, polymorphism, arrays | Extra package; type handling must stay off | Complex models |
| PlayerPrefs | `PlayerPrefs.Set*` / `Save` | Trivial, per-platform store | No atomicity, no versioning, small data | Settings and flags |
| Binary writer | `BinaryWriter` / `BinaryReader` | Compact, full control | Manual versioning, no readability | Large numeric saves |

`BinaryFormatter` is obsolete and unsafe for player-editable files; do not use it.

## Application.persistentDataPath

| Platform | Location |
|----------|----------|
| Windows | `%userprofile%\AppData\LocalLow\<company>\<product>` |
| macOS | `~/Library/Application Support/<company>.<product>` |
| Linux | `~/.config/unity3d/<company>/<product>` |
| Android | app-specific external files directory |
| iOS | app sandbox Documents (visible in file sharing if enabled) |
| WebGL | IndexedDB `/idbfs/<hash>`, hash derived from the hosting URL |

The path includes a GUID derived from the bundle identifier; keep the identifier stable across
updates or players lose their saves.

Always build paths with `Path.Combine(Application.persistentDataPath, fileName)` — relative paths
resolve against the project folder in the Editor.

## JsonUtility rules

Serialized:

- Public fields, and private fields with `[SerializeField]`.
- `[Serializable]` classes and structs, `List<T>` of serializable types.
- Primitives, strings, enums, Unity types such as `Vector3`, `Color`, `AnimationCurve`.

Not serialized:

- Properties (even with getters/setters).
- `Dictionary<>` and other generic collections except `List<T>`.
- Top-level arrays or primitives — wrap them in a class.
- Null for custom classes — you get a default instance.
- Polymorphic fields — the declared type is what comes back.
- Interfaces and abstract types.

`JsonUtility.FromJsonOverwrite(json, target)` patches an existing object and leaves fields absent
from the JSON untouched; useful for settings diffs, not for full saves.

## Atomic write recipe

```text
json = JsonUtility.ToJson(data, true)
File.WriteAllText(path + ".tmp", json)
if File.Exists(path): File.Copy(path, path + ".bak", true)
File.Move(path + ".tmp", path, true)
```

Load order: main file → `.bak` → defaults. Log which one succeeded; silent fallback hides
corruption during development.

## Versioning and migration

```csharp
[Serializable]
public class SaveData
{
    public const int CurrentVersion = 3;
    public int version = CurrentVersion;
    // fields...
}
```

Rules:

- Never reuse a version number.
- Migrate step by step (`v1 → v2 → v3`) instead of a chain of ad-hoc checks.
- Default every new field.
- Rewrite the file once after migration.
- Keep an old save fixture in the project and load it in a test or a debug menu.

## PlayerPrefs notes

- `PlayerPrefs.Save()` writes dirty keys; on WebGL it also triggers the IndexedDB sync.
- Values live in the registry (Windows), plist (macOS/iOS), or IndexedDB (WebGL).
- There is no atomic multi-key commit; a crash can leave some keys updated and others not.
- Keys are global per app, not per save slot. Namespace them (`audio.music`, `slot1.coins`) or avoid
  PlayerPrefs for slot data.

## WebGL specifics

- `persistentDataPath` is IndexedDB-backed and changes with the hosting URL; a moved build looks
  like a fresh install.
- Arbitrary file writes land in memory (MEMFS) until synced. Unity syncs on quit, and browsers do
  not reliably deliver quit events; call `FS.syncfs(false, cb)` from a `.jslib` plugin after
  writing, or use `PlayerPrefs.Save()`.
- Safari's tracking prevention can clear storage for cross-origin iframes (game portals), so warn
  players and consider cloud saves.

## Test checklist

1. Fresh install: defaults, no exceptions in the console.
2. Save → quit → relaunch: state restored on the target platform, not just in the Editor.
3. Corrupt the main file: backup loads, error is logged.
4. Corrupt both: defaults, no crash.
5. Old version fixture: migration runs, file rewritten at the current version.
6. Save twice: no `.tmp` left, `.bak` holds the previous state.
7. Slot name with path characters: rejected or sanitized.
8. WebGL build: reload the page and confirm the save survives.
9. Mobile kill (swipe away) after a checkpoint: progress is on disk.
10. Bundle identifier unchanged across an update: the old save is still found.
