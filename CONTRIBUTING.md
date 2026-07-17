# Contributing to Quelltest

Thanks for helping make Quelltest better. This guide covers setup, the
contribution workflow, and the invariants that keep the tool trustworthy.

By participating you agree to our [Code of Conduct](CODE_OF_CONDUCT.md).

## Quick links

- [Report a bug or extraction gap](https://github.com/quelltest/quelltest-lib/issues/new)
- [Good first issues](https://github.com/quelltest/quelltest-lib/labels/good%20first%20issue)
- [Architecture overview](CLAUDE.md)

## Dev setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# fork on GitHub first, then:
git clone https://github.com/<your-username>/quelltest-lib
cd quelltest-lib
uv sync --dev

# the suite must be green before you branch
uv run pytest tests/ -v

# lint + types — CI enforces both
uv run ruff check . --fix
uv run mypy quell/
```

Try your build against the bundled fixture project:

```bash
uv run quell find tests/fixtures/sample_project/src/
```

## What to contribute

The highest-value contributions, in order:

1. **Extraction gap reports.** A docstring pattern, Pydantic constraint, or type
   annotation Quell should have turned into a requirement but didn't. File an
   issue with a minimal snippet — even without a fix, these are gold.
2. **New spec readers** (see below).
3. **New ConstraintKind rules** (see below).
4. **Docs** — typos, missing examples, unclear explanations.

## Adding a spec reader

Spec readers turn existing artifacts (docstrings, models, schemas) into
`Requirement` objects.

1. Create `quell/spec/<name>_reader.py` implementing the `SpecReader` protocol.
2. Add it to `quell/spec/__init__.py` exports.
3. Wire it into the `_check()` method in `sdk.py`.
4. Add unit tests in `tests/unit/test_<name>_reader.py`.

**The reader contract:** a reader returns `[]` on any error. It never raises.
A reader that can crash `quell find` will not be merged.

## Adding a ConstraintKind

Each `ConstraintKind` teaches the rule engine a new class of requirement — and
teaches Gate 5 how to violate it.

1. Add the enum value to `ConstraintKind` in `core/models.py`.
2. Add the generation rule in `rule_engine.py` (`generate()` and `can_handle()`).
3. Add the violation injection in `verifier.py` (`_violate()`).
4. Add tests in `tests/unit/test_rule_engine.py`.

All four steps are required — a rule without a Gate 5 injection can't be proven
and won't ship.

## Hard invariants — never violate these

These are the properties users rely on. PRs that weaken them will be declined
regardless of the feature they enable:

1. `verifier.py` ALWAYS restores source files in a `finally` block.
2. `writer.py` ALWAYS backs up before writing and restores on failure.
3. `writer.py` ALWAYS validates the CST parses before writing to disk.
4. No source code is transmitted anywhere except the user-configured LLM
   provider — and any outbound payload must pass through `quell/sync/sanitizer.py`.
5. The LLM is only called when the rule engine can't handle a case.
6. Spec readers return `[]` on error — never raise.
7. pytest always runs in a subprocess, never in-process.
8. The coverage checker marks uncertain cases as uncovered.

## Pull request checklist

- [ ] Branched from `master`, one logical change per PR
- [ ] `uv run pytest tests/ -v` green
- [ ] `uv run ruff check .` and `uv run mypy quell/` clean
- [ ] New behavior has tests; changed behavior has updated tests
- [ ] Public functions have docstrings
- [ ] Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, …)

## Reporting security issues

Do **not** open a public issue for security vulnerabilities. Email
security@quelltest.com and we'll respond within 48 hours.

## License

By contributing, you agree that your contributions are licensed under the MIT
License that covers this project.
