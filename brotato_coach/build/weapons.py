from __future__ import annotations

from brotato_coach import calc
from brotato_coach.tres import parse_tres


def _rd_coefficient(scaling_stats: list) -> float:
    for entry in scaling_stats or []:
        if isinstance(entry, list) and len(entry) == 2 and entry[0] == "stat_ranged_damage":
            return float(entry[1])
    return 0.0


def build_weapon_record(stats_text: str, data_text: str, *, weapon_id: str,
                        name: str, tier: int) -> dict:
    s = parse_tres(stats_text).resource
    d = parse_tres(data_text).resource

    cooldown = float(s.get("cooldown", 0))
    recoil_duration = float(s.get("recoil_duration", 0.0))
    base_damage = float(s.get("damage", 0))
    accuracy = float(s.get("accuracy", 1.0))
    scaling_stats = s.get("scaling_stats", []) or []

    burst = None
    every = s.get("additional_cooldown_every_x_shots", -1)
    mult = s.get("additional_cooldown_multiplier", -1.0)
    if isinstance(every, int) and every > 0 and isinstance(mult, (int, float)) and mult > 0:
        burst = (every, float(mult))

    ct = calc.cycle_time(recoil_duration, cooldown, burst=burst)
    dps0, slope = calc.dps_line(base_damage, _rd_coefficient(scaling_stats), ct, accuracy)

    return {
        "id": weapon_id,
        "name": name,
        "tier": tier,
        "base_damage": base_damage,
        "cooldown": cooldown,
        "accuracy": accuracy,
        "crit_chance": float(s.get("crit_chance", 0.0)),
        "crit_damage": float(s.get("crit_damage", 0.0)),
        "piercing": s.get("piercing", 0),
        "nb_projectiles": s.get("nb_projectiles", 1),
        "scaling_stats": scaling_stats,
        "can_have_negative_knockback": bool(s.get("can_have_negative_knockback", False)),
        "base_knockback": s.get("knockback", 0),
        "cycle_time": ct,
        "dps_at_zero_rd": dps0,
        "dps_slope_per_rd": slope,
        "sets": [],
        "effects": d.get("effects", []) or [],
    }
