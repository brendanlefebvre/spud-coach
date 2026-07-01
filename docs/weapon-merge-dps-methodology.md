# Weapon merge DPS methodology

To compare two ways of merging weapons up to the same final tier (e.g. LaserGun II+II vs III+I), compute each path's DPS as a linear function of the player's ranged-damage (RD) stat and check whether one dominates everywhere or the lines cross over.

Formula: `cycle_time = recoil_duration*2 + cooldown/60`; `DPS = (base_damage + RD*scaling_coefficient) / cycle_time`, using the `damage`, `cooldown`, `recoil_duration`, and `scaling_stats` coefficient from each tier's `*_stats.tres` (see [extraction-setup.md](extraction-setup.md) for paths). Multiply by `accuracy` for an effective/realized DPS when comparing weapons with different accuracy.

For weapons with an `additional_cooldown_every_x_shots` burst/reload mechanic (e.g. Revolver: every 6 shots, add `cooldown * additional_cooldown_multiplier / 60` extra seconds), fold the average extra time per shot into `cycle_time`: `cycle_time += (cooldown * additional_cooldown_multiplier / 60) / additional_cooldown_every_x_shots`.

Examples:
- LaserGun II+II vs III+I was a near-coinflip (~1% DPS difference at any RD — decide by merge-planning convenience instead). IV+I vs III+III had a clear, RD-independent winner (IV+I, no crossover at any RD value).
- Comparing per-weapon-slot DPS slope (damage gained per RD point) across T4 ranged weapons for a Ranger build: Minigun's tiny cooldown gives it the highest slope (~8.3 dmg/s per RD) despite a modest 0.75 scaling coefficient — it beats Revolver (slope ~2.9, RD-scaling coefficient 2.0 but taxed by the reload mechanic above) at any RD > ~0.33, i.e. essentially always in real play. Laser Gun has the highest raw scaling coefficient (6.0) and a strong slope (~3.6) but a long cycle time.

Tip: if a shop offers a copy of a weapon already owned, buying it merges into the existing weapon in place — it does not consume a new weapon slot. Surface this explicitly when recommending such a purchase, since it removes the usual slot-cost tradeoff.

Note: Legendary weapons (e.g. Chain Gun) only have a single, top-tier stats file — no lower tiers exist to merge from. They drop already fully-formed and can't be deliberately built toward; treat them as an opportunistic pickup, not a plan.
