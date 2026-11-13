---
name: unity-save
description: >
  Save and load player data in Unity 6.3 LTS: Application.persistentDataPath, JsonUtility fields-only
  serialization and its limits, dictionary and polymorphism workarounds, atomic file writes, save
  versioning and migrations, PlayerPrefs for settings, Newtonsoft for complex data, and WebGL
  IndexedDB persistence. Use when a game must persist progress, inventory or options, or when a save
  fails to load after an update or vanishes in a WebGL build.
---

# Unity save and load

Persist game state in Unity 6.3 LTS (6000.3). Targets **Unity 6.3 LTS**.

Writable data goes under `Application.persistentDataPath`. `JsonUtility` covers simple field-based
models; `PlayerPrefs` covers small settings; Newtonsoft handles what `JsonUtility` cannot.

## When to use

- Use when implementing save slots, checkpoints, inventory, unlockables or settings.
- Use when saves fail to load, disappear in a WebGL build, break after a content update, or a crash
  leaves a truncated file.

**When *not* to use:** save-format design and cross-engine slot strategy → `save-systems`; data
architecture with `ScriptableObject` → `unity-scriptableobjects`; settings UI → `game-ui-ux`; cloud
saves or leaderboards → the platform service, not local files.

## Core workflow

1. **Pick the container.** `JsonUtility` for simple `[Serializable]` models; Newtonsoft
   (`com.unity.nuget.newtonsoft-json`) when you need dictionaries, polymorphism or top-level
   arrays; `PlayerPrefs` only for small settings; never `BinaryFormatter`.
2. **Resolve the path.** `Path.Combine(Application.persistentDataPath, "save_slot1.json")`. Never
   write to `Application.dataPath` or a relative path.
3. **Model plain data.** Fields (public or `[SerializeField]`), lists of serializable structs, string
   IDs instead of object references.
4. **Version from day one.** An `int version` field plus a migration function that runs on load.
5. **Write atomically.** Serialize to `.tmp`, keep a `.bak`, then move the temp file over the live
   one. A crash mid-write must not destroy the last good save.
6. **Load defensively.** `File.Exists`, `try/catch` around parse, defaults for missing values,
   fall back to the backup.
7. **Test the failure paths and the target platform** — especially WebGL, where IndexedDB needs an
   explicit flush.

## Patterns

### 1. Serializable model with atomic JSON save

```csharp
using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

[Serializable]
public class SaveData
{
	public const int CurrentVersion = 2;

	public int version = CurrentVersion;
	public int coins;
	public string checkpointId = "start";
	public List<string> inventory = new List<string>();
}

public static class SaveFile
{
	public static string PathFor(string slot) =>
		Path.Combine(Application.persistentDataPath, $"save_{slot}.json");

	public static bool Write(string slot, SaveData data)
	{
		string path = PathFor(slot);
		string tmp = path + ".tmp";
		string bak = path + ".bak";
		data.version = SaveData.CurrentVersion;

		try
		{
			File.WriteAllText(tmp, JsonUtility.ToJson(data, prettyPrint: true));
			if (File.Exists(path))
				File.Copy(path, bak, overwrite: true);
			File.Move(tmp, path, overwrite: true);   // .NET Standard 2.1
			return true;
		}
		catch (Exception e)
		{
			Debug.LogError($"save: write failed for {slot}: {e.Message}");
			return false;
		}
	}

	public static SaveData Read(string slot) => ReadPath(PathFor(slot));

	public static SaveData ReadPath(string path)
	{
		if (!File.Exists(path)) return null;

		try
		{
			return JsonUtility.FromJson<SaveData>(File.ReadAllText(path));
		}
		catch (Exception e)
		{
			Debug.LogError($"save: read failed for {path}: {e.Message}");
			return null;
		}
	}
}
```

`File.Move(tmp, path, overwrite: true)` needs the .NET Standard 2.1 API level (default in Unity 6).
On an older profile, delete the target before moving.

### 2. Load with version migration and backup fallback

```csharp
public static SaveData Load(string slot)
{
	SaveData data = SaveFile.Read(slot);
	if (data == null)
		data = SaveFile.ReadPath(SaveFile.PathFor(slot) + ".bak");

	if (data == null) return new SaveData();

	if (data.version < SaveData.CurrentVersion)
	{
		Migrate(data, data.version);
		data.version = SaveData.CurrentVersion;
		SaveFile.Write(slot, data);   // rewrite once, so the next load is current
	}
	return data;
}

static void Migrate(SaveData data, int from)
{
	if (from < 1) data.coins = Mathf.Max(0, data.coins);
	if (from < 2) data.inventory ??= new List<string>();
}
```

