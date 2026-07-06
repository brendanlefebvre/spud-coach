from __future__ import annotations

from brotato_coach.builders.localization import resolve_text
from brotato_coach.scene import parse_scene_node
from brotato_coach.tres import parse_tres

# Attack-behavior script basename -> (attack kind, ability tag or None).
_BEHAVIOR_KIND = {
    "shooting_attack_behavior": ("ranged", None),
    "charging_attack_behavior": ("charging", "charger"),
    "spawning_attack_behavior": ("ranged", "spawner"),
}


def _num(d: dict, key: str, default: float = 0.0):
    v = d.get(key)
    return v if isinstance(v, (int, float)) else default


def _classify_attack(scene_text: str | None) -> tuple[str, list[str], dict]:
    """Return (kind, abilities, attack_params) from an enemy scene.

    kind/abilities derive from which *_attack_behavior.gd the scene references
    (available in ext_resources without a scene-node parse). Numeric params
    come from the AttackBehavior node. No behavior script -> pure contact melee.
    """
    if not scene_text:
        return "melee", [], {}
    doc = parse_tres(scene_text)
    kind, abilities = "melee", []
    for ext in doc.ext_resources.values():
        path = str(ext.get("path", ""))
        if path.endswith("_attack_behavior.gd"):
            base = path.rsplit("/", 1)[-1][: -len(".gd")]
            if base in _BEHAVIOR_KIND:
                k, ability = _BEHAVIOR_KIND[base]
                kind = k
                if ability:
                    abilities.append(ability)
    node = parse_scene_node(scene_text, "AttackBehavior")
    params: dict = {}
    if kind == "ranged":
        params = {
            "projectile_damage": _num(node, "damage"),
            "projectile_dmg_per_wave": _num(node, "damage_increase_each_wave"),
            "number_projectiles": int(_num(node, "number_projectiles", 1)),
        }
    return kind, abilities, params


def build_enemy_record(stats_text: str, scene_text: str | None, *, enemy_id: str,
                       name: str, tr: dict[str, str] | None = None) -> dict:
    s = parse_tres(stats_text).resource
    kind, abilities, attack_params = _classify_attack(scene_text)
    return {
        "id": enemy_id,
        "name": name,
        "display_name": resolve_text(tr, None, name),
        "base": {
            "health": _num(s, "health"),
            "speed": _num(s, "speed"),
            "speed_randomization": _num(s, "speed_randomization"),
            "damage": _num(s, "damage"),
            "armor": _num(s, "armor"),
            "attack_cd": _num(s, "attack_cd"),
            "knockback_resistance": _num(s, "knockback_resistance"),
        },
        "per_wave": {
            "health": _num(s, "health_increase_each_wave"),
            "damage": _num(s, "damage_increase_each_wave"),
            "armor": _num(s, "armor_increase_each_wave"),
        },
        "attack": {"kind": kind, **attack_params},
        "abilities": abilities,
    }
