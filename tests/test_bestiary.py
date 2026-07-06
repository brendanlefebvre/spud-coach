from brotato_coach import bestiary

_DS = {
    "enemies": [
        {"id": "baby_alien", "name": "Baby Alien", "display_name": "Baby Alien",
         "base": {"health": 3, "speed": 250, "speed_randomization": 50,
                  "damage": 1, "armor": 0, "attack_cd": 30.0,
                  "knockback_resistance": 0.0},
         "per_wave": {"health": 2.0, "damage": 0.6, "armor": 0.0},
         "attack": {"kind": "melee"}, "abilities": [], "appears_in": ["normal"]},
        {"id": "spitter", "name": "Spitter", "display_name": "Spitter",
         "base": {"health": 10, "speed": 200, "speed_randomization": 0,
                  "damage": 2, "armor": 0, "attack_cd": 60.0,
                  "knockback_resistance": 0.0},
         "per_wave": {"health": 4.0, "damage": 0.0, "armor": 0.0},
         "attack": {"kind": "ranged", "projectile_damage": 1,
                    "projectile_dmg_per_wave": 0.75, "number_projectiles": 1},
         "abilities": [], "appears_in": ["normal"]},
    ],
    "zone_1_waves": [],
}


def test_effective_stats_scale_with_wave():
    eff = bestiary.effective_stats(_DS["enemies"][0], wave=20)
    assert eff["health"] == 3 + 2.0 * 19   # 41
    assert eff["damage"] == 1 + 0.6 * 19   # 12.4
    assert eff["speed_range"] == [200, 300]  # 250 +/- 50


def test_get_enemy_without_wave_has_base_and_slopes():
    r = bestiary.get_enemy(_DS, "Baby Alien")
    assert r["base"]["health"] == 3
    assert r["per_wave"]["health"] == 2.0
    assert "effective" not in r


def test_get_enemy_with_wave_adds_effective():
    r = bestiary.get_enemy(_DS, "baby_alien", wave=20)
    assert r["effective"]["health"] == 41


def test_get_enemy_miss_suggests():
    r = bestiary.get_enemy(_DS, "baby alein")
    assert r["error"] == "not_found"
    assert "Baby Alien" in r["did_you_mean"]


def test_list_enemies_filters_by_attack_kind():
    out = bestiary.list_enemies(_DS, attack_kind="ranged")
    assert [e["id"] for e in out] == ["spitter"]
