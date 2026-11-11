"""Verify example prompts still reach the skills the documentation promises.

The router is prose that an agent reads, so a test cannot run it. What *is*
deterministic is the routing contract the router relies on: the trigger words in
``router/references/routing-table.md`` and the composition / "pairs with" edges
recorded in the same rows. This test asserts that a realistic prompt shares every
word of at least one documented trigger with the expected skill, or reaches that
skill one composition hop from a matched genre/workflow/discipline skill.

It fails when a prompt loses its vocabulary, a trigger is reworded away, a skill
is renamed or removed, or a genre stops composing an engine skill it needs.
"""

from __future__ import annotations

import re
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = ROOT / "router" / "references" / "routing-table.md"
SKILLS_ROOT = ROOT / "skills"

TOKEN_RE = re.compile(r"[a-z0-9]+")
SKILL_ROW_RE = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|(.*)\|\s*$")
CODE_SPAN_RE = re.compile(r"`([a-z0-9-]+)`")

# Rows mix prose triggers with file signals. A request never spells out a glob,
# path or extension, so only the prose half can take part in prompt matching.
FILE_SIGNAL_RE = re.compile(
    r"\*|/|\bdep\b|\.(?:toml|json|cs|cpp|gd|tscn|uasset|inputactions|controller|gltf|glb|"
    r"yarn|ink|rpy|md|txt|luau|rbxlx?|script|go|collection|cfg|uproject|sav|shader|hlsl)\b"
)

