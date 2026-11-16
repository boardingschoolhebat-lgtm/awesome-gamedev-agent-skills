# Frame data and feel

Depth for `combat-design`: timing, reactions, tests.

## Timing baseline (60 fps)

| Action | Startup | Active | Recovery | Notes |
|--------|---------|--------|----------|-------|
| Light | 6–10 f | 2–4 f | 8–12 f | chains |
| Heavy | 16–24 f | 4–6 f | 20–30 f | punish tool |
| Dodge | 2–4 f | 6–10 f i-frames | 8–14 f | stamina |
| Parry | 3–6 f | 6–10 f | 16–24 f | whiff punish |
| Heal | 30–60 f | — | — | vulnerable |

- Convert to seconds for your engine: `frames / 60`.
- Keep the same move's timing stable across animation tweaks.

## Hit-stop and hitstun recipe

```text
hit-stop = clamp(damage * 0.15, 2, 8) frames
hitstun  = clamp(damage * 0.5, 6, 20) frames
knockback = direction * (light ? 2 : 5) m/s, decay over 0.2 s
```

- Pause both fighters during hit-stop; keep effects running.
- Add combo scaling: each hit reduces hitstun by ~10 %, floor at 4 f.
- Wall/ground bounce adds a follow-up window; make it optional, not mandatory.

## Enemy archetypes

| Archetype | Tell | Punish | Role |
|-----------|------|--------|------|
| Fodder | short wind-up | any | pacing |
| Shield | guard stance | guard break/back | positioning |
| Charger | paw scrape | sidestep, wall stun | timing |
| Ranged | aim laser | close gap | movement |
| Flyer | hover + dive | anti-air | verticality |
| Elite | unique aura | pattern break | spike |

- One tell per attack; do not stack two colors and a sound for the same move.
- Attack tokens: 1–2 active attackers, others strafe.

## Debug overlay

```text
hitboxes red, hurtboxes green, i-frames blue
current state + frame counter
last input + buffer age
enemy attack token state
```

- Toggle at runtime; capture a clip for review.
- Log damage source and death frame in playtests.

## Checklist

1. Every attack has startup/active/recovery and a punish window.
2. Input buffer is 100–200 ms; no dropped inputs during recovery.
3. Hit-stop and hitstun scale with damage but have caps.
4. Combos cannot loop infinitely; scaling or resource stops them.
5. Dodge i-frames are visible in debug and consistent.
6. Block has chip/guard break; parry has a whiff punish.
7. Enemies telegraph with two channels and attack in turns.
8. Off-screen attacks do not damage the player.
9. Camera keeps both fighters visible; shake does not hide tells.
10. Metrics show damage sources and defense usage.
