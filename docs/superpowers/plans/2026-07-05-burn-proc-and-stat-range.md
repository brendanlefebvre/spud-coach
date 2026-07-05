# Burn proc model + stat_range projectile-speed nuance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Model `effect_burning`'s expected DPS contribution (the top entry of the unmodeled-proc worklist) so the six shipped burn weapons rank honestly, and close the `stat_range` projectile-speed docs gap.

**Architecture:** Add a second `damage_source` type (`"burn_dot"`) to the existing `PROC_MODELS`/proc-aggregation machinery in `brotato_coach/builders/{procs,weapons}.py`, backed by a new pure `calc.burn_dps_line`. Burn's real numbers (`chance`/`damage`/`duration`) live on a separate `burning_data.tres` resource that today's builder can't see — `discover.py` and `build_dataset.py` gain new, additive plumbing to resolve and read that companion file. The model applies only when two preconditions (verified true for every shipped burn weapon) hold; otherwise the effect falls back to `unmodeled_effects` rather than guessing. Separately, `stat_range`'s `explain_stat` entry gets one more evidenced sentence about the `increase_projectile_speed_with_range` flag — no calc change.

**Tech Stack:** Python 3.11+, `uv`, `pytest`. No new dependencies.

## Global Constraints

- TDD is the norm: write the failing test first (`CLAUDE.md`).
- Run tests with `uv run pytest`.
- Evidence citations (file/function/line) must be re-pinned against `recovered/`/`extracted/` at write time, not carried forward — every citation below was independently re-verified during design (see `docs/superpowers/specs/2026-07-05-burn-proc-and-stat-range-design.md`).
- `data/brotato.json` is gitignored and must never be committed; the only way to see the effect of these changes end-to-end is running `build_dataset.py` locally against your own `extracted/`.

---

### Task 1: `calc.burn_dps_line`

**Files:**
- Modify: `brotato_coach/calc.py` (append after `proc_line`, i.e. after line 45)
- Test: `tests/test_calc.py` (append)

**Interfaces:**
- Produces: `calc.burn_dps_line(damage_per_tick: float, tick_interval: float = 0.5) -> tuple[float, float]` — returns `(dps0, slope)` with `slope` always `0.0`. Used by Task 5.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_calc.py`:

```python
def test_burn_dps_line_typical():
    dps0, slope = calc.burn_dps_line(3.0, 0.5)
    assert math.isclose(dps0, 6.0)
    assert slope == 0.0


def test_burn_dps_line_default_tick_interval():
    dps0, slope = calc.burn_dps_line(5.0)
    assert math.isclose(dps0, 10.0)
    assert slope == 0.0


def test_burn_dps_line_zero_damage():
    dps0, slope = calc.burn_dps_line(0.0)
    assert dps0 == 0.0
    assert slope == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_calc.py -k burn_dps_line -v`
Expected: FAIL with `AttributeError: module 'brotato_coach.calc' has no attribute 'burn_dps_line'`

- [ ] **Step 3: Implement `burn_dps_line`**

In `brotato_coach/calc.py`, append after `proc_line` (after the line 45 closing of that function):

```python


