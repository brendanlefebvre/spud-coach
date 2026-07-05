# Auto-detect game version + default generated_at (build_dataset.py ergonomics)

## Goal

Two independent `build_dataset.py` ergonomics fixes, bundled into one spec/plan because they're
the same shape of change (a required CLI arg becomes optional-with-auto-default, explicit value
still always wins) and touch the same file.

**1. `--game-version`** is currently `required=True`, and the README tells users to "check the
Steam client" for the value because "it is not recorded inside the .pck." That's misleading:
`recovered/singletons/progress_data.gd` (decompiled GDScript, part of the existing `recovered/`
extraction) declares `const VERSION = "1.1.15.4"` — the game's own source of truth for its
version string. Read it from there by default instead of asking the user to supply it by hand.

**2. `--generated-at`** is currently `required=True` too, justified in project `CLAUDE.md` as
"passed in, never read from a clock, so builds stay reproducible." Tracing that rule to its
origin (`docs/superpowers/specs/2026-07-01-brotato-coach-design.md:105`) shows the *original*
reason was `"(sandbox blocks wall-clock calls in scripts)"` — a constraint on the AI-agent
environment that originally authored this project, not a real constraint on the shipped CLI
running on an end user's own machine. The "reproducibility" framing is a legitimate-sounding
justification bolted onto what was actually a category error. And the value it protects is
low here anyway: `data/brotato.json` is local-only, gitignored, and never diffed or published
across machines/builds — a fixed timestamp doesn't make two builds meaningfully "more
comparable." So: default it to the current UTC time, same explicit-override-always-wins pattern
as `--game-version`. Existing callers of `assemble_dataset()` (tests, `server.py`) already pass
`generated_at` as a plain string and are unaffected — this change is entirely in
`build_dataset.py`'s CLI layer.

## Design

### New module: `brotato_coach/builders/version.py`

One pure function, parallel to `builders/localization.py`'s `parse_translations_csv` (parses
text, does no file I/O):

```python
import re

_VERSION_RE = re.compile(r'const VERSION\s*=\s*"([^"]+)"')

def parse_game_version(text: str) -> str | None:
    """Extract the VERSION constant from progress_data.gd source text.

    Returns None if the constant isn't present (e.g. the singleton's format changed).
    """
    m = _VERSION_RE.search(text)
    return m.group(1) if m else None
```

### `build_dataset.py` changes — game version

- `--game-version` changes from `required=True` to `default=None` — an explicit override, not
  a mandatory input.
- New `--version-file` arg, `default="recovered/singletons/progress_data.gd"` — same pattern as
  the existing `--translations` default (a hardcoded path under `recovered/`, overridable, and
  tolerant of the file being absent).
- Resolution order in `main()`, replacing the direct `args.game_version` usage:

```python
game_version = args.game_version
if game_version is None:
    if os.path.isfile(args.version_file):
        game_version = parse_game_version(_read(args.version_file))
    if game_version is None:
        parser.error(
            f"could not detect game version from {args.version_file}; "
            "pass --game-version explicitly")
```

Precedence: an explicitly-passed `--game-version` always wins, even if the version file is
present and parses fine — this preserves the ability to build against a declared version other
than what's in a given `recovered/` checkout (e.g. testing). If neither source yields a version,
the build fails the same way it does today (a required value with no default), just pointed at
`--version-file` instead of `--game-version` in the error message.

### New module: `brotato_coach/builders/timestamps.py`

One pure function, same shape as `parse_game_version` — takes a `datetime`, returns a string,
no clock access inside it:

```python
from datetime import datetime

def format_generated_at(dt: datetime) -> str:
    """Format a UTC datetime as the ISO8601 form used for generated_at, e.g. '2026-07-05T12:34:56Z'."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
```

Keeping the clock read (`datetime.now(timezone.utc)`) out of this function and in
`build_dataset.py`'s `main()` instead means the formatting logic is testable without mocking the
system clock — same reasoning as keeping `parse_game_version` pure and doing file I/O in `main()`.

