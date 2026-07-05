# Landing Page Content Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three new sections to `site/index.html` — "Build your dataset," "Connect it to Claude," and "What you get" — bringing over the parts of the PyPI project page the landing page currently lacks, per the approved design spec.

**Architecture:** Pure static-content addition to the existing single-file `site/index.html` + `site/style.css` (no build step, no JS, no new dependencies). Three new `<section class="section">` blocks are inserted between the existing "Install" section and the footer; a small CSS addition styles the new `<h3>` sub-labels and tool-list `<ul>`s these sections introduce. No existing HTML/CSS is modified.

**Tech Stack:** Plain HTML5 + CSS3, matching the existing page exactly (same fonts, same CSS variables, same responsive breakpoints).

## Global Constraints

- No new colors, fonts, or CSS custom properties — every new rule reuses the existing `:root` variables (`--bg`, `--heading`, `--muted`, `--code-bg`, etc.) already defined in `site/style.css`.
- No changes to the existing Hero, "What it is," "Install," or footer content/copy.
- No changes to `netlify.toml`, deployment config, or DNS.
- The "Build your dataset" command is the bare `uv run python build_dataset.py` — no `--game-version`/`--generated-at` flags — since `build_dataset.py` now auto-detects both (see `docs/superpowers/plans/2026-07-05-auto-detect-game-version.md`, already implemented on this branch).
- The "What you get" tool list covers all 16 `@mcp.tool()`-decorated functions in `brotato_coach/server.py`, grouped into exactly four categories: Data lookups, DPS & comparison, Build evaluation, Run analysis.
- New sections appear in this order: Build your dataset → Connect it to Claude → What you get.

---

### Task 1: Add the three new sections and their CSS

