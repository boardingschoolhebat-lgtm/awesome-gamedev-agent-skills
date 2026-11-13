---
name: unreal-save
description: >
  Save and load game progress in Unreal Engine 5.8 with USaveGame: slot saves through
  UGameplayStatics SaveGameToSlot and LoadGameFromSlot, async autosaves with
  AsyncSaveGameToSlot, slot existence and deletion, versioned save classes, raw byte saves, and
  platform user-index and size constraints. Use when a game must persist progress, checkpoints or
  unlocks, or when a save slot fails to load after a class rename or content update.
---

# Unreal save and load

Persist game state in Unreal Engine 5.8 with the built-in SaveGame system. Targets **UE 5.8**.

A save is a `USaveGame` object whose `UPROPERTY` fields the engine serializes into a slot file.
`UGameplayStatics` creates, writes, loads and deletes slots.

## When to use

- Use when implementing save slots, checkpoints, autosaves, unlocks or settings persistence.
- Use when a save fails to load after renaming a class, breaks after a content update, or hitches
  the game during autosave.

**When *not* to use:** save-format and slot design across engines → `save-systems`; Blueprint-only
graph work → `unreal-blueprints`; reflection and module basics → `unreal-cpp-gameplay`; online
persistence → the platform or backend service, not local `.sav` files.

## Core workflow

1. **Declare a save class.** `UCLASS()` deriving from `USaveGame`, with `GENERATED_BODY()` and
   `UPROPERTY` fields. Only `UPROPERTY` members are serialized.
2. **Create an instance.** `UGameplayStatics::CreateSaveGameObject(UMySaveGame::StaticClass())`,
   then fill it from the game state.
3. **Choose sync or async.** `SaveGameToSlot` for menus and small saves; `AsyncSaveGameToSlot` for
   autosaves and larger payloads, with a delegate for success/failure.
4. **Load defensively.** `DoesSaveGameExist` → `LoadGameFromSlot` → `Cast<UMySaveGame>`; treat a
   null or failed cast as "no save" and start fresh.
5. **Version and migrate.** An `int32 Version` field plus a migration step keeps old slots working
   after content changes.
6. **Name slots deliberately.** Stable names (`Slot_01`, `Autosave`), per-user index on platforms
   that need it, and no user-typed strings without sanitizing.
7. **Verify in a packaged build.** PIE and packaged builds share `Saved/SaveGames` on development
   platforms; consoles and some platforms behave differently.

## Patterns

### 1. The save class

```cpp
// MySaveGame.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "MySaveGame.generated.h"

UCLASS()
class MYGAME_API UMySaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	static constexpr int32 CurrentVersion = 2;

	UPROPERTY(BlueprintReadWrite, Category = "Save")
	int32 Version = CurrentVersion;

	UPROPERTY(BlueprintReadWrite, Category = "Save")
	int32 Coins = 0;

	UPROPERTY(BlueprintReadWrite, Category = "Save")
	FString CheckpointId = TEXT("start");

	UPROPERTY(BlueprintReadWrite, Category = "Save")
	TArray<FString> Inventory;
};
```

Every field that must survive a restart needs `UPROPERTY`. The generated class name is part of the
serialized data, so renaming or moving `UMySaveGame` breaks existing slots.

### 2. Synchronous save (menus, small saves)

```cpp
#include "Kismet/GameplayStatics.h"

bool UMySaveSubsystem::SaveToSlot(const FString& SlotName) const
{
	UMySaveGame* Save = Cast<UMySaveGame>(
		UGameplayStatics::CreateSaveGameObject(UMySaveGame::StaticClass()));
	if (!Save) return false;

	Save->Version = UMySaveGame::CurrentVersion;
	Save->Coins = Coins;
	Save->CheckpointId = CurrentCheckpoint;
	Save->Inventory = Inventory;

	if (!UGameplayStatics::SaveGameToSlot(Save, SlotName, 0))
	{
		UE_LOG(LogTemp, Error, TEXT("Save failed for slot %s"), *SlotName);
		return false;
	}
	return true;
}
```

`SaveGameToSlot` returns `false` on failure; ignoring the result hides full disks and platform
errors. It blocks while writing, so keep it out of gameplay frames.

### 3. Asynchronous autosave

```cpp
void UMySaveSubsystem::Autosave(const FString& SlotName)
{
	UMySaveGame* Save = Cast<UMySaveGame>(
		UGameplayStatics::CreateSaveGameObject(UMySaveGame::StaticClass()));
	if (!Save) return;

	FAsyncSaveGameToSlotDelegate OnSaved;
	OnSaved.BindUObject(this, &UMySaveSubsystem::HandleSaveComplete);
	UGameplayStatics::AsyncSaveGameToSlot(Save, SlotName, 0, OnSaved);
}

void UMySaveSubsystem::HandleSaveComplete(const FString& SlotName, const int32 UserIndex, bool bSuccess)
{
	UE_LOG(LogTemp, Log, TEXT("Autosave %s: %s"), *SlotName, bSuccess ? TEXT("ok") : TEXT("failed"));
}
```

