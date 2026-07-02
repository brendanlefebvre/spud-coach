import math

from brotato_coach import answers

DS = {
    "weapons": [
        {"id": "weapon_minigun", "name": "Minigun", "tier": 4,
         "dps_at_zero_rd": 55.5556, "dps_slope_per_rd": 8.3333, "scaling_stats": []},
        {"id": "weapon_revolver", "name": "Revolver", "tier": 4,
         "dps_at_zero_rd": 57.35, "dps_slope_per_rd": 2.8673, "scaling_stats": []},
        {"id": "weapon_laser", "name": "Laser", "tier": 2,
         "dps_at_zero_rd": 30.0, "dps_slope_per_rd": 1.8, "scaling_stats": []},
        {"id": "weapon_laser", "name": "Laser", "tier": 3,
         "dps_at_zero_rd": 45.0, "dps_slope_per_rd": 2.7, "scaling_stats": []},
        {"id": "weapon_laser", "name": "Laser", "tier": 1,
         "dps_at_zero_rd": 15.0, "dps_slope_per_rd": 0.9, "scaling_stats": []},
    ],
    "characters": [
        {"id": "character_ranger", "name": "Ranger",
         "gain_modifiers": [{"stat": "stat_ranged_damage", "pct": 50},
                            {"stat": "stat_max_hp", "pct": -25}]},
    ],
    "stat_mechanics": {
        "stat_attack_speed": {"special": "attack_speed_universal", "never_dead_weight": True},
    },
}


def test_weapon_dps_at_rd():
    result = answers.weapon_dps(DS, "Minigun", 4, {"ranged_damage": 10})
    assert math.isclose(result["dps"], 55.5556 + 8.3333 * 10, rel_tol=1e-4)


def test_compare_weapons_minigun_beats_revolver_at_rd10():
    result = answers.compare_weapons(
        DS, [("Minigun", 4), ("Revolver", 4)], {"ranged_damage": 10})
    assert result["ranking"][0]["name"] == "Minigun"


def test_compare_merge_paths_crossover_reported():
    # path_a = II+II (two tier-2), path_b = III+I (tier-3 + tier-1)
    result = answers.compare_merge_paths(DS, "Laser", [2, 2], [3, 1])
    # II+II line: (60.0, 3.6); III+I line: (60.0, 3.6) -> effectively tie
    assert "crossover_rd" in result


def test_explain_stat_known():
    result = answers.explain_stat(DS, "stat_attack_speed")
    assert result["never_dead_weight"] is True


def test_stat_display_value_ranger_rd():
    result = answers.stat_display_value(DS, "Ranger", "stat_ranged_damage", 6)
    assert result["displayed_value"] == 9
    assert result["modifier_pct"] == 50


def test_stat_display_value_no_modifier():
    result = answers.stat_display_value(DS, "Ranger", "stat_speed", 10)
    assert result["displayed_value"] == 10
    assert result["modifier_pct"] == 0
