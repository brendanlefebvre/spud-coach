# Brotato stat mechanics

Reference facts derived from decompiled code, for judging itemization/stat-priority tradeoffs without re-deriving from scratch:

- **stat_curse**: positive curse scales enemy damage/HP via a `sqrt(curse)` factor (`entity_service.gd`) — avoid. Negative curse is clamped to zero benefit — harmless to have, but not a defensive gain either.
- **Stat caps**: `utils.gd`'s `get_capped_stat`/`get_max_capped_stat` cap `stat_max_hp`, `stat_speed`, `stat_dodge`, `stat_curse`, and `stat_crit_chance` — relevant when judging whether further investment in one of these is wasted.
- **stat_attack_speed** is a universal cooldown-reducing multiplier, confirmed applied identically in both `ranged_shooting_data.gd` and `melee_shooting_data.gd` — never dead weight regardless of weapon type.
- **stat_hp_regeneration** at or below 0 is a harmless no-op (`player.gd`'s `check_hp_regen`/`set_hp_regen_timer_value` just stops the regen timer) — unlike negative lifesteal, which actively drains HP on hit.

## Cap-at-current-value item archetype

Some items grant a strong stat bonus in exchange for permanently freezing a *different* stat at its current value for the rest of the run. Observed on Handcuffs (`key="hp_cap"`, `text_key="EFFECT_HP_CAP_AT_CURRENT_VALUE"`) and Shackles (`key="speed_cap"`, `text_key="EFFECT_SPEED_CAP_AT_CURRENT_VALUE"`). Detect via the `key`/`text_key` naming pattern, not `effect_sign` — that field is inconsistent across these items (Handcuffs uses 0, Shackles uses 3), so it can't be used to spot the archetype. When evaluating such an item, weigh how costly freezing that specific stat is for the build's remaining waves (e.g. freezing Max HP is much worse than freezing Speed for a build that's already capped or doesn't need more).

## Ranger character kit

Reverse-engineered from `items/characters/ranger/ranger_data.tres` + effect files:
- `wanted_tags=["stat_ranged_damage","stat_range"]`, `banned_item_groups=["melee_damage"]`, `no_melee_weapons` effect.
- Flat `+50 stat_range`.
- `+50%` gain modifier on `stat_ranged_damage` (`ranger_effect_4.tres`, key=`effect_increase_stat_gains`).
- `-25%` gain modifier on `stat_max_hp` (`ranger_effect_6.tres`, key=`effect_reduce_stat_gains`).

Gain modifiers are applied multiplicatively to the raw effects-dict sum at *display* time: `displayed_stat = raw_effects_sum * character_gain_modifier`. Verified: raw RD 6 × 1.5 = displayed 9; raw max_hp 48 × 0.75 = displayed 36. Implementation: `recovered/effects/items/stat_gains_modification_effect.gd`.