`AsyncSaveGameToSlot` serializes on the game thread, writes on a worker thread, and calls the
delegate on the game thread. The delegate is copied, so keep its payload trivially copyable, and
do not start a load while an async save is in flight on platforms that forbid concurrent access.

### 4. Load with cast, defaults and migration

```cpp
bool UMySaveSubsystem::LoadFromSlot(const FString& SlotName)
{
	if (!UGameplayStatics::DoesSaveGameExist(SlotName, 0))
		return false;

	USaveGame* Loaded = UGameplayStatics::LoadGameFromSlot(SlotName, 0);
	UMySaveGame* Save = Cast<UMySaveGame>(Loaded);
	if (!Save) return false;   // wrong class or corrupt slot: start fresh

	if (Save->Version < UMySaveGame::CurrentVersion)
	{
		Migrate(*Save);
		Save->Version = UMySaveGame::CurrentVersion;
		UGameplayStatics::SaveGameToSlot(Save, SlotName, 0);   // rewrite once at the new version
	}

	Coins = Save->Coins;
	CurrentCheckpoint = Save->CheckpointId;
	Inventory = Save->Inventory;
	return true;
}
```

A failed `Cast` is a normal outcome (old class name, corrupted file). Return `false` and let the
caller start a new game instead of crashing.

### 5. Slot management

```cpp
UGameplayStatics::DoesSaveGameExist(SlotName, UserIndex);
UGameplayStatics::DeleteGameInSlot(SlotName, UserIndex);
```

Delete before overwriting when the platform's save system requires a free slot, and list slots by
asking for the fixed names the game uses rather than scanning the directory.

### 6. Raw byte slots

```cpp
TArray<uint8> Bytes;
// fill Bytes with your own format
UGameplayStatics::SaveDataToSlot(Bytes, SlotName, UserIndex);

TArray<uint8> Loaded;
UGameplayStatics::LoadDataFromSlot(Loaded, SlotName, UserIndex);
```

Use this when the payload is not a `USaveGame` (custom binary format, compression, encryption
wrapper). The versioning and validation work is then entirely yours.

## Pitfalls

- **Data does not persist** — the field lacks `UPROPERTY`, is not a supported type, or lives on a
  different object than the one passed to `SaveGameToSlot`.
- **Loading returns null after a rename** — the serialized class path changed. Keep the class name
  and module path stable, or write a migration that reads the old class and copies fields.
- **`Cast<UMySaveGame>` fails** — the slot belongs to an older class or is corrupt. Treat it as "no
  save", not as a fatal error.
- **Save fails silently** — `SaveGameToSlot` returns `false` on full disks, permission errors and
  platform limits. Check the result and surface it.
- **Autosave hitch** — synchronous `SaveGameToSlot` on a gameplay frame. Use
  `AsyncSaveGameToSlot` for autosaves.
- **Save and load at the same time** — some platforms do not allow concurrent access. Serialize
  operations through one subsystem and queue requests.
- **Slot name collisions or bad characters** — use fixed, sanitized names; console save systems
  may reject spaces or path separators.
- **Wrong user on consoles** — `UserIndex` identifies the platform user and is ignored on some
  platforms. Read the actual controller/user index instead of hardcoding `0` where it matters.
- **Huge saves** — platform certification limits exist and vary. Keep payloads small; move large
  blobs to raw slots or server storage.
- **Saving object references** — `UObject*` pointers do not survive a restart meaningfully. Save
  stable IDs and resolve them on load.
- **TMap surprises** — container support in the save archive is narrower than in a normal
  `UPROPERTY`. Prefer `TArray` of structs with an explicit key field.
- **PIE saves pollute development** — PIE and packaged builds share `Saved/SaveGames` on desktop;
  delete test slots or use a PIE-specific slot prefix.

## References

- Read `references/slots-and-async.md` for the API table, file locations, async semantics,
  versioning rules, platform constraints and a test checklist.

## Related skills

- `save-systems` — format and slot design, versioning strategy, cross-engine concerns.
- `unreal-cpp-gameplay` — reflection macros, subsystems and module setup.
- `unreal-blueprints` — Blueprint save/load nodes that call the same API.
- `unreal-packaging` — packaged builds where save paths and platform rules apply.
- `godot-save` / `unity-save` — the equivalent persistence skills for other engines.
- `roblox-datastores` — server-side persistence for Roblox.
