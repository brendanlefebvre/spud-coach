# Brotato proc mechanics

Reference facts derived from decompiled code, for judging weapon on-hit proc
effects without re-deriving from scratch. Companion to `docs/stat-mechanics.md`.
Each entry in `brotato_coach/builders/procs.py`'s `PROC_MODELS` must cite the
evidence recorded here.

## Exploding effect (`ExplodingEffect`, `recovered/effects/weapons/exploding_effect.gd`)

Three weapon-effect `key` values all attach the same `exploding_effect.gd`
script and are therefore the same mechanic at runtime, since the game
dispatches on script class, not on the key string:

- `effect_explode_custom` — Shredder T1/T2/T3 (`chance` 0.5 / 0.65 / 0.8)
- `effect_explode` — Fireball, Nuclear Launcher T3/T4, Rocket Launcher (all
  `chance` 1.0), Shredder T4 (`chance` 1.0)
- `effect_explode_melee` — Plank T1–T4 (0.25 / 0.3 / 0.4 / 0.5), Power Fist
  T3/T4 (0.25 / 0.5), Plasma Sledgehammer T3/T4 (0.25 / 0.5), Dextroyer T4
  (0.5)

All three keys get the same `PROC_MODELS` entry (see below).

### Damage dealt

- `recovered/weapons/weapon.gd:419-436`, `_on_Hitbox_hit_something`: for each
  weapon effect, `if effect is ExplodingEffect and
  Utils.get_chance_success(effect.chance):` spawns an explosion with
  `_explosion_args.damage = _hitbox.damage` (line 427) — the weapon's own
  *current* hit damage (base + scaling stats, post-crit-chance/accuracy
  setup) — and forwards `accuracy`, `crit_chance`, `crit_damage`, and
  `scaling_stats` from the same hitbox (lines 428-431).
- Conclusion: the explosion re-deals the weapon's own damage line, unscaled
  beyond what the weapon already applies. `damage_source: "weapon_damage"`,
  `damage_multiplier: 1.0` is CONFIRMED, not an assumption.

### Enemies-hit semantics (AoE nuance)

- `recovered/weapons/weapon.gd:435`: `_explosion_args.ignored_objects =
  [thing_hit]` — the enemy that was just hit by the direct attack is
  explicitly excluded from the explosion's own hit list. The explosion can
  therefore only damage *other* enemies caught in its blast radius.
- Consequence: against a lone enemy, the exploding proc adds **zero**
  additional damage — the explosion has nothing left to hit. The
  `default_enemies_hit: 1.0` in the model means "assume one *other* enemy is
  caught in the blast," which is conservative for crowded waves (undercounts
  actual value against 3+ enemies) and optimistic against a single target
  (overcounts — the true value there is 0). Callers evaluating single-target
  scenarios (e.g. boss waves) should override `enemies_hit` down.

### Chance default

- `recovered/effects/weapons/exploding_effect.gd:4`: `export (float, 0.0,
  1.0, 0.01) var chance: = 1.0` — the engine's own default for a missing
  `chance` field is 1.0 (always triggers), not some lower value.
- This confirms the builder's existing `eff.get("chance", 1.0)` fallback is
  correct engine behavior, not a silent bug, resolving the carry-over
  question from the original plan.
- Empirically moot either way: all 17 `.tres` files across the three
  exploding-effect keys set `chance` explicitly (verified via `grep -rl
  'key = "effect_explode' extracted/weapons/ | xargs grep chance`), so the
  default never actually fires for a shipped weapon today.

### Known limitation: `explosion_damage` player stat (unmodeled)

- `recovered/singletons/weapon_service.gd:245-249`: weapons flagged
  `is_exploding` get an *additional* multiplicative damage bonus from the
  player's `explosion_damage` stat (`Keys.explosion_damage_hash`), folded
  into `new_stats.damage` alongside `stat_percent_damage`:
  `exploding_dmg_bonus = Utils.get_stat(Keys.explosion_damage_hash,
  player_index) / 100.0`.