**Files:**
- Modify: `site/index.html:39-42` (insert three new sections between the Install section's closing `</section>` and `</main>`)
- Modify: `site/style.css` (append new rules before the final `@media` block)

**Interfaces:**
- N/A — static content only, no functions/APIs.

- [ ] **Step 1: Insert the three new sections into `site/index.html`**

Replace:

```html
      <p class="caveat">You'll need to build your own dataset before use — the game files are copyrighted and never distributed. See the <a href="https://github.com/BrendanL79/spud-coach#building-the-dataset">README</a> for how.</p>
    </section>
  </main>
```

with:

```html
      <p class="caveat">You'll need to build your own dataset before use — the game files are copyrighted and never distributed. See the <a href="https://github.com/BrendanL79/spud-coach#building-the-dataset">README</a> for how.</p>
    </section>

    <section class="section">
      <h2>Build your dataset</h2>
      <p>The game's data files are copyrighted, so nothing pre-built ships with Spud Coach — you generate <code>data/brotato.json</code> yourself, once, from your own Brotato install.</p>
      <pre class="install-code"><code>uv run python build_dataset.py</code></pre>
      <p class="caveat">Needs a local extraction first — see <a href="https://github.com/BrendanL79/spud-coach/blob/main/docs/extraction-setup.md">extraction-setup.md</a>. Game version and build timestamp are auto-detected; re-run after each game patch to refresh your local copy.</p>
    </section>

    <section class="section">
      <h2>Connect it to Claude</h2>
      <h3>Claude Code</h3>
      <pre class="install-code"><code>claude mcp add brotato-coach -- uv run --directory /path/to/spud-coach python -m brotato_coach.server</code></pre>
      <h3>Claude Desktop</h3>
      <pre class="install-code"><code>{
  "mcpServers": {
    "spud-coach": {
      "command": "uvx",
      "args": ["spudcoach", "--data", "/path/to/brotato.json"]
    }
  }
}</code></pre>
      <p class="caveat">Add this to <code>claude_desktop_config.json</code>, then fully restart Claude Desktop. Hitting a "Git executable not found" error on Windows? See the <a href="https://github.com/BrendanL79/spud-coach#windows-git-executable-not-found-or-uvx-not-found">README</a>.</p>
    </section>

    <section class="section">
      <h2>What you get</h2>
      <h3>Data lookups</h3>
      <ul>
        <li><code>get_weapon</code> / <code>get_item</code> / <code>get_character</code> — full records: stats, effects, kit</li>
        <li><code>get_weapon_class_set</code> — set bonuses for a weapon class</li>
        <li><code>list_weapons</code> / <code>list_items</code> — filtered summaries</li>
        <li><code>get_filter_options</code> — valid filter values (tags, archetypes, tiers, classes)</li>
      </ul>
      <h3>DPS &amp; comparison</h3>
      <ul>
        <li><code>weapon_dps</code> — one weapon's realized DPS at your stats</li>
        <li><code>compare_weapons</code> — rank several weapons by DPS</li>
        <li><code>compare_merge_paths</code> — which tier-merge order wins, and where it flips</li>
      </ul>
      <h3>Build evaluation</h3>
      <ul>
        <li><code>evaluate_item_for_build</code> — live / wasted / harmful verdict for an item</li>
        <li><code>loadout_set_bonuses</code> — set-bonus progress across a whole loadout</li>
        <li><code>explain_stat</code> — a stat's real mechanics (caps, dead-weight ranges)</li>
        <li><code>stat_display_value</code> — raw stat &rarr; what the game displays</li>
      </ul>
      <h3>Run analysis</h3>
      <ul>
        <li><code>evaluate_run</code> — post-mortem a whole run.json in one call</li>
        <li><code>check_dataset_version</code> — which game version the facts are from</li>
      </ul>
    </section>
  </main>
```

- [ ] **Step 2: Add the new CSS rules to `site/style.css`**

Replace:

```css
.disclaimer {
  max-width: 640px;
  margin: 0 auto;
  padding: 24px 24px 48px;
  color: var(--muted);
  font-size: 0.8rem;
  text-align: center;
}

@media (max-width: 480px) {
```

with:

```css
.disclaimer {
  max-width: 640px;
  margin: 0 auto;
  padding: 24px 24px 48px;
  color: var(--muted);
  font-size: 0.8rem;
  text-align: center;
}

.section h3 {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 1rem;
  color: var(--heading);
  margin: 20px 0 8px;
}

.section h3:first-of-type {
  margin-top: 0;
}

.section ul {
  margin: 0 0 0 18px;
  padding: 0;
  font-size: 0.95rem;
}

.section li {
  margin-bottom: 6px;
}

.section li code {
  background: var(--code-bg);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: 'Space Mono', monospace;
  font-size: 0.85rem;
  color: var(--heading);
}

@media (max-width: 480px) {
```

- [ ] **Step 3: Validate the HTML is well-formed**

Run:

```bash
uvx --with html5validator html5validator --root site --show-warnings 2>&1 || echo "html5validator unavailable, falling back to structural check"
```

If `html5validator` isn't available, the structural checks in Step 4 cover the essentials instead.

- [ ] **Step 4: Confirm every required section, snippet, and tool name is present**

Run:

```bash
grep -c "<h2>Build your dataset</h2>" site/index.html
grep -c "<h2>Connect it to Claude</h2>" site/index.html
grep -c "<h2>What you get</h2>" site/index.html
grep -c "uv run python build_dataset.py</code>" site/index.html
grep -c "claude mcp add brotato-coach" site/index.html
grep -c '"command": "uvx"' site/index.html
```

Expected: each prints `1` — confirms the three new `<h2>` headings and the three code snippets (bare dataset command, Claude Code one-liner, Claude Desktop config) are present exactly once, not paraphrased or dropped.

Run:

```bash
grep -oE '<code>(get_weapon|get_item|get_character|get_weapon_class_set|list_weapons|list_items|get_filter_options|weapon_dps|compare_weapons|compare_merge_paths|evaluate_item_for_build|loadout_set_bonuses|explain_stat|stat_display_value|evaluate_run|check_dataset_version)</code>' site/index.html | sort -u | wc -l
```

Expected: `16` — confirms all 16 MCP tool names from `brotato_coach/server.py` appear as distinct `<code>` entries (catches a dropped or misspelled tool name).

Run:

```bash
grep -c "\.section h3 {" site/style.css
grep -c "\.section li code {" site/style.css
```

Expected: each prints `1` — confirms the new CSS rules landed.

- [ ] **Step 5: Note the visual-verification gap**

There is no browser tool available in this session to render the page, so verification here is structural only (Steps 3-4). Before this ships, open `site/index.html` directly in a browser to confirm: the three new sections render with correct spacing, the `<h3>` sub-labels are visually distinct from the `<h2>` section titles but don't compete with them, the tool-list `<ul>`s are readable, and the page still looks correct at the existing 480px mobile breakpoint. Do not claim the page "looks correct" without having seen it rendered.

- [ ] **Step 6: Commit**

```bash
git add site/index.html site/style.css
git commit -m "feat(site): add dataset-build, Claude-connect, and tool-list sections"
```
