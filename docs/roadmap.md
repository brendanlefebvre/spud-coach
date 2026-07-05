# spud-coach — Roadmap

Coarse, high-level next steps — a shared backlog, not committed timelines.
Ordered by priority.

Shipped: proc-aware DPS with verified exploding-effect models, loadout
set-bonus reasoning, the complete 16-stat mechanics table, localized
names/effect text (dataset schema v2), run-save ingestion (`evaluate_run`
post-mortem tool), the PyPI release (`uvx spudcoach`, currently v0.9.3), and
the official MCP registry listing.

## Ship (in progress)

- **Finish publish checklist** — tag the release and write GitHub release
  notes, stand up the spudcoach.fyi install page, and PR an entry to
  awesome-mcp-servers. Checklist: Phase C of
  `docs/superpowers/plans/2026-07-02-roadmap-implementation.md` (each step
  needs an explicit go-ahead).

## Bigger build

- **Incorporate enemy data** — build a bestiary layer from
  `extracted/entities/units/enemies/` (path verified: 90 `.tres` records) so
  the coach can give threat- and wave-aware advice (what's coming at a given
  wave / danger level), not just build-only reasoning. Needs its own
  implementation plan; survey commands are in the deferred section of the
  Phase A/B plan.

## Backlog (successors from shipped work)

- **Model the rest of the proc worklist** — only exploding procs carry
  expected DPS today; every other on-hit effect contributes zero and is
  surfaced in `unmodeled_effects`. `docs/proc-mechanics.md` holds the
  evidence-gated worklist (`effect_burning` ×19 is the top entry). The first
  non-`weapon_damage` model also triggers the deferred `aggregate_proc_dps`
  extraction.
- **stat_range projectile-speed nuance** — `weapon_service.gd::
  _set_common_ranged_stats:115` scales projectile speed off `stat_range`, but
  only for weapons with `increase_projectile_speed_with_range` (clamped
  50–6000). Verify and encode with the flag condition.
