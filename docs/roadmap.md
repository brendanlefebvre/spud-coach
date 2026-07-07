# spud-coach — Roadmap

Coarse, high-level next steps — a shared backlog, not committed timelines.
Ordered by priority.

Shipped: the `read_me` session-orientation primer (package prose + live
dataset provenance, superseding the build-time-distillation idea),
1-indexed item tiers matching the in-game display (dataset schema v3),
proc-aware DPS with verified exploding/burning/companion-projectile
models, the full proc-worklist triage (every shipped effect modeled or
classified — `unmodeled_effects` is empty dataset-wide; 9-category
`classified_effects` with metadata like Vorpal's execute chance), loadout
set-bonus reasoning, the complete 16-stat mechanics table (incl. the
`stat_range` projectile-speed nuance), localized names/effect text (dataset
schema v2), run-save ingestion (`evaluate_run` post-mortem tool), the PyPI
release (`uvx spudcoach`, latest tagged **v0.10.0**), and the official MCP
registry listing.

On `main`, merged but not yet in a tagged/PyPI release (v0.10.0 predates it):

- **Bestiary awareness** — enemy records (base stats + per-wave scaling
  slopes + attack profile + ability tags) and base-game (Crash Zone /
  `zone_1`) per-wave spawn composition, exposed via `get_enemy`,
  `list_enemies`, and `wave_composition`, plus a `wave_context` section in the
  `evaluate_run` post-mortem (dataset **schema v4**). Base-game Zone 1 only;
  bosses are records with a `bespoke_kit_not_modeled` flag. Honesty envelope:
  exact stats/base composition, run-dependent counts and elite/horde presence
  labelled as run-variance. Spec/plan under `docs/superpowers/`.

## Ship (in progress)

- **Cut the next release** — bump the package version off `v0.10.0` and
  tag/publish so PyPI ships the bestiary layer + dataset schema v4 (the
  current tag predates the bestiary merge).
- **Finish publish checklist** — spudcoach.fyi install page and an
  awesome-mcp-servers entry. Checklist: Phase C of
  `docs/superpowers/plans/2026-07-02-roadmap-implementation.md` (each step
  needs an explicit go-ahead).

## Bigger build

- **Wire achievements into the dataset** — the achievement/challenge builder
  (`brotato_coach/builders/achievements.py`) and its gather script
  (`tools/gather_achievements.py`) are merged (#12) as prep, but nothing in
  `build_dataset.py` references them yet: achievement records aren't in the
  dataset. Next step is folding them into the build (and deciding on an MCP
  surface — e.g. "what does this character/item unlock").
- **Bestiary follow-ups** — extend past base-game Zone 1: DLC zones 2/3
  (Abyssal Terrors) wave data; boss/elite multi-phase kits (currently flagged
  `bespoke_kit_not_modeled` rather than modeled); and richer `appears_in`
  provenance so horde/elite/endless-only enemies carry a label instead of an
  empty list. Deferred test-hardening minors are logged in the bestiary
  implementation plan/review notes.
