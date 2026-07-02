"""Verified stat mechanics, encoded from decompiled code (see docs/stat-mechanics.md).

Only stats whose behavior has been confirmed against the game code are listed.
This table is authoritative for what the coach claims about stat mechanics.
"""

from __future__ import annotations


def _m(cap=None, special=None, safe_below_zero=False, safe_at_zero=False,
       avoid_positive=False, never_dead_weight=False) -> dict:
    return {
        "cap": cap, "special": special, "safe_below_zero": safe_below_zero,
        "safe_at_zero": safe_at_zero, "avoid_positive": avoid_positive,
        "never_dead_weight": never_dead_weight,
    }


STAT_MECHANICS: dict[str, dict] = {
    "stat_max_hp": _m(cap={"cap_key": "hp_cap"}),
    "stat_speed": _m(cap={"cap_key": "speed_cap"}),
    "stat_dodge": _m(cap={"cap_key": "dodge_cap"}),
    "stat_crit_chance": _m(cap={"cap_key": "crit_chance_cap"}),
    "stat_curse": _m(cap={"cap_key": "curse_cap"}, special="curse_sqrt_penalty",
                     safe_below_zero=True, avoid_positive=True),
    "stat_hp_regeneration": _m(special="regen_zero_safe", safe_below_zero=True,
                               safe_at_zero=True),
    "stat_lifesteal": _m(special="lifesteal_negative_drains"),
    "stat_attack_speed": _m(special="attack_speed_universal", never_dead_weight=True),
    "knockback": _m(special="knockback_clamped_by_weapon_flag", safe_below_zero=True,
                    safe_at_zero=True),
}
