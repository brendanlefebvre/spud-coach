"""Pure logic over the bestiary dataset arrays. No I/O.

Effective per-wave stats use base + increase_each_wave * (wave - 1), matching
the game's (current_wave - 1) scaling. Movement speed is a range because the
game rolls speed +/- speed_randomization per spawn.
"""

from __future__ import annotations

from brotato_coach import query


def effective_stats(enemy: dict, wave: int) -> dict:
    base, slope = enemy["base"], enemy["per_wave"]
    n = wave - 1
    spd, rnd = base.get("speed", 0), base.get("speed_randomization", 0)
    return {
        "health": base.get("health", 0) + slope.get("health", 0) * n,
        "damage": base.get("damage", 0) + slope.get("damage", 0) * n,
        "armor": base.get("armor", 0) + slope.get("armor", 0) * n,
        "speed_range": [spd - rnd, spd + rnd],
    }


def _match(enemies: list[dict], name: str) -> dict | None:
    low = name.lower()
    for e in enemies:
        if low in (e.get("id", "").lower(), e.get("name", "").lower(),
                   e.get("display_name", "").lower()):
            return e
    return None


def get_enemy(ds: dict, name: str, wave: int | None = None) -> dict:
    enemies = ds.get("enemies", [])
    enemy = _match(enemies, name)
    if enemy is None:
        return {"error": "not_found", "did_you_mean": query.suggest(enemies, name)}
    if wave is None:
        return enemy
    return {**enemy, "effective": effective_stats(enemy, wave)}


def list_enemies(ds: dict, *, appears_in=None, ability=None, attack_kind=None) -> list[dict]:
    out = []
    for e in ds.get("enemies", []):
        if appears_in is not None and appears_in not in e.get("appears_in", []):
            continue
        if ability is not None and ability not in e.get("abilities", []):
            continue
        if attack_kind is not None and e.get("attack", {}).get("kind") != attack_kind:
            continue
        out.append({"id": e["id"], "name": e["name"],
                    "attack_kind": e.get("attack", {}).get("kind"),
                    "appears_in": e.get("appears_in", [])})
    return out
