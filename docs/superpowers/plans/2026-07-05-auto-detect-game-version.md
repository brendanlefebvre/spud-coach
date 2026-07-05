# Auto-detect game version + default generated_at Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `build_dataset.py --game-version` and `--generated-at` optional — auto-detecting the game version from the decompiled `recovered/singletons/progress_data.gd` and defaulting `generated_at` to the current UTC time — while keeping both flags available as explicit overrides.

**Architecture:** Two new pure-function builder modules (`brotato_coach/builders/version.py`, `brotato_coach/builders/timestamps.py`), following the existing `builders/localization.py` pattern (parse/format text or a datetime, no file I/O or clock access inside the function itself). `build_dataset.py`'s `main()` does the file read and clock read, then resolves each value: explicit CLI flag wins if given, otherwise auto-detect/default, with a hard `parser.error` only for game version (no auto-source ever fails for `generated_at`, since "now" always exists).

**Tech Stack:** Python 3.11+, `argparse`, `re`, `datetime`, `pytest`.

## Global Constraints

- An explicitly-passed `--game-version` or `--generated-at` always overrides auto-detection/the default — never the other way around.
- If `--game-version` is omitted and `--version-file` (default `recovered/singletons/progress_data.gd`) is missing or doesn't contain a `VERSION` constant, `build_dataset.py` must fail via `parser.error(...)`, same as today's `required=True` failure mode, just pointing at `--version-file` in the message.
- `--generated-at` has no failure path — if omitted, it defaults to `datetime.now(timezone.utc)` formatted as `"%Y-%m-%dT%H:%M:%SZ"` (e.g. `"2026-07-05T12:34:56Z"`).
- New builder modules stay pure: `brotato_coach/builders/version.py`'s `parse_game_version(text)` takes text and does no file I/O; `brotato_coach/builders/timestamps.py`'s `format_generated_at(dt)` takes a `datetime` and does no clock reads. All I/O and clock access stays in `build_dataset.py`'s `main()`.
- New tests follow the existing `test_build_<module>.py` naming convention and require no real `recovered/` checkout (this worktree doesn't have one — it's gitignored).
- `brotato_coach/dataset.py`'s `assemble_dataset(game_version=..., generated_at=...)` signature is unchanged — this plan only changes how `build_dataset.py` obtains those two string values.

---

### Task 1: `parse_game_version` in a new `brotato_coach/builders/version.py`

**Files:**
- Create: `brotato_coach/builders/version.py`
- Test: `tests/test_build_version.py`

**Interfaces:**
- Produces: `parse_game_version(text: str) -> str | None` — extracts the `VERSION` constant from `progress_data.gd` source text; returns `None` if not present. Consumed by Task 3.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_build_version.py`:

```python
from brotato_coach.builders.version import parse_game_version

PROGRESS_DATA_GD = '''extends Node

const VERSION = "1.1.15.4"
const VERSION_SWITCH = "1.1.13.2"

var settings := {}
'''


def test_parse_game_version_finds_version_constant():
    assert parse_game_version(PROGRESS_DATA_GD) == "1.1.15.4"


def test_parse_game_version_returns_none_when_absent():
    assert parse_game_version("extends Node\nvar x = 1\n") is None


def test_parse_game_version_ignores_version_switch_only():
    text = 'extends Node\nconst VERSION_SWITCH = "1.1.13.2"\n'
    assert parse_game_version(text) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_build_version.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'brotato_coach.builders.version'`

- [ ] **Step 3: Write the minimal implementation**

Create `brotato_coach/builders/version.py`:

```python
"""Extract the game's VERSION constant from the decompiled progress_data.gd singleton."""

from __future__ import annotations

import re

_VERSION_RE = re.compile(r'const VERSION\s*=\s*"([^"]+)"')


def parse_game_version(text: str) -> str | None:
    """Extract the VERSION constant from progress_data.gd source text.

    Returns None if the constant isn't present (e.g. the singleton's format changed).
    """
    m = _VERSION_RE.search(text)
    return m.group(1) if m else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_build_version.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add brotato_coach/builders/version.py tests/test_build_version.py
git commit -m "feat: add parse_game_version for auto-detecting the game version"
```

---

### Task 2: `format_generated_at` in a new `brotato_coach/builders/timestamps.py`

**Files:**
- Create: `brotato_coach/builders/timestamps.py`
- Test: `tests/test_build_timestamps.py`

**Interfaces:**
- Produces: `format_generated_at(dt: datetime) -> str` — formats a UTC `datetime` as `"%Y-%m-%dT%H:%M:%SZ"`. Consumed by Task 3.

- [ ] **Step 1: Write the failing test**

Create `tests/test_build_timestamps.py`:

```python
from datetime import datetime, timezone

from brotato_coach.builders.timestamps import format_generated_at


def test_format_generated_at_matches_iso8601_with_z_suffix():
    dt = datetime(2026, 7, 5, 12, 34, 56, tzinfo=timezone.utc)
    assert format_generated_at(dt) == "2026-07-05T12:34:56Z"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_build_timestamps.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'brotato_coach.builders.timestamps'`

- [ ] **Step 3: Write the minimal implementation**

Create `brotato_coach/builders/timestamps.py`:

```python
"""Format the build timestamp stamped into the dataset as generated_at."""

