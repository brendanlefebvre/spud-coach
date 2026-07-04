# MCP Registry Listing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish spud-coach's `server.json` to the official MCP registry automatically on every release, using the same GitHub OIDC trusted-publishing pattern as the existing PyPI workflow, and hand off ready-to-paste copy for the one manual step (the `mcpservers.org` submission form).

**Architecture:** A new `server.json` manifest at the repo root describes the server (name, PyPI package reference, transport). A second job (`publish-registry`) is added to the existing `.github/workflows/publish.yml`, gated with `needs: publish` so it only runs after the PyPI package for that version is confirmed live. It downloads the `mcp-publisher` CLI, authenticates via GitHub OIDC (no stored secret), stamps the release version into `server.json`, and publishes.

**Tech Stack:** `jq` (pre-installed on `ubuntu-latest` runners), `mcp-publisher` CLI (downloaded from `modelcontextprotocol/registry` GitHub releases), GitHub Actions OIDC.

## Global Constraints

- Registry name: `io.github.brendanl79/spudcoach` (matches the PyPI package name, not the repo name `spud-coach` or the `plugin/.mcp.json` key `brotato-coach`)
- No stored secrets — GitHub OIDC only, matching the existing PyPI job's trusted-publishing pattern
- `websiteUrl` points at the GitHub repo for now (`https://github.com/BrendanL79/spud-coach`) — update to `https://spudcoach.fyi` once phase 3 (landing page) ships
- Registry publish must run strictly after the PyPI publish succeeds for the same release
- Out of scope: renaming the `plugin/.mcp.json` server key (flagged for pre-1.0 cleanup, not this plan), automating the `mcpservers.org` form submission (no public API)

---

### Task 1: Add the `server.json` registry manifest

**Files:**
- Create: `server.json` (repo root)

**Interfaces:**
- Produces: a `server.json` file with `packages[0].version` and top-level `version` both currently `"0.9.0"`. Task 2's workflow step reads and rewrites both these fields at release time via `jq`.

- [ ] **Step 1: Write the manifest**

Create `server.json`:

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

- [ ] **Step 2: Validate the JSON is well-formed**

Run:

```bash
uvx --with pyyaml python -c "import json; json.load(open('server.json')); print('valid JSON')"
```

Expected: prints `valid JSON` with no exception. (`pyyaml`'s presence is irrelevant here — this just reuses an environment that already has Python available, same trick as the phase-1 YAML check. Plain `python3 -c "import json; ..."` works too if a bare `python3` is on PATH.)

- [ ] **Step 3: Cross-check the identifier matches the real PyPI package**

Run:

```bash
grep '"identifier"' server.json
grep '^name' pyproject.toml
```

Expected: `server.json` shows `"identifier": "spudcoach"`, `pyproject.toml` shows `name = "spudcoach"` — same string, confirming the registry entry points at the package that's actually published.

- [ ] **Step 4: Commit**

```bash
git add server.json
git commit -m "feat: add server.json for official MCP registry listing"
```

---

### Task 2: Extend the release workflow with a registry-publish job

**Files:**
- Modify: `.github/workflows/publish.yml`

**Interfaces:**
- Consumes: `server.json` from Task 1 (reads/rewrites `.version` and `.packages[0].version`).
- Consumes: the existing `publish` job's success (`needs: publish`) — this job only starts once the PyPI job in the same workflow run completes successfully.

- [ ] **Step 1: Rename the workflow and add the new job**

The workflow now does two things (PyPI + registry), so its display name in the Actions tab should say so. Replace the full contents of `.github/workflows/publish.yml`:

```yaml
name: Publish release

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

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

- [ ] **Step 2: Validate the YAML is well-formed**

Run:

```bash
uvx --with pyyaml python -c "import yaml; yaml.safe_load(open('.github/workflows/publish.yml')); print('valid YAML')"
```

Expected: prints `valid YAML` with no exception.

- [ ] **Step 3: Confirm the job dependency is wired correctly**

Run:

```bash
grep -A1 'publish-registry:' .github/workflows/publish.yml
```

Expected output includes `needs: publish` on the line immediately after `publish-registry:` — this is what guarantees the registry publish never races ahead of the PyPI publish.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/publish.yml
git commit -m "ci: publish to the official MCP registry after each PyPI release"
```

---

### Task 3: Bump to 0.9.1 to get a release that exercises the new job

**Files:**
- Modify: `pyproject.toml:3` (the `version = "0.9.0"` line)
- Modify: `uv.lock` (regenerated — pins the project's own version at the `name = "spudcoach"` entry)

**Interfaces:**
- Produces: project version string `0.9.1`. `v0.9.0` is already live on PyPI (immutable), so a new version number is required to get a release event that runs the new `publish-registry` job — `server.json`'s committed `0.9.0` values are stamped over at release time by Task 2's `jq` step regardless of what's committed, so no further edit to `server.json` is needed here.

- [ ] **Step 1: Edit the version field**

In `pyproject.toml`, change:

```toml
version = "0.9.0"
```

to:

```toml
version = "0.9.1"
```

- [ ] **Step 2: Regenerate the lockfile so it matches**

Run: `uv lock`

Expected: exits 0. Confirm with:

```bash
grep -A1 'name = "spudcoach"' uv.lock
```

Expected output includes `version = "0.9.1"`.

- [ ] **Step 3: Confirm the test suite still passes**

Run: `uv run pytest`

Expected: same pass/fail counts as the last run on this branch — a version bump must not change test behavior.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: bump version to 0.9.1 to exercise the MCP registry publish job"
```

---

### Task 4: Cut the release (manual, not subagent-executed)

Same reasoning as phase 1's Task 3: creating a GitHub Release is a real,
public action (a new immutable PyPI version), so it isn't triggered
automatically as part of plan execution. Whoever executes this plan should
stop after Task 3 and hand back to the user for this step.

**Manual steps (for the user to run, or explicitly confirm before an agent runs them):**

1. Push the three commits from Tasks 1–3 to `main`.
2. Create a GitHub Release:
   ```bash
   gh release create v0.9.1 --title "v0.9.1" --generate-notes
   ```
3. Watch the workflow run: `gh run watch` — this time expect two jobs,
   `publish` and `publish-registry`, both green.
4. Confirm the entry exists on the official registry:
   ```bash
   curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=spudcoach"
   ```
   Expected: JSON response containing `"name": "io.github.brendanl79/spudcoach"`.
5. Submit the `mcpservers.org` listing manually at `https://mcpservers.org/submit`,
   using the copy from `docs/superpowers/specs/2026-07-04-mcp-registry-design.md`
   (Name: Brotato Coach; Tagline, Description, Category/tags, Repository,
   Package, and Install command are all pre-written there — copy/paste, no
   drafting needed).

**Rollback note:** if `publish-registry` fails after `publish` already
succeeded, the PyPI package for that version is still live and fine — only
the registry job needs a retry. Re-running the failed job via
`gh run rerun --failed` is safe since `mcp-publisher publish` for an
already-registered name/version is expected to be idempotent-or-erroring,
not duplicating entries.
