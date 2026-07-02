from __future__ import annotations

import difflib

from brotato_coach import calc, query


def _weapon_at(ds: dict, name: str, tier: int) -> dict | None:
    rec = query.get_weapon(ds, name, tier=tier)
    return rec if "id" in rec else None


def weapon_dps(ds: dict, name: str, tier: int, stats: dict) -> dict:
    rec = query.get_weapon(ds, name, tier=tier)
    if "id" not in rec:
        return rec
    rd = float(stats.get("ranged_damage", 0))
    dps = calc.dps_at(rec["dps_at_zero_rd"], rec["dps_slope_per_rd"], rd)
    return {
        "name": rec["name"], "tier": tier, "ranged_damage": rd, "dps": dps,
        "breakdown": {
            "dps_at_zero_rd": rec["dps_at_zero_rd"],
            "dps_slope_per_rd": rec["dps_slope_per_rd"],
        },
    }


def compare_weapons(ds: dict, names_with_tiers: list, stats: dict) -> dict:
    rows = []
    for name, tier in names_with_tiers:
        r = weapon_dps(ds, name, tier, stats)
        if "dps" in r:
            rows.append({"name": r["name"], "tier": tier, "dps": r["dps"]})
    rows.sort(key=lambda x: x["dps"], reverse=True)
    return {"ranking": rows}


def compare_merge_paths(ds: dict, weapon_name: str, path_a: list, path_b: list,
                        rd_range: tuple = (0, 100)) -> dict:
    def path_line(tiers: list) -> tuple[float, float] | None:
        lines = []
        for t in tiers:
            rec = _weapon_at(ds, weapon_name, t)
            if rec is None:
                return None
            lines.append((rec["dps_at_zero_rd"], rec["dps_slope_per_rd"]))
        return calc.sum_lines(lines)

    line_a, line_b = path_line(path_a), path_line(path_b)
    if line_a is None or line_b is None:
        return {"error": "not_found",
                "did_you_mean": difflib.get_close_matches(
                    weapon_name, [w["name"] for w in ds["weapons"]], n=3, cutoff=0.5)}

    result = calc.compare_lines(line_a, line_b, rd_range[0], rd_range[1])
    return {
        "weapon": weapon_name, "path_a": path_a, "path_b": path_b,
        "line_a": line_a, "line_b": line_b, **result,
    }


def explain_stat(ds: dict, stat: str) -> dict:
    mechanics = ds.get("stat_mechanics", {})
    if stat not in mechanics:
        return {"error": "unknown_stat",
                "did_you_mean": difflib.get_close_matches(stat, list(mechanics), n=3, cutoff=0.4)}
    return {"stat": stat, **mechanics[stat]}


def stat_display_value(ds: dict, character: str, stat: str, raw_value: float) -> dict:
    rec = query.get_character(ds, character)
    modifier_pct = 0
    if "id" in rec:
        for mod in rec.get("gain_modifiers", []):
            if mod["stat"] == stat:
                modifier_pct = mod["pct"]
                break
    displayed = raw_value * (1 + modifier_pct / 100)
    displayed = int(displayed) if float(displayed).is_integer() else displayed
    return {"stat": stat, "raw_value": raw_value, "displayed_value": displayed,
            "modifier_pct": modifier_pct}
