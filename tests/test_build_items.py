from brotato_coach.build.items import build_item_record

HANDCUFFS_DATA = """[gd_resource type="Resource" format=2]
[resource]
tier = 2
value = 80
tags = [ "stat_melee_damage", "stat_ranged_damage", "stat_elemental_damage" ]
"""

EFF_MELEE = '[resource]\nkey = "stat_melee_damage"\nvalue = 8\neffect_sign = 3\ntext_key = ""\n'
EFF_RANGED = '[resource]\nkey = "stat_ranged_damage"\nvalue = 8\neffect_sign = 3\ntext_key = ""\n'
EFF_ELEM = '[resource]\nkey = "stat_elemental_damage"\nvalue = 8\neffect_sign = 3\ntext_key = ""\n'
EFF_CAP = '[resource]\nkey = "hp_cap"\nvalue = 0\neffect_sign = 0\ntext_key = "EFFECT_HP_CAP_AT_CURRENT_VALUE"\n'


def test_item_effects_parsed():
    rec = build_item_record(HANDCUFFS_DATA, [EFF_MELEE, EFF_RANGED, EFF_ELEM, EFF_CAP],
                            item_id="item_handcuffs", name="Handcuffs")
    assert rec["value"] == 80
    assert {"key": "stat_ranged_damage", "value": 8, "effect_sign": 3, "text_key": ""} in rec["effects"]
    assert rec["damage_tags"] == ["stat_melee_damage", "stat_ranged_damage", "stat_elemental_damage"]


def test_item_cap_archetype_detected():
    rec = build_item_record(HANDCUFFS_DATA, [EFF_MELEE, EFF_RANGED, EFF_ELEM, EFF_CAP],
                            item_id="item_handcuffs", name="Handcuffs")
    assert "cap_at_current_value" in rec["archetype"]
    assert rec["frozen_stat"] == "stat_max_hp"