Always write the migrated payload back — otherwise the same migration runs on every load and older
bugs never age out of the player base.

### 3. Dictionaries: serialize entries, rebuild on load

```csharp
[Serializable]
public struct ItemCount
{
	public string id;
	public int count;
}

[Serializable]
public class InventoryData
{
	public List<ItemCount> items = new List<ItemCount>();

	public Dictionary<string, int> ToDictionary()
	{
		var map = new Dictionary<string, int>();
		foreach (var item in items)
			map[item.id] = item.count;
		return map;
	}
}
```

`JsonUtility` cannot serialize `Dictionary<>`. Parallel lists of key/value structs keep the save
readable and avoid a third-party dependency; switch to Newtonsoft only when the model genuinely
needs it.

### 4. Settings with PlayerPrefs

```csharp
PlayerPrefs.SetFloat("audio.music", 0.8f);
PlayerPrefs.SetInt("video.fullscreen", 1);
PlayerPrefs.Save();   // flushes; on WebGL this syncs to IndexedDB
```

`PlayerPrefs` lives in the registry (Windows), plists (macOS/iOS) or IndexedDB (WebGL). It has no
atomic multi-key write and no versioning, so keep game state in files and use it for options only.

### 5. Complex models with Newtonsoft

```csharp
using Newtonsoft.Json;

string json = JsonConvert.SerializeObject(data, Formatting.Indented);
var loaded = JsonConvert.DeserializeObject<SaveData>(json);
```

The `com.unity.nuget.newtonsoft-json` package supports dictionaries, polymorphism with type
handling and top-level arrays. Keep `TypeNameHandling` at `None` for save files — enabling it lets a
tampered file construct arbitrary types.

### 6. WebGL persistence

`Application.persistentDataPath` maps to IndexedDB (`/idbfs/<hash>`) in WebGL builds, and the path
changes if the hosting URL changes. `PlayerPrefs.Save()` triggers a sync; plain `File.WriteAllText`
does not. For file-based saves, flush after writing with a small JavaScript plugin calling
`FS.syncfs(false, callback)`, or keep the critical data in `PlayerPrefs`.

## Pitfalls

- **Fields are missing from the JSON** — `JsonUtility` serializes fields only. Properties are
  ignored; mark private fields `[SerializeField]`.
- **`Dictionary<>` comes back empty** — unsupported by `JsonUtility`. Use entry lists or Newtonsoft.
- **Top-level array or primitive serializes as `{}`** — wrap it in a `[Serializable]` class.
- **A null nested object loads as a default instance** — Unity cannot serialize null for custom
  classes. Add an explicit `hasX` flag or a wrapper.
- **Polymorphic list loses derived data** — `JsonUtility` has no type information. Store a type tag
  and dispatch, or use Newtonsoft without `TypeNameHandling.All`.
- **Saves go to the wrong folder** — relative paths resolve against the project directory in the
  Editor. Always use `Path.Combine(Application.persistentDataPath, ...)`.
- **Crash during save wipes the slot** — writing straight over the live file. Write `.tmp`, copy
  `.bak`, then move.
- **Corrupt file crashes startup** — no `try/catch` around `FromJson`. Treat parse failure as a
  normal case with defaults or backup.
- **Old saves break new code** — no `version` field. Add migrations and keep a fixture save in the
  repo.
- **`BinaryFormatter` used for saves** — obsolete and unsafe; it is not a supported format for
  player-writable files.
- **WebGL saves vanish** — IndexedDB was never flushed. Call `PlayerPrefs.Save()` or a
  `FS.syncfs` plugin after writing, and test in a real build.
- **Slot names come from users** — sanitize them; `../` in a slot name writes outside the save
  directory.
- **Save on quit is lost** — `OnApplicationQuit` is not guaranteed on mobile or when the process is
  killed. Save at checkpoints and on pause.

## References

- Read `references/paths-and-formats.md` for the format comparison, `JsonUtility` rules, platform
  paths, the atomic-write recipe, migration strategy, WebGL notes and a test checklist.

## Related skills

- `save-systems` — format and slot design, versioning strategy, cross-engine concerns.
- `unity-scriptableobjects` — data assets that feed or mirror save state.
- `unity-csharp-scripting` — serialization attributes, lifecycle and file APIs in C#.
- `unity-build-pipeline` — platform builds where save paths and WebGL flushing differ.
- `godot-save` — the equivalent persistence skill for Godot.
- `roblox-datastores` — server-side persistence for Roblox.