- This stat is zero at base (no starting items grant it as a flat weapon
  stat; it only exists as a player-accumulated stat from items), so it does
  not change the weapon's *base* precomputed proc line and is intentionally
  left out of the static dataset. Documented here as a known limitation:
  builds that stack `explosion_damage`-granting items will out-DPS the
  dataset's static `proc_dps_at_zero_rd` line for exploding weapons — callers
  reasoning about such builds should account for this manually.
- `recovered/singletons/weapon_service.gd:511`, `func explode(effect:
  ExplodingEffect, args: WeaponServiceExplodeArgs) -> Node`: spawns the
  explosion scene and applies `args` (the damage + scaling stats captured in
  weapon.gd above) to the explosion's own hitbox — no separate flat damage
  value is defined on the scene itself.

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

## Companion-projectile procs (`ProjectilesOnHitEffect`, `recovered/effects/weapons/projectiles_on_hit_effect.gd`)

One script class serves four differently-keyed effects (dispatch is on script
class; casing is cosmetic): `effect_lightning_on_hit` (Lightning Shiv T1-4,
Dextroyer T4), `effect_projectiles_on_hit` (Cactus Mace T1-4),
`EFFECT_PROJECTILES_ON_HIT` (Sniper Gun T3-4), and
`EFFECT_SLOW_PROJECTILES_ON_HIT` (Thunder Sword T3-4). All share one
`PROC_MODELS` entry (`damage_source: "companion_ranged_stats"`). Full
evidence: `docs/superpowers/research/2026-07-05-family-lightning.md` and
`...-family-projectiles-on-hit.md`.

### Mechanics

- `recovered/weapons/weapon.gd:146-149` (`init_stats`): for a
  `ProjectilesOnHitEffect`, the hitbox carries `[effect.value, companion
  weapon_stats, effect.auto_target_enemy]`.
- `recovered/entities/units/unit/unit.gd:586-603`: on every landed hit,
  `value` projectiles spawn from the just-hit enemy's position —
  **unconditionally** (no chance roll; there is no `chance` field on this
  effect class, and `value` is a spawn count, not a probability).
- Damage is fully independent of the host weapon: the companion
  `RangedWeaponStats` (`weapon_stats = ExtResource(N)` on the effect .tres)
  carries its own `damage`, `scaling_stats`, crit fields. At the dataset's
  zero-stat baseline this reduces to the companion's raw `damage` field
  (`recovered/singletons/weapon_service.gd` `init_ranged_stats(…,
  is_special_spawn=true)`).
- Targeting (`recovered/singletons/weapon_service.gd:353-357`): with
  `auto_target_enemy=true` (lightning users) the projectile aims at a
  uniformly *random other* enemy (`recovered/global/entity_spawner.gd:485-495`,
  excludes the triggering enemy — worth 0 against a lone target); with
  `false` (all other users) the direction stays `rand_range(-PI, PI)` — an
  unaimed spray.
- Bounce chaining (`recovered/projectiles/player_projectile.gd:119-129`)
  re-rolls a random target per hop; lightning users ship `bounce` 0/1/2/3/4
  with an explicit `bounce_dmg_reduction = 0.0` (engine default is 0.5,
  `recovered/weapons/weapon_stats/ranged_weapon_stats.gd:9`); spray users
  ship `bounce = 0`.

### Model

`proc_dps0 = companion_damage × value × enemies_hit / host_cycle_time`, slope
via the companion's own `stat_ranged_damage` coefficient (nonzero only for
Cactus Mace, 0.6→1.0 by tier; lightning scales off elemental, Sniper Gun off
`stat_range`, Thunder Sword off elemental — slope 0 for those).

`enemies_hit` policy (the softest number, like exploding's
`default_enemies_hit`):

