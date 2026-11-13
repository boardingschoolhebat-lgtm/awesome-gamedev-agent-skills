# Unreal SaveGame: slots, async writes and versioning

Reference material for `SKILL.md`. Targets **UE 5.8**.

## API table

| Call | Header | Notes |
|------|--------|-------|
| `UGameplayStatics::CreateSaveGameObject(TSubclassOf<USaveGame>)` | `Kismet/GameplayStatics.h` | Returns a new `USaveGame` instance |
| `UGameplayStatics::SaveGameToSlot(SaveGameObject, SlotName, UserIndex)` | same | Synchronous, returns `bool` |
| `UGameplayStatics::AsyncSaveGameToSlot(SaveGameObject, SlotName, UserIndex, Delegate)` | same | Serializes on game thread, writes on worker, delegate on game thread |
| `UGameplayStatics::LoadGameFromSlot(SlotName, UserIndex)` | same | Returns `USaveGame*` or null |
| `UGameplayStatics::DoesSaveGameExist(SlotName, UserIndex)` | same | Cheap existence check |
| `UGameplayStatics::DeleteGameInSlot(SlotName, UserIndex)` | same | Removes a slot |
| `UGameplayStatics::SaveDataToSlot(Bytes, SlotName, UserIndex)` | same | Raw `TArray<uint8>` payload |
| `UGameplayStatics::LoadDataFromSlot(OutBytes, SlotName, UserIndex)` | same | Raw payload load |

Async delegate type: `FAsyncSaveGameToSlotDelegate` with
`(const FString& SlotName, const int32 UserIndex, bool bSuccess)`.

## Save class requirements

```cpp
UCLASS()
class MYGAME_API UMySaveGame : public USaveGame
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadWrite, Category = "Save")
    int32 Version = 1;
};
```

- Must derive from `USaveGame`.
- Only `UPROPERTY` members serialize; plain C++ members do not.
- Supported field types follow normal `UPROPERTY` serialization: numbers, bools, `FString`,
  `FName`, enums, structs, `TArray`, and object references that serialize as paths. Keep object
  references to assets only; gameplay actors should be saved as IDs.
- The class name and module path are stored in the file. Renaming the class without a migration
  makes old slots unloadable.

## File locations

- Development platforms: `<Project>/Saved/SaveGames/<SlotName>.sav`.
- Packaged desktop builds: inside the user's saved-games directory for the project.
- Consoles and some platforms: managed by the platform save system; the `.sav` path is not
  meaningful and `UserIndex` selects the profile.
- `UserIndex` is ignored on some platforms; use the real platform user where it matters.

## Sync vs async

| | `SaveGameToSlot` | `AsyncSaveGameToSlot` |
|---|---|---|
| Blocking | Yes, whole write | Serialize on game thread, write on worker |
| Use for | Menus, pause screen, tiny saves | Autosaves, large payloads, active gameplay |
| Failure signal | Return value | Delegate `bSuccess` |
| Concurrency | Simple | Do not load concurrently on platforms that forbid it |

Both go through the platform save system. Certification requirements can include save-size limits,
write-frequency limits and "do not write during certain states" rules; check the target platform's
requirements before shipping an autosave loop.

## Versioning and migration

```cpp
if (Save->Version < UMySaveGame::CurrentVersion)
{
    if (Save->Version < 1) { /* fill new fields with defaults */ }
    if (Save->Version < 2) { /* convert old layout */ }
    Save->Version = UMySaveGame::CurrentVersion;
    // rewrite once
}
```

Rules:

- Never reuse a version number.
- Migrate step by step, not with a chain of ad-hoc checks.
- Default every new field.
- Rewrite the migrated save once.
- Keep an old `.sav` fixture in the project and load it in a test map or automation test.

## Slot naming

- Fixed names per purpose: `Slot_01`, `Slot_02`, `Autosave`, `Settings`.
- Avoid user-provided text; sanitize to `[A-Za-z0-9_-]` if slots are named by players.
- Prefix PIE/test slots (`TEST_`) so development saves do not overwrite real progress on desktop.
- To enumerate slots, keep an index slot or a fixed list; the API has no "list all slots" call.

## Raw byte slots

`SaveDataToSlot` / `LoadDataFromSlot` take `TArray<uint8>`. Use them for:

- Custom binary formats built with `FMemoryWriter` / `FMemoryReader`.
- Compressed or encrypted payloads.
- Data that must interoperate with another system.

You own versioning, validation and corruption handling in that case.

## Test checklist

1. New game → save → restart → load: all fields restored.
2. Save twice: second save overwrites cleanly, no leftover temp files.
3. Rename the save class in a test branch: loading an old slot fails gracefully instead of crashing.
4. Old version fixture: migration fills defaults and rewrites at the current version.
5. Corrupt a `.sav` file: `LoadGameFromSlot` returns null, the game starts fresh and logs.
6. Async save while playing: no hitch, delegate fires with success.
7. Async save then immediate load: no crash on platforms that serialize access.
8. Console/controller user index: saves land in the right profile.
9. Save size near the platform limit: behavior documented and handled.
10. Packaged build: save path differs from PIE; confirm the slot is found after relaunch.