# Prompts adapted from README "What you can ask" and the router's "Worked
# examples", plus day-to-day phrasings. The expected skills are authored here,
# independently of the table, so the test checks the table rather than restating it.
PROMPT_CASES = (
    ("add a double jump to my Godot player", ("godot-2d-movement", "platformer")),
    ("make an inventory for my Unity RPG", ("unity-scriptableobjects", "rpg", "save-systems")),
    ("build a 2D puzzle game in Go with Ebitengine", ("ebitengine-game", "puzzle")),
    ("add player movement to my Defold game", ("defold-core",)),
    ("rebind gamepad controls in my Defold game", ("defold-core", "input-systems")),
    ("procedural dungeon roguelike in Godot", ("godot-tilemap", "procedural-gen", "roguelike")),
    ("connect a signal from my Godot player to the HUD", ("godot-signals-groups", "game-ui-ux")),
    ("set up tilemap autotiling in Godot", ("godot-tilemap",)),
    ("write a Unity shader for a dissolve effect", ("shader-programming",)),
    ("set up NavMeshAgent patrols in my Unity game", ("unity-navmesh",)),
    ("my Unity game drops to 30 FPS, optimize it", ("performance-optimization",)),
    ("my Godot game stutters when many enemies spawn", ("performance-optimization",)),
    ("make hits feel punchy in my Godot game", ("game-feel", "camera-systems")),
    ("the camera should follow my player smoothly", ("camera-systems",)),
    ("load a gltf model with animation in three.js", ("threejs-gltf-loading",)),
    ("add a wall jump to my platformer", ("platformer",)),
    ("how should I design save slots?", ("save-systems",)),
    ("publish my game on itch with butler", ("itch-publish",)),
    ("rebirths in my Roblox simulator take forever", ("roblox-simulator-economy", "roblox-networking")),
    # Every genre and workflow keeps at least one prompt; the coverage test below
    # fails when a new genre or workflow is added without one.
    ("build a first-person shooter with hitscan weapons", ("fps-shooter",)),
    ("add tower defense waves and tower targeting to my game", ("tower-defense",)),
    ("make a deckbuilder card game in Godot", ("card-game",)),
    ("write a branching story with a choice menu", ("visual-novel",)),
    ("add a crafting system and resource gathering to my survival game", ("survival-crafting",)),
    ("publish my game on Steam with Steamworks", ("steam-publish",)),
    ("I have 48 hours for a game jam, help me scope it", ("game-jam",)),
    ("build a vertical slice prototype fast", ("prototype-fast",)),
    # One prompt per engine skill; the coverage test below fails when a skill is
    # added without either its own prompt or a documented composition path.
    ("type my GDScript variables with @export in Godot", ("godot-gdscript",)),
    ("instance a scene from my node tree in Godot", ("godot-nodes-scenes",)),
    ("my Godot rigidbody keeps sliding", ("godot-physics",)),
    ("build a Control node HUD in Godot", ("godot-ui-control",)),
    ("blend two animations with AnimationPlayer in Godot", ("godot-animation",)),
    ("write a gdshader for a screen-reading outline in Godot", ("godot-shaders",)),
    ("set up Camera3D and WorldEnvironment in Godot", ("godot-3d-essentials",)),
    ("make a custom Resource for item data in Godot", ("godot-resources",)),
    ("lower the audio bus volume in Godot", ("godot-audio",)),
    ("sync my Godot multiplayer players with an RPC", ("godot-multiplayer",)),
    ("export Godot to web from the CLI", ("godot-export",)),
    ("GodotSharp signals in my C# script", ("godot-csharp",)),
    ("run my Godot headless test in CI", ("godot-gdscript-headless-testing",)),
    ("my Unity script keeps restarting coroutines", ("unity-csharp-scripting",)),
    ("set up an action map in the Input System", ("unity-input-system",)),
    ("tune collision layers for my Unity physics", ("unity-physics",)),
    ("my Animator state machine keeps resetting", ("unity-animation",)),
    ("paint a Unity tilemap with a rule tile", ("unity-tilemap-2d",)),
    ("my Unity build fails at IL2CPP", ("unity-build-pipeline",)),
    ("my Blueprint event graph won't compile", ("unreal-blueprints",)),
    ("spawn a Pawn from my Unreal GameMode", ("unreal-cpp-gameplay",)),
    ("add an Input Mapping Context for Enhanced Input", ("unreal-enhanced-input",)),
    ("my Behavior Tree Blackboard key is null in Unreal", ("unreal-behavior-trees",)),
    ("my Niagara particle system looks flat", ("unreal-niagara",)),
    ("package Unreal and cook content for shipping", ("unreal-packaging",)),
    ("create a Phaser scene with a preload function", ("phaser-core",)),
    ("my Arcade Physics collider never fires", ("phaser-arcade-physics",)),
    ("add a Pixi sprite to the stage", ("pixijs-rendering",)),
    ("set up a render loop with THREE.Scene", ("threejs-scene-setup",)),
    ("fix my MeshStandardMaterial lighting and shadows", ("threejs-materials-lighting",)),
    ("write a Bevy ECS system query", ("bevy-ecs",)),
    ("my pygame sprite group won't blit", ("pygame-core",)),
    ("my LÖVE love.draw is blank", ("love2d-core",)),
    ("Luau type annotations in Roblox", ("roblox-luau",)),
    ("save player data with DataStore in Roblox", ("roblox-datastores",)),
    ("build a Roblox HUD with ScreenGui", ("roblox-ui",)),
    ("my Roblox character respawns with a stale Humanoid", ("roblox-characters",)),
    ("my Roblox projectile uses RaycastParams", ("roblox-physics",)),
    ("move my Roblox LocalScript into the right Explorer location in Studio", ("roblox-studio-workflow",)),
    # One prompt per discipline skill, completing catalog-wide coverage.
    ("define an art direction and sprite sheet for my game", ("create-game-assets",)),
    ("add pathfinding for my enemy AI", ("game-ai",)),
    ("build a behavior tree runtime with a blackboard and utility AI", ("ai-behavior-trees-utility-ai",)),
    ("import a Yarn Spinner dialogue system", ("dialogue-systems",)),
    ("add adaptive music and ducking to my audio mixer", ("audio-design",)),
    ("fix jitter and tunneling with a fixed timestep", ("physics-tuning",)),
    ("blockout the level design and pacing", ("level-design",)),
)

# Off-topic requests must not pick up game-dev skills, or every trigger would be
# free to decay into a common English word.
OFF_TOPIC_CASES = (
    ("generate a Dockerfile for my Node service", ("godot-physics", "unity-animation", "threejs-gltf-loading")),
    ("write a SQL migration for the billing table", ("save-systems", "roblox-datastores", "unity-animation")),
    ("translate this changelog paragraph into French", ("dialogue-systems", "game-feel", "platformer")),
)


