# Quell Spec 9 — Local-First Agentic Integration (the pivot)

> Status: ACTIVE. Supersedes the cloud-connector positioning of spec8 §11.
> The cloud connector (mcp.quelltest.com) is parked, not deleted — see §6.

## 1. The pivot in one paragraph

Spec8 built a **remote** MCP connector: Claude.ai reads PRS reports from a
cloud dashboard. That makes Claude a *spectator* of Quelltest. This spec makes
Claude an *operator* of Quelltest: a *local* stdio MCP server ships inside the
pip package, so any agent (Claude Code, Claude Desktop, Cursor, Devin) can run
`find / fix / score / reproduce / prove` directly against the repo it is
working in — no terminal, no cloud, no OAuth, no sync. The privacy story
becomes absolute: nothing leaves the machine because there is no remote end.

## 2. Why this is the right surface (research summary, July 2026)

- MCP is the standard: ~97M monthly SDK downloads; every major provider
  adopted it. FastMCP (bundled in the official `mcp` Python SDK) powers ~70%
  of MCP servers; stdio is the default transport for local dev tools spawned
  by Claude Code / Claude Desktop.
- The dominant pattern for dev tools is exactly this: a console script the
  client spawns (`command: "quelltest-mcp"`), declared in `.mcp.json`.
- Claude Code plugins (skills + hooks + agents + MCP bundles, distributed via
  `/plugin marketplace add owner/repo`) are the standard way to teach Claude
  a tool's workflow. `claude-seo` is the reference implementation we follow.
- Agentic loop this enables: Claude writes code → calls
  `write_verified_tests` → Gate-5-proven tests land next to the change →
  Claude reads FLAGGED reasons and fixes testability — all inside one session.

## 3. Surface 1 — `quell/mcp_server.py` (rewrite, ships in the wheel)

Old file was v0.2 (mutation-era, broken API mix). Full rewrite on the
official SDK's FastMCP.

Install / run:

```bash
pip install "quelltest[mcp]"
quelltest-mcp            # console script, stdio
python -m quell.mcp_server   # equivalent
quell mcp                # CLI alias
```

`.mcp.json` (per-project, what Claude Code reads):

```json
{
  "mcpServers": {
    "quelltest": { "command": "quelltest-mcp" }
  }
}
```

Tools (all sync — FastMCP runs them in a worker thread, which keeps the
SDK's internal `asyncio.run()` legal; all return JSON dicts; never raise —
errors come back as `{"error": ...}`):

| Tool | Wraps | Returns |
|---|---|---|
| `find_edge_cases(path, sources?)` | `Quell.check(fix=False)` | coverage %, uncovered requirements (id, kind, function, file:line, description) |
| `write_verified_tests(path)` | `Quell.check(fix=True)` | written/scaffolded/flagged counts + names, report path |
| `get_prs_score()` | `Quell.score()` | PRS + tier + per-file breakdown |
| `prove_file(file, function?)` | `Quell.prove()` | coverage ratio for one file/function |
| `reproduce_bug(description, file?)` | `Quell.reproduce()` | whether a verified failing test was written |

Invariants preserved: pytest stays in subprocess (SDK already does);
verifier restore-in-finally untouched; readers never raise; no network.

## 4. Surface 2 — Claude Code plugin (repo root, claude-seo pattern)

```
.claude-plugin/plugin.json        name: quelltest
.claude-plugin/marketplace.json   → /plugin marketplace add quelltest/quelltest-lib
skills/quelltest/SKILL.md         /quelltest [find|fix|score|reproduce|prove]
```

The skill teaches Claude: prefer the MCP tools when the `quelltest` server is
configured; otherwise fall back to the CLI via Bash. It also carries the
daily-workflow recipes: "after writing a feature, run fix on changed files";
"before opening a PR, run score and paste the delta".

Hooks: **not auto-installed in v1** (a PostToolUse hook on every .py edit is
too hot). The skill documents an opt-in hook recipe instead.

## 5. Surface 3 — existing CI surface (unchanged)

`quell ci --threshold N` + GitHub Action remain the non-interactive gate.

## 6. What happens to the spec8 cloud connector

Parked. `connector/` and mcp.quelltest.com stay deployable for the dashboard
story, but the website/README lead with the local server. No new work.

## 7. Version

Ships as **quelltest 2.1.0** (minor: new public surface, no breaking change).