def burn_dps_line(damage_per_tick: float, tick_interval: float = 0.5) -> tuple[float, float]:
    """Expected DPS line from a sustained burn (damage-over-time) proc.

    Assumes steady-state: once ignited, the burn is kept continuously
    refreshed by the weapon's own attacks (verified true for every shipped
    burn weapon — see docs/proc-mechanics.md). Burn damage scales off
    stat_elemental_damage, not RD, so slope is always 0 in this dataset's
    RD-parameterized model.
    """
    return (damage_per_tick / tick_interval, 0.0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_calc.py -v`
Expected: PASS (all tests, including the pre-existing ones)

- [ ] **Step 5: Commit**

```bash
git add brotato_coach/calc.py tests/test_calc.py
git commit -m "feat(calc): add burn_dps_line for damage-over-time procs"
```

---

### Task 2: `stat_range` projectile-speed nuance (docs only)

**Files:**
- Modify: `brotato_coach/builders/mechanics.py` (the `stat_range` entry, currently the last entry in `STAT_MECHANICS`)
- Modify: `docs/stat-mechanics.md:13` (the `stat_range` bullet)
- Test: `tests/test_mechanics.py` (append)

**Interfaces:** None — pure documentation, no new functions or schema fields.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_mechanics.py`:

```python
def test_stat_range_projectile_speed_nuance_documented():
    assert "increase_projectile_speed_with_range" in STAT_MECHANICS["stat_range"]["summary"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mechanics.py -k projectile_speed -v`
Expected: FAIL with `AssertionError`

- [ ] **Step 3: Update the `stat_range` entry**

In `brotato_coach/builders/mechanics.py`, replace the `stat_range` entry:

```python
    "stat_range": _m(
        summary="Added flat to weapon max_range. Ranged weapons get the "
                "full stat (weapon_service.gd::init_ranged_stats:42 / "
                "init_ranged_pet_stats:78); melee weapons get only half "
                "(stat/2, weapon_service.gd::init_melee_stats:29 / "
                "init_melee_pet_stats:66) — both are floored at that "
                "weapon's own min_range, so it can shrink an increase's "
                "effect but never push range below the weapon's floor. Not "
                "in utils.gd's cap list — uncapped."),
}
```

with:

```python
    "stat_range": _m(
        summary="Added flat to weapon max_range. Ranged weapons get the "
                "full stat (weapon_service.gd::init_ranged_stats:42 / "
                "init_ranged_pet_stats:78); melee weapons get only half "
                "(stat/2, weapon_service.gd::init_melee_stats:29 / "
                "init_melee_pet_stats:66) — both are floored at that "
                "weapon's own min_range, so it can shrink an increase's "
                "effect but never push range below the weapon's floor. Not "
                "in utils.gd's cap list — uncapped. Weapons flagged "
                "increase_projectile_speed_with_range (only Flamethrower "
                "T2-T4 ship with this) also scale projectile_speed = "
                "clamp(projectile_speed + projectile_speed/300 * "
                "stat_range, 50, 6000) "
                "(weapon_service.gd::_set_common_ranged_stats:115)."),
}
```

- [ ] **Step 4: Update `docs/stat-mechanics.md`**

In `docs/stat-mechanics.md`, replace line 13:

```
- **stat_range** adds flat range to weapons: ranged weapons get the full stat via `weapon_service.gd::init_ranged_stats` (42) and `init_ranged_pet_stats` (78) — `max_range = max(min_range, max_range + stat_range)`; melee weapons get only half via `weapon_service.gd::init_melee_stats` (29) and `init_melee_pet_stats` (66) — `max_range = max(min_range, max_range + stat_range/2)`. Both are floored at that weapon's own `min_range`, so it can shrink effective range increases but never below the weapon's floor. Not in utils.gd's cap list — uncapped.
```

with:

```
- **stat_range** adds flat range to weapons: ranged weapons get the full stat via `weapon_service.gd::init_ranged_stats` (42) and `init_ranged_pet_stats` (78) — `max_range = max(min_range, max_range + stat_range)`; melee weapons get only half via `weapon_service.gd::init_melee_stats` (29) and `init_melee_pet_stats` (66) — `max_range = max(min_range, max_range + stat_range/2)`. Both are floored at that weapon's own `min_range`, so it can shrink effective range increases but never below the weapon's floor. Not in utils.gd's cap list — uncapped. Weapons flagged `increase_projectile_speed_with_range` (only Flamethrower T2–T4 ship with this) also get a projectile-speed boost from `stat_range`: `projectile_speed = clamp(projectile_speed + projectile_speed/300 * stat_range, 50, 6000)` (`weapon_service.gd::_set_common_ranged_stats:115`).
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_mechanics.py -v`
Expected: PASS (all tests)

- [ ] **Step 6: Commit**

```bash
git add brotato_coach/builders/mechanics.py docs/stat-mechanics.md tests/test_mechanics.py
git commit -m "docs(mechanics): add stat_range projectile-speed nuance"
```

---

### Task 3: `discover.py` — resolve the `burning_data` companion path

**Files:**
- Modify: `brotato_coach/builders/discover.py` (add a function after `_resolve_weapon_refs`, ~line 46; modify `find_weapon_dirs`, ~lines 63-72)
- Test: `tests/test_build_discover.py` (append)

**Interfaces:**
- Produces: `discover._resolve_effect_burning_data(extracted_root: str, effect_paths: list[str]) -> dict[str, str]` — maps an effect path to its resolved `burning_data` companion path, omitting effects without one. Used internally by `find_weapon_dirs` and directly by Task 6.
- `find_weapon_dirs` entries gain a new key: `"effect_burning_data_paths": dict[str, str]` (same shape, aligned to that entry's own `effect_paths`). Existing keys (`effect_paths`, `classes`, etc.) are unchanged — this is additive.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_build_discover.py`:

```python
def test_resolve_effect_burning_data_finds_companion_resource(tmp_path):
    from brotato_coach.builders import discover
    wdir = tmp_path / "weapons" / "melee" / "torch" / "1"
    wdir.mkdir(parents=True)
    effect_path = wdir / "torch_effect_1.tres"
    effect_path.write_text(
        '[gd_resource type="Resource" format=2]\n'
        '[ext_resource path="res://effects/weapons/burning_effect.gd" type="Script" id=1]\n'
        '[ext_resource path="res://weapons/melee/torch/1/torch_burning_data.tres" type="Resource" id=2]\n'
        '[resource]\nscript = ExtResource( 1 )\nkey = "effect_burning"\n'
        'burning_data = ExtResource( 2 )\n', encoding="utf-8")
    (wdir / "torch_burning_data.tres").write_text(
        '[gd_resource type="Resource" format=2]\n[resource]\n'
        'chance = 1.0\ndamage = 3\nduration = 3\n', encoding="utf-8")

    result = discover._resolve_effect_burning_data(str(tmp_path), [str(effect_path)])
    assert list(result.keys()) == [str(effect_path)]
    assert result[str(effect_path)].endswith("torch_burning_data.tres")


def test_resolve_effect_burning_data_skips_effects_without_one(tmp_path):
    from brotato_coach.builders import discover
    wdir = tmp_path / "weapons" / "ranged" / "shredder" / "1"
    wdir.mkdir(parents=True)
    effect_path = wdir / "shredder_effect.tres"
    effect_path.write_text(
        '[gd_resource type="Resource" format=2]\n[resource]\n'
        'key = "effect_explode_custom"\nchance = 0.5\n', encoding="utf-8")

    result = discover._resolve_effect_burning_data(str(tmp_path), [str(effect_path)])
    assert result == {}


def test_find_weapon_dirs_includes_burning_data_paths(tmp_path):
    from brotato_coach.builders.discover import find_weapon_dirs
    wdir = tmp_path / "weapons" / "melee" / "torch" / "1"
    wdir.mkdir(parents=True)
    (wdir / "torch_stats.tres").write_text("stats")
    effect_path = wdir / "torch_effect_1.tres"
    effect_path.write_text(
        '[gd_resource type="Resource" format=2]\n'
        '[ext_resource path="res://effects/weapons/burning_effect.gd" type="Script" id=1]\n'
        '[ext_resource path="res://weapons/melee/torch/1/torch_burning_data.tres" type="Resource" id=2]\n'
        '[resource]\nscript = ExtResource( 1 )\nkey = "effect_burning"\n'
        'burning_data = ExtResource( 2 )\n', encoding="utf-8")
    (wdir / "torch_burning_data.tres").write_text(
        '[gd_resource type="Resource" format=2]\n[resource]\n'
        'chance = 1.0\ndamage = 3\nduration = 3\n', encoding="utf-8")
    (wdir / "torch_data.tres").write_text(
        '[gd_resource type="Resource" format=2]\n'
        '[ext_resource path="res://weapons/melee/torch/1/torch_effect_1.tres" type="Resource" id=1]\n'
        '[resource]\neffects = [ ExtResource( 1 ) ]\n', encoding="utf-8")

    found = find_weapon_dirs(str(tmp_path))
    assert len(found) == 1
    paths = found[0]["effect_burning_data_paths"]
    assert len(paths) == 1
    assert list(paths.values())[0].endswith("torch_burning_data.tres")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_build_discover.py -k burning_data -v`
Expected: FAIL with `AttributeError: module 'brotato_coach.builders.discover' has no attribute '_resolve_effect_burning_data'` (first two), then `KeyError: 'effect_burning_data_paths'` (third, once the first two are fixed)

- [ ] **Step 3: Implement `_resolve_effect_burning_data` and wire it into `find_weapon_dirs`**

In `brotato_coach/builders/discover.py`, add this function after `_resolve_weapon_refs` (after its closing `return effect_paths, classes` at line 45):

```python


def _resolve_effect_burning_data(extracted_root: str, effect_paths: list[str]) -> dict[str, str]:
    """Resolve each effect's `burning_data` ext_resource reference, if any.

    Most weapon effects (e.g. exploding) keep their gameplay numbers inline
    on the effect resource itself; burning effects instead point to a
    separate BurningData resource. Returns effect path -> burning_data path,
    omitting effects that don't reference one.
    """
    result: dict[str, str] = {}
    for effect_path in effect_paths:
        with open(effect_path, encoding="utf-8") as fh:
            doc = parse_tres(fh.read())
        ref = doc.resource.get("burning_data")
        if isinstance(ref, dict) and "__ext__" in ref:
            ext = doc.ext_resources.get(ref["__ext__"]) or {}
            path = _res_url_to_path(extracted_root, ext.get("path"))
            if path and os.path.isfile(path):
                result[effect_path] = path
    return result
```

Then in `find_weapon_dirs`, replace:

```python
            effect_paths, classes = _resolve_weapon_refs(extracted_root, data[0])
            results.append({
                "weapon_id": f"weapon_{weapon_folder}",
                "name": weapon_folder.replace("_", " ").title(),
                "tier": int(tier_name),
                "stats_path": stats[0],
                "data_path": data[0],
                "effect_paths": effect_paths,
                "classes": classes,
            })
```

with:

```python
            effect_paths, classes = _resolve_weapon_refs(extracted_root, data[0])
            burning_data_paths = _resolve_effect_burning_data(extracted_root, effect_paths)
            results.append({
                "weapon_id": f"weapon_{weapon_folder}",
                "name": weapon_folder.replace("_", " ").title(),
                "tier": int(tier_name),
                "stats_path": stats[0],
                "data_path": data[0],
                "effect_paths": effect_paths,
                "effect_burning_data_paths": burning_data_paths,
                "classes": classes,
            })
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_build_discover.py -v`
Expected: PASS (all tests, including pre-existing ones)

- [ ] **Step 5: Commit**

```bash
git add brotato_coach/builders/discover.py tests/test_build_discover.py
git commit -m "feat(discover): resolve burning_data companion resource per effect"
```

---

### Task 4: `_weapon_effect_record` — merge the burning_data companion

**Files:**
- Modify: `brotato_coach/builders/weapons.py` (the `_weapon_effect_record` function, lines 16-25, and its one call site, line 52)
- Test: `tests/test_build_weapons.py` (append)

**Interfaces:**
- Consumes: nothing new.
- Produces: `_weapon_effect_record(text: str, extra_text: str | None = None) -> dict` — when `extra_text` is given, the returned dict gains a `"burning_data"` key nesting that companion resource's own scalar fields. `build_weapon_record` gains a new optional parameter `effect_extra_texts: list[str | None] | None = None` (positional, after `effect_texts`, before the `*`), index-aligned with `effect_texts`. Used by Task 5 (reads `eff["burning_data"]`) and Task 6 (build_dataset.py passes this parameter).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_build_weapons.py`:

```python
BURNING_EFFECT = ('[gd_resource type="Resource" format=2]\n'
                  '[ext_resource path="res://effects/weapons/burning_effect.gd" type="Script" id=1]\n'
                  '[resource]\nscript = ExtResource( 1 )\n'
                  'key = "effect_burning"\nvalue = 0\n')

BURNING_DATA = ('[gd_resource type="Resource" format=2]\n[resource]\n'
                'chance = 1.0\ndamage = 3\nduration = 3\nspread = 0\n'
                'scaling_stats = [ [ "stat_elemental_damage", 1.0 ] ]\n'
                'is_global_burn = false\n')


def test_weapon_record_merges_burning_data_companion():
    rec = build_weapon_record(STATS, DATA, [BURNING_EFFECT], [BURNING_DATA],
                              weapon_id="w", name="W", tier=1)
    e = rec["effects"][0]
    assert e["key"] == "effect_burning"
    assert e["burning_data"] == {
        "chance": 1.0, "damage": 3, "duration": 3, "spread": 0,
        "scaling_stats": [["stat_elemental_damage", 1.0]],
        "is_global_burn": False,
    }


def test_weapon_record_effect_without_companion_has_no_burning_data_key():
    rec = build_weapon_record(STATS, DATA, [BURNING_EFFECT],
                              weapon_id="w", name="W", tier=1)
    assert "burning_data" not in rec["effects"][0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_build_weapons.py -k burning_data_companion -v`
Expected: FAIL with `TypeError: build_weapon_record() takes from 2 to 3 positional arguments but 4 were given`

- [ ] **Step 3: Implement the merge**

In `brotato_coach/builders/weapons.py`, replace `_weapon_effect_record`:

```python
def _weapon_effect_record(text: str) -> dict:
    """A weapon's on-hit effect as plain scalar fields.

    Drops nested resource references (script, explosion_scene, …) and keeps the
    gameplay scalars — e.g. the Shredder's `key="effect_explode_custom"` with
    `chance=0.5`.
    """
    r = parse_tres(text).resource
    return {k: v for k, v in r.items()
            if not (isinstance(v, dict) and ("__ext__" in v or "__sub__" in v))}
```

with:

```python
def _weapon_effect_record(text: str, extra_text: str | None = None) -> dict:
    """A weapon's on-hit effect as plain scalar fields.

    Drops nested resource references (script, explosion_scene, …) and keeps the
    gameplay scalars — e.g. the Shredder's `key="effect_explode_custom"` with
    `chance=0.5`. Some effects (e.g. burning) keep their real numbers on a
    separate companion resource instead of inline; when `extra_text` is given
    (that companion file's raw text), its scalar fields are nested under
    `burning_data` rather than flattened, since both files carry unrelated
    same-named boilerplate fields (e.g. `value`).
    """
    r = parse_tres(text).resource
    record = {k: v for k, v in r.items()
              if not (isinstance(v, dict) and ("__ext__" in v or "__sub__" in v))}
    if extra_text is not None:
        extra = parse_tres(extra_text).resource
        record["burning_data"] = {k: v for k, v in extra.items()
                                  if not (isinstance(v, dict) and ("__ext__" in v or "__sub__" in v))}
    return record
```

Then update `build_weapon_record`'s signature — replace:

```python
def build_weapon_record(stats_text: str, data_text: str,
                        effect_texts: list[str] | None = None, *,
                        weapon_id: str, name: str, tier: int,
                        classes: list[str] | None = None,
                        proc_models: dict | None = None,
                        tr: dict[str, str] | None = None) -> dict:
```

with:

```python
def build_weapon_record(stats_text: str, data_text: str,
                        effect_texts: list[str] | None = None,
                        effect_extra_texts: list[str | None] | None = None, *,
                        weapon_id: str, name: str, tier: int,
                        classes: list[str] | None = None,
                        proc_models: dict | None = None,
                        tr: dict[str, str] | None = None) -> dict:
```

And replace the effects-building line:

```python
    effects = [_weapon_effect_record(t) for t in (effect_texts or [])]
```

with:

```python
    extras = effect_extra_texts or [None] * len(effect_texts or [])
    effects = [_weapon_effect_record(t, e) for t, e in zip(effect_texts or [], extras)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_build_weapons.py -v`
Expected: PASS (all tests, including pre-existing ones)

- [ ] **Step 5: Commit**

```bash
git add brotato_coach/builders/weapons.py tests/test_build_weapons.py
git commit -m "feat(weapons): merge burning_data companion into effect records"
```

---

### Task 5: `procs.py` burn model + `weapons.py` dispatch

**Files:**
- Modify: `brotato_coach/builders/procs.py` (append model + update `PROC_MODELS`)
- Modify: `brotato_coach/builders/weapons.py` (the proc-aggregation loop, currently lines 56-65)
- Test: `tests/test_build_weapons.py` (append)

**Interfaces:**
- Consumes: `calc.burn_dps_line` (Task 1), `eff["burning_data"]` (Task 4).
- Produces: `PROC_MODELS["effect_burning"] = {"damage_source": "burn_dot", "tick_interval": 0.5}`. No new dataset fields — folds into the existing `proc_dps_at_zero_rd`/`proc_dps_slope_per_rd`/`unmodeled_effects`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_build_weapons.py`:

```python
def _burning_data(chance=1.0, damage=3, duration=3):
    return ('[gd_resource type="Resource" format=2]\n[resource]\n'
            f'chance = {chance}\ndamage = {damage}\nduration = {duration}\n'
            'spread = 0\nscaling_stats = [ [ "stat_elemental_damage", 1.0 ] ]\n'
            'is_global_burn = false\n')


def test_weapon_record_burn_dot_contributes_when_preconditions_hold():
    # Torch T1: cooldown 31 frames, recoil 0.1 -> cycle_time ~0.717s;
    # duration 3 ticks * 0.5s tick_interval = 1.5s window comfortably
    # sustains continuous uptime.
    stats = ('[gd_resource type="Resource" format=2]\n[resource]\n'
             'cooldown = 31\ndamage = 5\naccuracy = 1.0\nrecoil_duration = 0.1\n'
             'scaling_stats = [ [ "stat_melee_damage", 1.0 ] ]\n')
    rec = build_weapon_record(stats, DATA, [BURNING_EFFECT], [_burning_data()],
                              weapon_id="w", name="W", tier=1)
    assert math.isclose(rec["proc_dps_at_zero_rd"], 6.0)  # 3 damage / 0.5s
    assert rec["proc_dps_slope_per_rd"] == 0.0
    assert rec["unmodeled_effects"] == []


def test_weapon_record_burn_dot_falls_back_when_cycle_time_exceeds_window():
    # Hypothetical slow weapon: cooldown 600 frames (10s) vs. a 1.5s window.
    stats = ('[gd_resource type="Resource" format=2]\n[resource]\n'
             'cooldown = 600\ndamage = 5\naccuracy = 1.0\nrecoil_duration = 0.1\n'
             'scaling_stats = [ [ "stat_melee_damage", 1.0 ] ]\n')
    rec = build_weapon_record(stats, DATA, [BURNING_EFFECT], [_burning_data()],
                              weapon_id="w", name="W", tier=1)
    assert rec["proc_dps_at_zero_rd"] == 0.0
    assert rec["unmodeled_effects"] == ["effect_burning"]


def test_weapon_record_burn_dot_falls_back_when_chance_below_one():
    rec = build_weapon_record(STATS, DATA, [BURNING_EFFECT],
                              [_burning_data(chance=0.5)],
                              weapon_id="w", name="W", tier=1)
    assert rec["proc_dps_at_zero_rd"] == 0.0
    assert rec["unmodeled_effects"] == ["effect_burning"]


def test_weapon_record_burn_dot_falls_back_without_burning_data():
    rec = build_weapon_record(STATS, DATA, [BURNING_EFFECT],
                              weapon_id="w", name="W", tier=1)
    assert rec["proc_dps_at_zero_rd"] == 0.0
    assert rec["unmodeled_effects"] == ["effect_burning"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_build_weapons.py -k burn_dot -v`
Expected: FAIL — the "contributes" test fails its `proc_dps_at_zero_rd` assertion (got `0.0`, expected `6.0`); the fallback tests currently pass by accident (already zero) but will be re-verified once the model exists, so run them again after Step 3.

- [ ] **Step 3: Add the model and dispatch**

In `brotato_coach/builders/procs.py`, replace:

```python
PROC_MODELS: dict[str, dict] = {
    "effect_explode_custom": _EXPLODE_MODEL,
    "effect_explode": _EXPLODE_MODEL,
    "effect_explode_melee": _EXPLODE_MODEL,
}
```

with:

```python
# Burning effect: a chance-per-hit damage-over-time proc, independent of the
# weapon's own damage line (it scales off stat_elemental_damage, not RD).
# Evidence: docs/proc-mechanics.md (unit.tscn:52 BurningTimer wait_time=0.5;
# unit.gd apply_burning/burn-tick handler). Modeled only when the weapon's
# own cycle_time fits inside the burn's duration window at chance==1.0 —
# verified true for every shipped burn weapon (Torch, Fireball, Wand,
# Flamethrower, Particle Accelerator, Flaming Knuckles). builders/weapons.py
# enforces this precondition and falls back to unmodeled_effects otherwise,
# rather than guess at an unverified duty-cycle model for chance < 1.0 or a
# slower weapon — no shipped weapon exercises either case.
_BURN_MODEL = {
    "damage_source": "burn_dot",
    "tick_interval": 0.5,
}

PROC_MODELS: dict[str, dict] = {
    "effect_explode_custom": _EXPLODE_MODEL,
    "effect_explode": _EXPLODE_MODEL,
    "effect_explode_melee": _EXPLODE_MODEL,
    "effect_burning": _BURN_MODEL,
}
```

In `brotato_coach/builders/weapons.py`, this file now has Task 4's edit applied, so the proc loop currently reads:

```python
    extras = effect_extra_texts or [None] * len(effect_texts or [])
    effects = [_weapon_effect_record(t, e) for t, e in zip(effect_texts or [], extras)]
    models = PROC_MODELS if proc_models is None else proc_models
    proc0 = proc_slope = 0.0
    unmodeled: list[str] = []
    for eff in effects:
        model = models.get(str(eff.get("key", "")))
        if model is not None and model["damage_source"] == "weapon_damage":
            p0, ps = calc.proc_line(dps0, slope, float(eff.get("chance", 1.0)),
                                    model["default_enemies_hit"],
                                    model["damage_multiplier"])
            proc0 += p0
            proc_slope += ps
        elif eff.get("key"):
            unmodeled.append(str(eff["key"]))
```

Replace just the `for eff in effects:` loop body (leave the two lines above it — `extras = ...` and `effects = [...]` — untouched) with:

```python
    for eff in effects:
        model = models.get(str(eff.get("key", "")))
        source = model["damage_source"] if model is not None else None
        if source == "weapon_damage":
            p0, ps = calc.proc_line(dps0, slope, float(eff.get("chance", 1.0)),
                                    model["default_enemies_hit"],
                                    model["damage_multiplier"])
            proc0 += p0
            proc_slope += ps
        elif source == "burn_dot":
            bd = eff.get("burning_data") or {}
            chance = float(bd.get("chance", 0.0))
            damage = float(bd.get("damage", 0))
            duration = float(bd.get("duration", 0))
            window = duration * model["tick_interval"]
            if chance == 1.0 and window > 0 and ct <= window:
                p0, ps = calc.burn_dps_line(damage, model["tick_interval"])
                proc0 += p0
                proc_slope += ps
            elif eff.get("key"):
                unmodeled.append(str(eff["key"]))
        elif eff.get("key"):
            unmodeled.append(str(eff["key"]))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_build_weapons.py tests/test_calc.py -v`
Expected: PASS (all tests, including pre-existing ones — in particular `test_default_proc_models_cover_explode_keys` and `test_weapon_record_unmodeled_effect_contributes_zero_and_is_listed` must still pass unchanged)

- [ ] **Step 5: Commit**

```bash
git add brotato_coach/builders/procs.py brotato_coach/builders/weapons.py tests/test_build_weapons.py
git commit -m "feat(procs): model effect_burning as a gated steady-state DoT"
```

---

### Task 6: Wire `build_dataset.py` + shipped-dataset verification

**Files:**
- Modify: `build_dataset.py:46-53`
- Modify: `tests/test_shipped_dataset.py` (append an assertion)

**Interfaces:** None new — glue code only.

- [ ] **Step 1: Update the weapon-building loop**

In `build_dataset.py`, replace:

```python
    weapons = []
    for entry in discover.find_weapon_dirs(args.extracted):
        weapons.append(build_weapon_record(
            _read(entry["stats_path"]), _read(entry["data_path"]),
            [_read(p) for p in entry.get("effect_paths", [])],
            weapon_id=entry["weapon_id"], name=entry["name"], tier=entry["tier"],
            classes=entry.get("classes", []), tr=tr,
        ))
```

with:

```python
    weapons = []
    for entry in discover.find_weapon_dirs(args.extracted):
        effect_paths = entry.get("effect_paths", [])
        burning_data_paths = entry.get("effect_burning_data_paths", {})
        effect_extra_texts = [
            _read(burning_data_paths[p]) if p in burning_data_paths else None
            for p in effect_paths
        ]
        weapons.append(build_weapon_record(
            _read(entry["stats_path"]), _read(entry["data_path"]),
            [_read(p) for p in effect_paths], effect_extra_texts,
            weapon_id=entry["weapon_id"], name=entry["name"], tier=entry["tier"],
            classes=entry.get("classes", []), tr=tr,
        ))
```

- [ ] **Step 2: Add a shipped-dataset assertion for a burn weapon**

In `tests/test_shipped_dataset.py`, after the existing proc-weapon assertion block:

```python
    # proc weapons carry a nonzero expected proc line
    sh = query.get_weapon(ds, "Shredder", tier=1)
    assert sh["proc_dps_at_zero_rd"] > 0
```

add:

```python

    # burn weapons carry a nonzero expected DoT proc line
    torch = query.get_weapon(ds, "Torch", tier=1)
    assert torch["proc_dps_at_zero_rd"] > 0
    assert torch["unmodeled_effects"] == []
```

- [ ] **Step 3: Run the full test suite**

Run: `uv run pytest -v`
Expected: PASS. `tests/test_shipped_dataset.py` will show as SKIPPED unless `data/brotato.json` already exists locally.

- [ ] **Step 4: Build the dataset locally and confirm the new assertion passes**

Run (adjust `--game-version`/`--generated-at` to match your usual local build):

```bash
uv run python build_dataset.py --game-version 1.1.15.4 --generated-at 2026-07-05T00:00:00Z
uv run pytest tests/test_shipped_dataset.py -v
```

Expected: PASS (not skipped this time), confirming Torch T1 now shows a nonzero `proc_dps_at_zero_rd` and empty `unmodeled_effects`. `data/brotato.json` is gitignored — do not commit it.

- [ ] **Step 5: Commit**

```bash
git add build_dataset.py tests/test_shipped_dataset.py
git commit -m "feat(build): resolve burning_data companions when building weapon records"
```

---

### Task 7: `docs/proc-mechanics.md` — document the burning effect

**Files:**
- Modify: `docs/proc-mechanics.md`

**Interfaces:** None — documentation only, mirroring the existing "Exploding effect" section's evidence format.

- [ ] **Step 1: Add the "Burning effect" section**

In `docs/proc-mechanics.md`, insert a new section after the "Exploding effect" section ends (after the line ending `...no separate flat damage value is defined on the scene itself.`, i.e. after the current line 82) and before `## Unmodeled effect-key worklist`:

```markdown

## Burning effect (`BurningEffect`, `recovered/effects/weapons/burning_effect.gd`)

Unlike the exploding effect, `effect_burning`'s gameplay numbers
(`chance`/`damage`/`duration`/`spread`/`scaling_stats`) are **not** on the
weapon-effect `.tres` itself — they live on a separate `BurningData`
resource, referenced only as `burning_data = ExtResource( N )`. The
build pipeline resolves and merges this companion file (`discover.py`'s
`_resolve_effect_burning_data`, `weapons.py`'s `_weapon_effect_record`).

### Tick mechanics

- `recovered/entities/units/unit/unit.tscn:51-52`: `BurningTimer` node,
  `wait_time = 0.5` — burns tick every 0.5s. This is an engine constant,
  not per-weapon.
- `recovered/entities/units/unit/unit.gd:581-583`: on a landed hit,
  `if hitbox.burning_data != null and
  Utils.get_chance_success(hitbox.burning_data.chance) ...:
  apply_burning(hitbox.burning_data)` — chance is rolled once per landed
  hit, not per tick.
- `recovered/entities/units/unit/unit.gd:618-648` (`apply_burning`):
  re-applying while already burning refreshes via `max()` on
  chance/damage/duration/spread — it does not stack additively.
- `recovered/entities/units/unit/unit.gd:660-706` (burn tick handler):
  each tick deals a flat `_burning.damage`, then `_burning.duration -= 1`;
  burn ends at `duration <= 0`.
- `recovered/singletons/weapon_service.gd:290-332` (`init_burning_data`):
  `damage` is scaled by the burn's own `scaling_stats` (default
  `[["stat_elemental_damage", 1.0]]`, `recovered/effects/burning_data.gd:8`)
  then by `stat_percent_damage`. At zero of both — this dataset's baseline —
  it reduces to `max(1, base_damage)`, i.e. the `.tres` `damage` field
  as-is.
- `recovered/effects/burning_data.gd:4`: `export (float) var chance: = 0.0`
  — burn's own missing-field default is **0.0**, unlike the exploding
  effect's default of `1.0`.

### Damage dealt

- `damage_source: "burn_dot"`, modeled as
  `dps0 = damage_per_tick / 0.5`, `slope = 0.0` (`calc.burn_dps_line`).
  Assumes steady-state: continuous attacking keeps the burn refreshed from
  ignition onward, so uptime is effectively 100%.

### Verified precondition (not a general model)

Empirically checked across every shipped burn weapon and tier
(`extracted/weapons/**/*_burning_data.tres` + matching `*_stats.tres`):
every one has `chance = 1.0`, and every one has
`cycle_time <= duration × 0.5s` (tightest margin: Particle Accelerator T3,
cycle_time≈1.95s vs. a 4s window). The model in `builders/weapons.py`
enforces both conditions per-weapon and falls back to `unmodeled_effects`
if either fails, rather than extrapolating an unverified duty-cycle formula
for `chance < 1.0` or a slower-cycling weapon — no shipped weapon exercises
either case.
```

- [ ] **Step 2: Update the unmodeled-effects worklist table**

In `docs/proc-mechanics.md`, in the "Unmodeled effect-key worklist" table, replace:

```
| 19 | `effect_burning` |
```

with:

```
| 19 | `effect_burning` (modeled) |
```

- [ ] **Step 3: Commit**

```bash
git add docs/proc-mechanics.md
git commit -m "docs(proc-mechanics): document the burning effect model"
```