### `build_dataset.py` changes — generated_at

- `--generated-at` changes from `required=True` to `default=None`.
- Resolution order in `main()`:

```python
generated_at = args.generated_at
if generated_at is None:
    generated_at = format_generated_at(datetime.now(timezone.utc))
```

No error path here — unlike game version, there's always a fallback (the actual current time),
so this can never fail the way version detection can.

### Docs updates

- `README.md`'s "Building the dataset" section: both the Bash and PowerShell example commands
  drop to just `uv run python build_dataset.py` with no flags (both `--game-version` and
  `--generated-at` are now optional/auto-populated) — collapsing what were previously two
  separate platform-specific commands (needed only because of the `--generated-at` shell date
  substitution) into one identical command for both platforms. Add a sentence noting: game
  version is auto-detected from `recovered/singletons/progress_data.gd`, generated_at defaults
  to the current UTC time; both remain available as explicit-override flags (e.g. for pinning a
  reproducible value in a test or release script).
- Project `CLAUDE.md`'s build snippet updates from `uv run python build_dataset.py --game-version
  <ver> --generated-at <iso8601>` (with "Both args are **required**... so builds stay
  reproducible") to `uv run python build_dataset.py` (no required args), with a note that both
  values auto-populate and can still be pinned via `--game-version`/`--generated-at` for
  reproducible builds (e.g. CI, release scripts, or regenerating a byte-identical dataset for
  comparison).
- Downstream effect (not part of this task, tracked separately): the not-yet-implemented landing
  page "Build your dataset" section (`2026-07-05-landing-page-content-expansion-design.md`)
  currently shows a PowerShell command with `--game-version <your-installed-version>` and a
  `(Get-Date)...` `--generated-at` expression — that spec needs a follow-up edit to collapse to
  the bare `uv run python build_dataset.py` command once this change lands, since the whole
  point of those two flags in that draft was working around the exact manual-entry problems this
  task removes.

## Testing (TDD)

New `tests/test_build_version.py`, following the existing `test_build_<module>.py` convention:

- `parse_game_version` finds `"1.1.15.4"` in a real-shaped fixture string (`const VERSION =
  "1.1.15.4"` plus surrounding lines copied from the actual file's structure, e.g. the
  `VERSION_SWITCH` constant beneath it, to guard against a regex that's accidentally too greedy).
- `parse_game_version` returns `None` for text with no `VERSION` constant at all.
- `parse_game_version` returns `None` for a near-miss (e.g. `const VERSION_SWITCH = "..."` alone,
  no bare `VERSION`) — guards against the regex matching the wrong constant.

New `tests/test_build_timestamps.py`:

- `format_generated_at` on a fixed `datetime(2026, 7, 5, 12, 34, 56, tzinfo=timezone.utc)`
  returns exactly `"2026-07-05T12:34:56Z"`.

No test needs a real `recovered/` checkout — this worktree doesn't have one (it's gitignored),
and the functions under test take text/`datetime`, not paths or the live clock. The
`build_dataset.py` CLI wiring (file-exists check, `parser.error` fallback, the `datetime.now()`
call itself) is thin enough to be covered by inspection rather than a dedicated subprocess test,
consistent with `build_dataset.py` having no existing test file of its own today.

## Out of scope

- Changing `brotato_coach/dataset.py`'s `assemble_dataset(game_version=..., generated_at=...)`
  signature — it already just takes strings; where those strings come from is entirely
  `build_dataset.py`'s concern.
- Validating the detected version against any known-good list, or warning on version mismatches
  between `--extracted` and the detected value — out of scope for this fix.
- Any change to how `generated_at` or `game_version` are used downstream (`check_dataset_version`
  tool, schema) — this task only changes how the values are obtained at build time.
- Implementing the landing-page spec's follow-up edit — noted above, but that's a change to an
  already-approved separate spec, not part of this task.
