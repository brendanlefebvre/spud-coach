#!/usr/bin/env python3
"""Inspect a Brotato save or run file and print a readable summary.

Usage:
    python tools/brotato_inspect.py [path]

Defaults to the live run file if no path is given. Handles both:
  - run_v3_<id>.json / .bak  (current_run_state: live run, stats, weapons, shop)
  - save_v3_<id>.json        (progress: unlocked weapons/characters/items as hashes)

Stat values are the raw (pre-gain-multiplier) numbers stored in the player
`effects` dict, keyed by djb2 hash of the stat name (see Keys.generate_hash).
"""
import json
import sys
from collections import Counter
from pathlib import Path

DEFAULT_RUN = Path.home() / "AppData/Roaming/Brotato/76561197969729613/run_v3_0.json"


def djb2(s: str) -> int:
    """Godot String.hash() — the hash used for all unlock/stat keys."""
    h = 5381
    for c in s.encode():
        h = (h * 33 + c) & 0xFFFFFFFF
    return h


# Stat panel, in display order.
STATS = [
    "stat_max_hp", "stat_hp_regeneration", "stat_lifesteal", "stat_percent_damage",
    "stat_melee_damage", "stat_ranged_damage", "stat_elemental_damage",
    "stat_attack_speed", "stat_crit_chance", "stat_engineering", "stat_range",
    "stat_armor", "stat_dodge", "stat_speed", "stat_luck", "stat_harvesting",
    "stat_curse", "stat_xp_gain",
]

# Weapon set ids -> hash, so active_sets resolves to names.
SET_IDS = [
    "set_gun", "set_blade", "set_blunt", "set_explosive", "set_elemental",
    "set_heavy", "set_medical", "set_medieval", "set_precise", "set_primitive",
    "set_support", "set_tool", "set_unarmed", "set_ethereal", "set_minigun",
]
SET_BY_HASH = {djb2(s): s.replace("set_", "") for s in SET_IDS}
STAT_BY_HASH = {djb2(s): s for s in STATS}


def summarize_run(state: dict) -> None:
    pd = state["players_data"][0]
    char = pd["current_character"]
    char = char.get("my_id") if isinstance(char, dict) else char
    print(f"== {char}  |  Wave {state['current_wave']}  Danger {state['current_difficulty']}"
          f"  Zone {state['current_zone']}  |  Level {pd['current_level']} ==")
    print(f"   gold {pd['gold']}   hp {pd['current_health']}   retries {state['retries']}"
          f"   endless {state['is_endless_run']}   bosses {state.get('bosses_spawn')}")

    print("\nWEAPONS:")
    for w in pd["weapons"]:
        tier = w.get('tier')
        tier_display = f"T{int(tier) + 1}" if tier is not None else "?"
        print(f"   {w.get('weapon_id'):24} {tier_display}")

    sets = pd.get("active_sets") or {}
    if sets:
        named = {SET_BY_HASH.get(int(k), k): v for k, v in sets.items()}
        print("   sets:", ", ".join(f"{n}x{c}" for n, c in named.items()))

    print("\nSTATS:")
    eff = pd["effects"]
    for s in STATS:
        v = eff.get(str(djb2(s)))
        if v not in (None, 0):
            print(f"   {s[5:]:20} {v}")

    print("\nITEMS:")
    c = Counter(it.get("my_id") for it in pd["items"] if isinstance(it, dict))
    for k, v in c.most_common():
        print(f"   {v}x {k}")


def summarize_save(d: dict) -> None:
    for key in ("weapons_unlocked", "characters_unlocked", "items_unlocked",
                "challenges_completed", "difficulties_unlocked"):
        v = d.get(key)
        if isinstance(v, list):
            print(f"{key}: {len(v)} entries")


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RUN
    data = json.loads(path.read_text())
    if "current_run_state" in data:
        summarize_run(data["current_run_state"])
    else:
        summarize_save(data)


if __name__ == "__main__":
    main()
