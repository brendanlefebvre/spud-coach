import math

from brotato_coach.build.weapons import build_weapon_record

STATS = """[gd_resource type="Resource" format=2]
[resource]
cooldown = 45
damage = 25
accuracy = 1.0
crit_chance = 0.03
crit_damage = 2.0
recoil_duration = 0.15
piercing = 3
nb_projectiles = 1
scaling_stats = [ [ "stat_ranged_damage", 0.5 ] ]
can_have_negative_knockback = false
knockback = 0
"""

DATA = """[gd_resource type="Resource" format=2]
[resource]
weapon_id = "weapon_shredder"
tier = 3
effects = [  ]
"""


def test_weapon_record_core_fields():
    rec = build_weapon_record(STATS, DATA, weapon_id="weapon_shredder",
                              name="Shredder", tier=4)
    assert rec["id"] == "weapon_shredder"
    assert rec["tier"] == 4
    assert rec["base_damage"] == 25
    assert rec["scaling_stats"] == [["stat_ranged_damage", 0.5]]
    assert rec["can_have_negative_knockback"] is False


def test_weapon_record_precomputed_dps_line():
    rec = build_weapon_record(STATS, DATA, weapon_id="weapon_shredder",
                              name="Shredder", tier=4)
    assert math.isclose(rec["cycle_time"], 1.05, rel_tol=1e-6)
    assert math.isclose(rec["dps_at_zero_rd"], 23.8095, rel_tol=1e-4)
    assert math.isclose(rec["dps_slope_per_rd"], 0.47619, rel_tol=1e-4)
