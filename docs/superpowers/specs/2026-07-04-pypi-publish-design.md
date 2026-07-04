# PyPI publish (phase 1 of 3: ship it)

Part of a three-phase publish push: **PyPI publish** (this doc) → MCP registry
listings → landing page. Each phase gets its own spec/plan.

## Goal

Make `uvx spudcoach` work for anyone, published from PyPI, via an automated,
repeatable release process — no manual `twine upload` from a laptop, no
long-lived API tokens to leak.

## Mechanism: GitHub Actions + PyPI Trusted Publishing

PyPI's OIDC-based trusted publishing lets a specific GitHub Actions workflow
authenticate to PyPI with no stored secret. PyPI is configured (by the repo
owner, external to this repo) to trust:

- Repo: `BrendanL79/spud-coach`
- Workflow filename: `.github/workflows/publish.yml`
- Environment: `pypi`

These prerequisites are already done as of 2026-07-04:
- PyPI account created, pending trusted publisher registered for project
  `spudcoach`.
- GitHub environment `pypi` created on the repo (verified via
  `gh api repos/BrendanL79/spud-coach/environments`).

## Release trigger

Publishing a **GitHub Release** (not a bare tag push) fires the workflow.
Tag format: `vX.Y.Z`. This gives a changelog for free and matches the most
common community pattern.

## Version

Bump `pyproject.toml` from `0.2.0` to `1.0.0` for the first public release —
this is the project's public debut, treated as the 1.0 milestone.

## Workflow: `.github/workflows/publish.yml`

Triggers on `release: published`. Steps:

1. Checkout
2. Set up `uv`
3. `uv run pytest` — the existing 89-test suite (1 test auto-skips without a
   built dataset, same as local runs without `data/brotato.json`). A failing
   test blocks the release.
4. `uv build` — produces sdist + wheel via the existing hatchling
   `[build-system]` config (no changes needed there).
5. `pypa/gh-action-pypi-publish` — publishes via OIDC trusted publishing
   against the `pypi` environment, no token/secret in the workflow.

## Out of scope

- TestPyPI dry-run rehearsal — skipped; `spudcoach` is unclaimed and trusted
  publishing to a fresh project is normally reliable.
- Required-reviewer manual-approval gate on the `pypi` environment — not
  configured; releases publish as soon as the GitHub Release is published.
- MCP registry listing and landing page — separate phases.

## Testing

No new application tests. Verification is: cut a real GitHub Release
(`v1.0.0`) and confirm the workflow run is green and the package appears on
PyPI, then confirm `uvx spudcoach --help` works from a clean environment.