- targeted chain: `1 + bounce`, gated on lossless bounce (`bounce == 0` or
  `bounce_dmg_reduction == 0.0`) — assumes the nominal chain connects;
  optimistic in sparse fields, 0 against a lone enemy.
- untargeted spray: `1.0` per volley, gated on `bounce == 0` — a pure
  assumption constant; a random-direction volley has no evidence anchor for
  its hit rate. Callers evaluating single-target scenarios should override
  down, as with exploding.

Gate failures (missing companion/damage, `value <= 0`, lossy or unexpected
bounce) fall back to `unmodeled_effects` — no decaying-bounce or
hit-probability math is modeled, since no shipped weapon needs it.

Thunder Sword's spawned projectile is literally taser's bullet scene, whose
`SlowHitbox` applies a hardcoded `add_decaying_speed(-200)`
(`recovered/projectiles/bullet_taser/taser_projectile.gd:15-17`) — the slow
is CC (see classification below);
this model scores only the companion's damage=1 sliver.

## Effect classification (`brotato_coach/builders/classifications.py`)

Effects with no damage model but a fully evidenced mechanic are classified
into `classified_effects` on the weapon record instead of polluting
`unmodeled_effects` (which now strictly means "uninvestigated" — blank-key
effects surface there by script basename instead of being dropped silently).
Classification is mechanism-based (script basename, then `storage_method`,
then key string) — never per-weapon lists. Categories, with evidence in the
2026-07-05 research dossiers:

