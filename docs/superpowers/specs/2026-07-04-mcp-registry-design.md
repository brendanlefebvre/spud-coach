# MCP registry listing (phase 2 of 3: ship it)

Part of a three-phase publish push: PyPI publish (done) → **MCP registry
listings** (this doc) → landing page. Each phase gets its own spec/plan.

## Goal

Make spud-coach discoverable through the MCP ecosystem's discovery surfaces,
with the automatable part (the official registry) wired into the existing
release pipeline, and the non-automatable part (the `mcpservers.org` curated
list) handed to the user as ready-to-paste copy.

## Why this scope

The official MCP registry (`registry.modelcontextprotocol.io`) is the
machine-readable source of truth that other directories crawl: **Glama is
documented as a superset of the official registry**, and PulseMCP/Smithery
both crawl GitHub and the registry to build their listings. Publishing one
`server.json` to the official registry is expected to cascade into most of
the "big" aggregators without separate submissions to each.

The two major "awesome-mcp-servers" GitHub lists (`punkpeye/awesome-mcp-servers`
and `wong2/awesome-mcp-servers`) both now explicitly refuse PRs and redirect
to a single web form at `mcpservers.org/submit` instead. That form isn't
API-accessible, so it's a manual, human-run step — this phase prepares exact
copy for it rather than automating it.

## Naming decision

Registry entries use a permanent reverse-DNS name: `io.github.brendanl79/spudcoach`.
This matches the PyPI package name (`uvx spudcoach`) rather than the repo
name (`spud-coach`) or the current `plugin/.mcp.json` server key
(`brotato-coach`) — least confusing for someone going registry → install.

**Flagged, out of scope for this phase:** the `plugin/.mcp.json` server key
(`brotato-coach`) is inconsistent with both the PyPI package name and this
registry name. Rename it before a 1.0 release (tracked as a roadmap item,
not part of this phase).

## `server.json` (new file, repo root)

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.brendanl79/spudcoach",
  "title": "Brotato Coach",
  "description": "Deterministic Brotato theorycrafter MCP server. Facts + math over data you build from your own game install (copyrighted files aren't distributed).",
  "version": "0.9.0",
  "repository": {
    "url": "https://github.com/BrendanL79/spud-coach",
    "source": "github"
  },
  "websiteUrl": "https://github.com/BrendanL79/spud-coach",
  "packages": [
    {
      "registryType": "pypi",
      "registryBaseUrl": "https://pypi.org",
      "identifier": "spudcoach",
      "version": "0.9.0",
      "runtimeHint": "uvx",
      "transport": { "type": "stdio" },
      "environmentVariables": [
        {
          "name": "SPUDCOACH_DATA",
          "description": "Path to a locally built brotato.json dataset (see README for how to build one — the game data itself is never distributed). Equivalent to the --data CLI flag.",
          "isRequired": false,
          "isSecret": false
        }
      ]
    }
  ]
}
```

`websiteUrl` points at the GitHub repo for now; update it to `https://spudcoach.fyi`
once phase 3 (landing page) ships.

## Workflow: extend `.github/workflows/publish.yml`

Add a second job to the existing workflow (not a new file), so both jobs
share the same `release: published` trigger and the registry publish is
guaranteed to run after the PyPI publish succeeds:

```yaml
  publish-registry:
    needs: publish
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Stamp release version into server.json
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          jq --arg v "$VERSION" '.version = $v | .packages[0].version = $v' server.json > server.tmp
          mv server.tmp server.json

      - name: Install mcp-publisher
        run: |
          curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher

      - name: Authenticate to MCP Registry
        run: ./mcp-publisher login github-oidc

      - name: Publish to MCP Registry
        run: ./mcp-publisher publish
```

No secrets required — GitHub OIDC authentication, same trusted-publishing
pattern as the existing PyPI job.

`GITHUB_REF` on a `release: published` event is the tag ref (e.g.
`refs/tags/v0.9.0`), so the same `v*` tag-stripping approach from the
official quickstart applies unchanged even though the trigger is
`release: published` rather than `push: tags`.

## `mcpservers.org` submission copy (manual, handed to user)

Not automated — `mcpservers.org/submit` is a web form with no public API.
Ready-to-paste copy:

- **Name:** Brotato Coach
- **Tagline:** Deterministic Brotato theorycrafter — computes DPS, stat math, and run post-mortems instead of guessing.
- **Description:** A deterministic theorycrafter for Brotato, delivered as an MCP server you chat with from Claude Code (and other MCP clients). A deterministic core holds the ground truth — weapon/item/character data, DPS formulas, stat mechanics — so the language model looks facts up and computes instead of recalling (and misremembering) them. Every tool returns a finished, verifiable answer or a structured error; there are no baked-in tier lists or opinions, only facts and math. The dataset is never distributed (it's derived from copyrighted game files) — you build your own from a local Brotato install.
- **Category/tags:** Gaming, Data Analysis
- **Repository:** https://github.com/BrendanL79/spud-coach
- **Package:** https://pypi.org/project/spudcoach/
- **Install command:** `uvx spudcoach`

## Testing

No application logic changes. Verification: after the next tagged release,
confirm the `publish-registry` job goes green and the server appears at
`registry.modelcontextprotocol.io` under `io.github.brendanl79/spudcoach`.

## Out of scope

- Automating the `mcpservers.org` submission itself (no API).
- Renaming the `plugin/.mcp.json` server key (flagged for pre-1.0 cleanup).
- Smithery/PulseMCP/Glama direct submissions — expected to pick this up via
  crawling the official registry; revisit only if that doesn't happen in
  practice.
