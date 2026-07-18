---
name: quelltest
description: >
  Find untested edge cases in Python code and write pytest tests proven to
  catch real bugs. Quelltest reads specs already in the code (docstrings,
  Pydantic models, type hints), generates a test per gap, verifies each
  through a 5-gate pipeline (Gate 5 injects the violation and requires the
  test to fail), and writes only proven tests to disk. Use after writing or
  editing Python code, before committing, when the user asks about test
  coverage, edge cases, production readiness, or wants a bug reproduced as a
  failing test. Triggers on: edge cases, untested, test coverage, prove
  tests, PRS, production readiness, reproduce bug, write tests, quelltest,
  quell.
user-invocable: true
argument-hint: "[find|fix|score|prove|reproduce] [path or description]"
license: MIT
metadata:
  author: quelltest
  version: "2.1.0"
  category: testing
---

# Quelltest: Proven Tests for Python

**Invocation:** `/quelltest $1 $2` where `$1` is the command and `$2` is a
path (or a bug description for `reproduce`).

| Command | What it does |
|---------|-------------|
| `/quelltest find [path]` | Scan for documented requirements with no test (read-only) |
| `/quelltest fix [path]` | Write Gate-5-proven pytest tests for every gap |
| `/quelltest score` | Project Production Readiness Score (0-100 + tier) |
| `/quelltest prove <file> [fn]` | Coverage ratio for one file or function |
| `/quelltest reproduce "<bug>"` | Turn a bug description into a verified failing test |

## How to run it

**Prefer the MCP tools** when an MCP server named `quelltest` is available in
this session: `find_edge_cases`, `write_verified_tests`, `get_prs_score`,
`prove_file`, `reproduce_bug`. They return structured JSON and run in-process.

**Fall back to the CLI** via Bash when the MCP server is not configured:

```bash
uv run quell find src/            # or: quell find src/
uv run quell find src/ --fix
uv run quell score
uv run quell reproduce "payment accepts zero amount"
```

If neither is available, install first: `pip install quelltest` (add
`"quelltest[mcp]"` for the MCP server) — then offer to register it:

```json
// .mcp.json in the project root
{ "mcpServers": { "quelltest": { "command": "quelltest-mcp" } } }
```

## Reading the output

Every requirement lands in exactly one bucket — never silently dropped:

- **WRITTEN** — passed all 5 gates, written to disk. Safe to commit as-is.
- **SCAFFOLDED** — needs state Quelltest can't fake (external APIs, DBs). A
  stub exists with the assertion sketched; finish it or mock the dependency.
- **FLAGGED** — no automatable test path; comes with file:line and a one-line
  reason. Fix testability (e.g. mock the external call), then re-run fix.

Gate 5 is the trust anchor: the violation was injected into the source and
the test failed against it, so the test provably catches the bug it claims
to catch. Do not second-guess WRITTEN tests by rewriting them.

## Daily workflows (use these proactively)

1. **After writing/editing a Python function** — run `find` on the changed
   file. If gaps appear, run `fix` on that file and show the user the
   written/scaffolded/flagged summary.
2. **Before a commit or PR** — run `score`; if below the project threshold
   (default 80), run `fix` on the worst files first, then report the delta.
3. **When the user reports a bug** — run `reproduce` with their description
   scoped to the suspect file; a verified failing test is the best bug report.
4. **When FLAGGED items block coverage** — read the reason, refactor for
   testability (inject dependencies, isolate I/O), and re-run `fix`.

## Ground rules

- Never mark a SCAFFOLDED stub as done without a real assertion.
- Never delete or weaken a WRITTEN test to raise the score.
- Everything runs locally: no network, no API key, no code leaves the machine.
- CI gate: `quell ci src/ --threshold 80` exits non-zero below threshold.

## Optional: auto-check hook (opt-in, not installed by default)

Add to `.claude/settings.json` to surface gaps after every Python edit:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "sh -c 'case \"$CLAUDE_TOOL_INPUT_FILE_PATH\" in *.py) quell find \"$CLAUDE_TOOL_INPUT_FILE_PATH\" 2>/dev/null | tail -5 ;; esac'"
          }
        ]
      }
    ]
  }
}
```
