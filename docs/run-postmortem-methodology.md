# Run post-mortem methodology

When diagnosing why a run was lost, evaluate two independent axes separately rather than as one blob:

- **Build strength** — weapon tiers, set-bonus completion (`active_sets` in the save).
- **Survivability** — Max HP%, lifesteal sign (negative lifesteal is actively harmful — dealing damage costs HP), speed sign (negative speed impairs dodging), armor, and item tags that spawn extra enemies (e.g. `item_bait`).

A run can have a maxed/optimal weapon build and still lose purely to accumulated survivability debt — don't conflate the two when giving a post-mortem.

Examples:
- Wave 19 loss: fully validated build (3x Shredder T4 + 2x Laser T4 + Revolver T4, both sets active) but died from Bait-spawned extra enemies + negative lifesteal + negative speed compounding chip damage before the boss.
- Wave 20 loss (13 retries): armor dropped from 6 (mid-run snapshot) to 3 (death screen) — traced to picking up Glass Cannon (`stat_percent_damage +25`, `stat_armor -3`) sometime after Wave 19, cutting an already-thin armor value in half right before the hardest wave.

Related tips:
- Before buying a stat-scaled item/pet, check its `scaling_stats` field (in `*_effect*.tres` or weapon stats) against the player's actual stat investment — e.g. Bot-O-Mine scales 100% on `stat_engineering` and is dead weight at Engineering=0; that gold is usually better spent on rerolls toward stats/items the build actually uses.
- When scanning a screenshot's item-icon grid for a specific item, a single quick glance is unreliable (small/similar icons cause misses). Before asserting an item is absent, deliberately re-scan the full grid.
