# Brotato Coach

Deterministic theorycrafter core + MCP server for a Brotato AI coach.

## Build the dataset

Requires a local extraction (`extracted/`) from a Brotato install (see
`docs/extraction-setup.md`). Then:

```bash
uv run python build_dataset.py --game-version <version> \
    --generated-at $(date -u +%Y-%m-%dT%H:%M:%SZ)
```

This writes `data/brotato.json`, the committed artifact the server reads.
Re-run it after each Brotato patch.

## Run the MCP server

```bash
uv run python -m brotato_coach.server
```

## Use as a Claude Code plugin

The server is registered via `plugin/.mcp.json`. The tools expose weapon/item/
character lookups, DPS and merge-path calculators, stat-mechanics explanations,
and the `evaluate_item_for_build` build-fit evaluator.

## Test

```bash
uv run pytest
```