from __future__ import annotations

from datetime import datetime


def format_generated_at(dt: datetime) -> str:
    """Format a UTC datetime as the ISO8601 form used for generated_at, e.g. '2026-07-05T12:34:56Z'."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_build_timestamps.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add brotato_coach/builders/timestamps.py tests/test_build_timestamps.py
git commit -m "feat: add format_generated_at for defaulting the build timestamp"
```

---

### Task 3: Wire both into `build_dataset.py` and update docs

**Files:**
- Modify: `build_dataset.py:1-40`
- Modify: `README.md:34-38,54-57,207-225`
- Modify: `CLAUDE.md` (project file, "Build & test" section)

**Interfaces:**
- Consumes: `parse_game_version` from Task 1, `format_generated_at` from Task 2.

- [ ] **Step 1: Update `build_dataset.py`'s module docstring and imports**

In `build_dataset.py`, replace lines 1-22:

```python
"""Distill extracted/ .tres game data into data/brotato.json.

Usage:
    python build_dataset.py --extracted extracted --out data/brotato.json \
        --game-version 1.1.0.0 --generated-at 2026-07-01T00:00:00Z
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from brotato_coach import dataset
from brotato_coach.builders import discover
from brotato_coach.builders.weapons import build_weapon_record
from brotato_coach.builders.items import build_item_record
from brotato_coach.builders.characters import build_character_record
from brotato_coach.builders.sets import build_set_record
from brotato_coach.builders.localization import parse_translations_csv
from brotato_coach.tres import parse_tres
```

with:

```python
"""Distill extracted/ .tres game data into data/brotato.json.

Usage:
    python build_dataset.py --extracted extracted --out data/brotato.json

--game-version and --generated-at are both optional: game version auto-detects from
--version-file (default recovered/singletons/progress_data.gd), and generated_at defaults
to the current UTC time. Pass either explicitly to override, e.g. for a pinned/reproducible
build.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from brotato_coach import dataset
from brotato_coach.builders import discover
from brotato_coach.builders.weapons import build_weapon_record
from brotato_coach.builders.items import build_item_record
from brotato_coach.builders.characters import build_character_record
from brotato_coach.builders.sets import build_set_record
from brotato_coach.builders.localization import parse_translations_csv
from brotato_coach.builders.version import parse_game_version
from brotato_coach.builders.timestamps import format_generated_at
from brotato_coach.tres import parse_tres
```

- [ ] **Step 2: Make the two CLI args optional and add `--version-file`**

Replace:

```python
    parser.add_argument("--game-version", required=True)
    parser.add_argument("--generated-at", required=True)
```

with:

```python
    parser.add_argument(
        "--game-version", default=None,
        help="override the auto-detected version; auto-detected from --version-file if omitted")
    parser.add_argument(
        "--generated-at", default=None,
        help="override the build timestamp; defaults to the current UTC time if omitted")
    parser.add_argument(
        "--version-file",
        default="recovered/singletons/progress_data.gd",
        help="decompiled Godot singleton providing the VERSION constant; "
             "used when --game-version is omitted")
```

- [ ] **Step 3: Resolve both values right after parsing args**

Immediately after `args = parser.parse_args(argv)`, insert:

```python
    game_version = args.game_version
    if game_version is None:
        if os.path.isfile(args.version_file):
            game_version = parse_game_version(_read(args.version_file))
        if game_version is None:
            parser.error(
                f"could not detect game version from {args.version_file}; "
                "pass --game-version explicitly")

    generated_at = args.generated_at
    if generated_at is None:
        generated_at = format_generated_at(datetime.now(timezone.utc))
```

- [ ] **Step 4: Use the resolved values instead of the raw args**

Replace:

```python
    ds = dataset.assemble_dataset(
        game_version=args.game_version, generated_at=args.generated_at,
        weapons=weapons, items=items, characters=characters, sets=sets)
```

with:

```python
    ds = dataset.assemble_dataset(
        game_version=game_version, generated_at=generated_at,
        weapons=weapons, items=items, characters=characters, sets=sets)
```

- [ ] **Step 5: Run the full test suite**

Run: `uv run pytest -v`
Expected: all previously-passing tests still pass (89 tests before this plan's new ones; +4 from Tasks 1-2). No test references `build_dataset.py`'s CLI directly, so none should break.

- [ ] **Step 6: Manually verify the new CLI behavior**

This worktree has no `recovered/` checkout (gitignored), so these commands exercise the *missing-file* and *default* paths without needing real game data.

Run: `uv run python build_dataset.py --help`
Expected: `--game-version`, `--generated-at`, and `--version-file` all appear as optional (no `(required)` marker), with the help text written in Step 2.

Run: `uv run python build_dataset.py --generated-at 2026-01-01T00:00:00Z`
Expected: exits with an argparse error (exit code 2) whose message contains `could not detect game version from recovered/singletons/progress_data.gd; pass --game-version explicitly` — confirms the hard-error path fires when `--game-version` is omitted and the version file is absent.

Run: `uv run python build_dataset.py --game-version 1.1.15.4`
Expected: does **not** raise any error about a missing `--generated-at`. Since this worktree has
no real `extracted/` directory, `glob`-based discovery finds zero weapons/items/characters/sets
(glob on a missing path returns `[]`, not an error) and `validate_dataset` has nothing to object
to, so the command actually **succeeds**, printing `Wrote data/brotato.json: 0 weapon records, 0
item records, 0 character records, 0 set records (NO translations found — slug names only)` and
writing a near-empty `data/brotato.json` (harmless — gitignored, not real data). The point of
this check is only that no argparse error fires over the omitted `--generated-at`.

- [ ] **Step 7: Update `README.md`'s Quick start example**

Replace (lines 34-38):

```markdown
```bash
uv run python build_dataset.py --game-version 1.1.15.4 \
    --generated-at $(date -u +%Y-%m-%dT%H:%M:%SZ)     # writes data/brotato.json
uv run python -m brotato_coach.server                 # starts the MCP server over stdio
```
```

with:

```markdown
```bash
uv run python build_dataset.py                        # writes data/brotato.json
uv run python -m brotato_coach.server                 # starts the MCP server over stdio
```
```

- [ ] **Step 8: Update `README.md`'s Run section**

Replace (lines 54-57):

```markdown
The dataset is never distributed — build your own from your Brotato install:
`uv run python build_dataset.py --game-version <ver> --generated-at <iso8601>`
(see [docs/extraction-setup.md](docs/extraction-setup.md)). `SPUDCOACH_DATA` works as an env-var alternative
to `--data`.
```

with:

```markdown
The dataset is never distributed — build your own from your Brotato install:
`uv run python build_dataset.py` (see [docs/extraction-setup.md](docs/extraction-setup.md)).
Game version auto-detects from the decompiled `recovered/singletons/progress_data.gd`, and
`generated_at` defaults to the current UTC time — pass `--game-version`/`--generated-at`
explicitly to override either. `SPUDCOACH_DATA` works as an env-var alternative to `--data`.
```

- [ ] **Step 9: Update `README.md`'s "Building the dataset" section**

Replace (lines 207-225):

```markdown
macOS / Linux (bash):

```bash
uv run python build_dataset.py \
    --game-version 1.1.15.4 \
    --generated-at $(date -u +%Y-%m-%dT%H:%M:%SZ)
```

Windows (PowerShell):

```powershell
uv run python build_dataset.py `
    --game-version 1.1.15.4 `
    --generated-at (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
```

This writes `data/brotato.json`. Supply the actual installed Brotato version to `--game-version`
(it is not recorded inside the `.pck`; check the Steam client). Re-run after each patch to refresh
your local copy — it stays gitignored, so don't commit it.
```

with:

```markdown
```bash
uv run python build_dataset.py
```

This writes `data/brotato.json`. Game version auto-detects from the decompiled
`recovered/singletons/progress_data.gd` (its `VERSION` constant), and `generated_at` defaults to
the current UTC time. Pass `--game-version <ver>` or `--generated-at <iso8601>` explicitly to
override either — e.g. if `recovered/` isn't present, or to pin a reproducible value for a test
or release script. Re-run after each patch to refresh your local copy — it stays gitignored, so
don't commit it.
```

(This also drops the separate macOS/Linux vs. Windows command blocks — the old split existed only because of shell-specific date substitution for `--generated-at`, which is no longer needed.)

- [ ] **Step 10: Update the project `CLAUDE.md`'s "Build & test" section**

Replace:

```markdown
## Build & test
- Python 3.11+, managed with **uv**. `uv sync` to set up; `uv run pytest` to test
  (TDD is the norm — write the failing test first).
- Build the dataset: `uv run python build_dataset.py --game-version <ver> --generated-at <iso8601>`.
  Both args are **required** — `generated_at` is passed in, never read from a clock, so builds
  stay reproducible.
- Run the MCP server: `uv run python -m brotato_coach.server` (cwd must be the repo root).
```

with:

```markdown
## Build & test
- Python 3.11+, managed with **uv**. `uv sync` to set up; `uv run pytest` to test
  (TDD is the norm — write the failing test first).
- Build the dataset: `uv run python build_dataset.py`. `--game-version` auto-detects from
  `recovered/singletons/progress_data.gd`'s `VERSION` constant; `--generated-at` defaults to the
  current UTC time. Pass either explicitly to override (e.g. a pinned/reproducible build).
- Run the MCP server: `uv run python -m brotato_coach.server` (cwd must be the repo root).
```

- [ ] **Step 11: Commit**

```bash
git add build_dataset.py README.md CLAUDE.md
git commit -m "feat: auto-detect game version and default generated_at in build_dataset.py"
```

---

## Not in this plan

- Updating the landing page's not-yet-implemented "Build your dataset" section (`docs/superpowers/specs/2026-07-05-landing-page-content-expansion-design.md`) to drop the now-unnecessary `--game-version`/`--generated-at` flags from its example command — that's a separate, already-approved spec; its own implementation plan should reflect the simplified command when it's written.