| category | shipped examples | notes |
|---|---|---|
| `stat_rider` | Rock armor/HP, Hand harvesting, Fighting Stick xp_gain, Hammer knockback (player-wide, `recovered/singletons/weapon_service.gd:265-270`), Jousting Lance speed, Torch `burning_spread` (+1 one-hop burn spread, global stat, `recovered/singletons/weapon_service.gd:334`), Chopper `consumable_heal` | flat SUM grant while held (`recovered/singletons/run_data.gd:989/1081`) |
| `dynamic` | Jousting Lance stand-still −damage% (`recovered/entities/units/player/player.gd:215-239`), Scythe T4 on-player-hit stack (`recovered/entities/units/player/player.gd:493-495`), Excalibur −2 armor × weapons owned (`recovered/singletons/run_data.gd:1190-1203`), Sharp Tooth missing-HP lifesteal (`recovered/singletons/linked_stats.gd`), Drill T4 unbounded +AS/5s, Rail Gun no-hit ramp (`recovered/weapons/ranged/rail_gun/railgun.gd:82-99`), Ghost weapons kill ratchet (`recovered/weapons/weapon.gd:211-232`) | state/build/time-dependent; no honest static number — deliberately no metadata value |
| `economy` | Dagger/Drill `gold_on_crit_kill` (`recovered/entities/units/unit/unit.gd:376-379`, value%/100 for +1 gold on crit-kill) | |
| `cc` | Particle Accelerator slow (engineering-scaled, `recovered/singletons/weapon_service.gd:191` → `recovered/entities/units/unit/unit.gd:605-606`), Taser `effect_slow_in_zone` (inert marker — the −200 slow is hardcoded in the projectile scene, not in extracted data) | |
| `delivery_modifier` | Crossbow `pierce_on_crit`, Shuriken `bounce_on_crit` (`recovered/projectiles/player_projectile.gd:132-154`: each crit converts one charge into +1 pierce/bounce, per-projectile budget, 0% damage falloff by explicit override) | no DPS number — the expected crit-chain needs a crowd-density assumption on top of `crit_chance`; deferred |
| `drawback` | Scythe T4 `lose_hp_per_second` (3 HP/s, undodgeable/unarmored, `recovered/entities/units/player/player.gd:844-850`) | |
| `execute` | Vorpal Sword T2-4 blank-key `OneShotOnHitEffect` (`recovered/entities/units/unit/unit.gd:285-305`: value% chance to force damage = target's current HP) | chance surfaces as `execute_chance_per_hit`; damage is run-state-dependent, never folded into DPS |
| `stack` | Stick `EFFECT_WEAPON_STACK` (`recovered/singletons/weapon_service.gd:192-197`: +value flat damage per extra copy owned, additive before RD scaling → slope 0) | `bonus_per_extra_copy` metadata; per-copies DPS needs a loadout axis the schema doesn't have — computed at answer time if needed |
| `structure` | Screwdriver landmines (blank key, `StructureEffect`; mine damage flat 10 + `stat_engineering` scaling for all tiers, tier only buys spawn rate 12/9/6/3s; trigger is enemy enter-then-exit pathing — no evidence anchor for an "eventually triggers" steady state), Pruner garden (spawning `TurretEffect`, `damage = 0` explicit — healing-fruit spawner; its own `spawn_cooldown` field ships as the unused `-1` sentinel, so the real cadence is the garden's `stats.cooldown` in frames — 900/840/720/600 for T1-T4 — which the classifier falls back to) | `spawn_cooldown` is the raw engine value: seconds for `StructureEffect`'s own field, frames for the turret `stats.cooldown` fallback |

## Unmodeled effect-key worklist

Effect `key` values found across `extracted/weapons/*.tres`
(`grep -rh '^key = ' extracted/weapons/ | sort | uniq -c`). As of the
2026-07-05 triage (research dossiers under `docs/superpowers/research/`),
every shipped key is either modeled (contributes to `proc_dps_*`) or
classified (`classified_effects`); `unmodeled_effects` is empty across the
shipped dataset and now strictly means "uninvestigated." Blank-key effects
are named by script basename rather than silently dropped.

| count | key | disposition |
|---|---|---|
| 19 | `effect_burning` | modeled (burn_dot) |
| 12 | `effect_gain_stat_every_killed_enemies` | classified: dynamic |
| 10 | *(blank key)* | classified: execute (Vorpal Sword) / structure (Screwdriver, Pruner) |
| 9  | `effect_explode_melee` | modeled (weapon_damage) |
| 5  | `stat_percent_damage` | classified: dynamic (KEY_VALUE storage on all shipped users) |
| 5  | `gold_on_crit_kill` | classified: economy |
| 5  | `effect_lightning_on_hit` | modeled (companion_ranged_stats) |
| 5  | `effect_explode` | modeled (weapon_damage) |
| 4  | `xp_gain` | classified: stat_rider |
| 4  | `stat_speed` | classified: stat_rider |
| 4  | `stat_lifesteal` | classified: dynamic (missing-HP-scaled) |
| 4  | `stat_harvesting` | classified: stat_rider |
| 4  | `stat_armor` | classified: stat_rider (Rock) / dynamic (Excalibur, KEY_VALUE) |
| 4  | `pierce_on_crit` | classified: delivery_modifier |
| 4  | `effect_projectiles_on_hit` | modeled (companion_ranged_stats) |
| 4  | `effect_no_hit_boost` | classified: dynamic |
| 4  | `bounce_on_crit` | classified: delivery_modifier |
| 4  | `EFFECT_WEAPON_STACK` | classified: stack |
| 3  | `knockback` | classified: stat_rider |
| 3  | `effect_explode_custom` | modeled (weapon_damage) |
| 2  | `EFFECT_PROJECTILES_ON_HIT` | modeled (companion_ranged_stats) |
| 2  | `EFFECT_SLOW_PROJECTILES_ON_HIT` | modeled (damage sliver) + CC noted |
| 2  | `EFFECT_WEAPON_SLOW_ON_HIT` | classified: cc |
| 2  | `burning_spread` | classified: stat_rider (global) |
| 2  | `consumable_heal` | classified: stat_rider |
| 2  | `stat_max_hp` | classified: stat_rider |
| 1  | `effect_slow_in_zone` | classified: cc |
| 1  | `lose_hp_per_second` | classified: drawback |
| 1  | `stat_attack_speed` | classified: dynamic (interval accumulator) |