def _stem(word: str) -> str:
    """Collapse simple English plurals so "rebirths" still matches "rebirth"."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("ses", "xes", "zes", "ches", "shes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def stems(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return {_stem(word) for word in TOKEN_RE.findall(normalized) if len(word) > 1}


def trigger_phrases(cell: str) -> list[str]:
    phrases: list[str] = []
    for piece in re.split(r"[,;]", cell):
        # The table writes alternatives with "/", e.g. "low/dropping FPS".
        for variant in piece.split("/"):
            phrase = re.sub(r"\([^)]*\)", " ", variant)
            phrase = re.sub(r"\s+", " ", phrase.strip('"\u201c\u201d` '))
            if not phrase or FILE_SIGNAL_RE.search(phrase):
                continue
            if not stems(phrase):
                continue
            phrases.append(phrase)
    return phrases


def _rows() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in TABLE_PATH.read_text(encoding="utf-8").splitlines():
        match = SKILL_ROW_RE.match(line)
        if match:
            rows.append((match.group(1), match.group(2)))
    return rows


def triggers_by_skill() -> dict[str, list[str]]:
    triggers: dict[str, list[str]] = {}
    for name, cell in _rows():
        triggers.setdefault(name, []).extend(trigger_phrases(cell))
    return triggers


def compositions(known: set[str]) -> dict[str, set[str]]:
    """Edges to other skills named in the same row (composes, pairs with)."""
    edges: dict[str, set[str]] = {name: set() for name in known}
    for name, cell in _rows():
        if name not in known:
            continue
        edges[name] |= {mentioned for mentioned in CODE_SPAN_RE.findall(cell) if mentioned in known} - {name}
    return edges


def skill_paths() -> dict[str, Path]:
    return {path.parent.name: path for path in sorted(SKILLS_ROOT.glob("*/*/SKILL.md"))}


def routed_skills(
    prompt: str,
    triggers: dict[str, list[str]],
    edges: dict[str, set[str]],
) -> set[str]:
    present = stems(prompt)
    direct = {
        name
        for name, phrases in triggers.items()
        if any(stems(phrase) and stems(phrase) <= present for phrase in phrases)
    }
    routed = set(direct)
    for name in direct:
        routed |= edges.get(name, set())
    return routed


class RoutingTableShapeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.paths = skill_paths()
        self.triggers = triggers_by_skill()

    def test_table_lists_every_skill_exactly_once(self) -> None:
        names = [name for name, _ in _rows()]

        self.assertEqual(len(names), len(set(names)), "a skill appears in more than one table row")
        self.assertEqual(set(names), set(self.paths), "table rows and skills/*/*/SKILL.md disagree")

    def test_every_skill_has_usable_trigger_words(self) -> None:
        for name in sorted(self.paths):
            with self.subTest(skill=name):
                self.assertTrue(self.triggers.get(name), f"{name} has no prompt trigger, only file signals")

    def test_expected_skills_exist(self) -> None:
        for prompt, expected in PROMPT_CASES:
            for name in expected:
                with self.subTest(prompt=prompt, skill=name):
                    self.assertIn(name, self.paths, f"example prompt expects missing skill {name!r}")

    def test_every_skill_has_an_example_prompt(self) -> None:
        covered = {name for _prompt, expected in PROMPT_CASES for name in expected}
        for path in sorted(SKILLS_ROOT.glob("*/*/SKILL.md")):
            category, name = path.parent.parent.name, path.parent.name
            with self.subTest(category=category, skill=name):
                self.assertIn(
                    name,
                    covered,
                    f"{category}/{name} has no example prompt in PROMPT_CASES",
                )


class ExamplePromptRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = skill_paths()
        cls.triggers = triggers_by_skill()
        cls.edges = compositions(set(cls.paths))

    def test_each_example_prompt_reaches_its_documented_skills(self) -> None:
        for prompt, expected in PROMPT_CASES:
            routed = routed_skills(prompt, self.triggers, self.edges)
            for name in expected:
                with self.subTest(prompt=prompt, skill=name):
                    self.assertIn(
                        name,
                        routed,
                        f"{prompt!r} cannot reach {name!r}; documented triggers: "
                        f"{self.triggers.get(name, [])}",
                    )

    def test_off_topic_prompts_do_not_route_to_game_skills(self) -> None:
        for prompt, forbidden in OFF_TOPIC_CASES:
            routed = routed_skills(prompt, self.triggers, self.edges)
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    routed & set(forbidden),
                    set(),
                    f"{prompt!r} should not select {sorted(routed & set(forbidden))}",
                )


if __name__ == "__main__":
    unittest.main()
