"""Quell local MCP server — lets AI agents operate Quelltest directly (spec9 §3).

Claude Code, Claude Desktop, Cursor, or any MCP client spawns this over stdio
and can find untested edge cases, write Gate-5-verified tests, score the
project, and reproduce bugs — against the local working tree, with no cloud,
no OAuth, and no network. Nothing leaves the machine.

Run:
    quelltest-mcp              # console script (stdio)
    python -m quell.mcp_server # equivalent
    quell mcp                  # CLI alias

Register in a project's .mcp.json:
    {"mcpServers": {"quelltest": {"command": "quelltest-mcp"}}}

Requires:
    pip install "quelltest[mcp]"

Tool implementations are plain functions (testable without the mcp package);
FastMCP registration happens only inside create_server()/main(). Tools are
sync on purpose: FastMCP executes sync tools in a worker thread, which keeps
the SDK's internal asyncio.run() calls legal.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# ── tool implementations (no mcp dependency) ─────────────────────────────────


def _root() -> Path:
    """Project root = the directory the MCP client spawned us in."""
    return Path.cwd().resolve()


def _resolve_target(path: str, root: Path) -> Path | None:
    """Resolve a user/agent-supplied path inside the project root."""
    candidate = Path(path) if Path(path).is_absolute() else root / path
    candidate = candidate.resolve()
    if not candidate.exists():
        return None
    return candidate


def _requirement_dict(req: Any) -> dict[str, Any]:
    return {
        "id": req.id,
        "description": req.description,
        "constraint_kind": req.constraint_kind.value,
        "function": req.target_function,
        "file": str(req.target_file),
        "line": req.source_line,
        "covered": req.is_covered,
    }


def impl_find_edge_cases(
    path: str = ".",
    sources: list[str] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Scan for testable requirements and report which have no test (read-only)."""
    root = root or _root()
    target = _resolve_target(path, root)
    if target is None:
        return {"error": f"Path not found: {path}"}
    try:
        from quell.sdk import Quell

        result = Quell(project_root=root).check(target, sources=sources, fix=False)
        uncovered = [_requirement_dict(r) for r in result.uncovered]
        return {
            "total_requirements": len(result.requirements),
            "covered": len(result.covered),
            "uncovered": len(uncovered),
            "coverage_percent": round(result.score * 100, 1),
            "gaps": uncovered,
            "note": "Run write_verified_tests to generate Gate-5-proven tests for these gaps.",
        }
    except Exception as exc:  # noqa: BLE001 — tools must never raise into the transport
        return {"error": f"{type(exc).__name__}: {exc}"}


def impl_write_verified_tests(path: str = ".", root: Path | None = None) -> dict[str, Any]:
    """Generate tests for every gap, verify through all 5 gates, write only proven ones."""
    root = root or _root()
    target = _resolve_target(path, root)
    if target is None:
        return {"error": f"Path not found: {path}"}
    try:
        from quell.sdk import Quell

        result = Quell(project_root=root).check(target, fix=True)
        summary: dict[str, Any] = {
            "total_requirements": len(result.requirements),
            "coverage_percent_after": round(result.score * 100, 1),
            "report_path": str(result.report_path) if result.report_path else None,
        }
        if result.report_path and Path(result.report_path).exists():
            try:
                report = json.loads(Path(result.report_path).read_text(encoding="utf-8"))
                for key in (
                    "written",
                    "already_covered",
                    "fails_on_correct",
                    "doesnt_catch_violation",
                    "timeout",
                    "error",
                    "skipped",
                ):
                    if key in report:
                        summary[key] = report[key]
            except Exception:  # noqa: BLE001 — summary without bucket detail is still useful
                pass
        summary["note"] = (
            "Only tests that passed all 5 gates (including Gate 5: violation "
            "injection) were written to disk. Others were discarded, never written."
        )
        return summary
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def impl_get_prs_score(root: Path | None = None) -> dict[str, Any]:
    """Project-wide requirement-coverage score with per-file breakdown."""
    root = root or _root()
    try:
        from quell.sdk import Quell

        score = Quell(project_root=root).score()
        pct = score.percentage
        tier = (
            "Production Ready" if pct >= 80
            else "Review Needed" if pct >= 60
            else "Needs Work"
        )
        return {
            "score_percent": pct,
            "tier": tier,
            "files": [
                {
                    "file": str(getattr(f, "path", getattr(f, "file", ""))),
                    "total_requirements": f.total_requirements,
                    "covered_requirements": f.covered_requirements,
                }
                for f in score.files
            ],
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def impl_prove_file(
    file: str,
    function: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Requirement-coverage ratio for a single file (optionally one function)."""
    root = root or _root()
    target = _resolve_target(file, root)
    if target is None:
        return {"error": f"File not found: {file}"}
    try:
        from quell.sdk import Quell

        ratio = Quell(project_root=root).prove(target, function=function)
        return {
            "file": str(target),
            "function": function,
            "coverage_percent": round(ratio * 100, 1),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def impl_reproduce_bug(
    description: str,
    file: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Turn a natural-language bug description into a verified failing test."""
    root = root or _root()
    target: Path | None = None
    if file is not None:
        target = _resolve_target(file, root)
        if target is None:
            return {"error": f"File not found: {file}"}
    try:
        from quell.sdk import Quell

        written = Quell(project_root=root).reproduce(description, file=target)
        return {
            "test_written": written,
            "note": (
                "A failing test proving the bug was written to disk."
                if written
                else "Could not produce a verified failing test for this description."
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


# ── FastMCP registration ─────────────────────────────────────────────────────


def create_server() -> Any:
    """Build the FastMCP server. Raises ImportError if mcp is not installed."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(
        "quelltest",
        instructions=(
            "Quelltest finds untested edge cases in the current Python project "
            "and writes pytest tests proven (via violation injection) to catch "
            "real bugs. Typical flow: find_edge_cases -> write_verified_tests -> "
            "get_prs_score. Everything runs locally; no code leaves the machine."
        ),
    )

    @mcp.tool()
    def find_edge_cases(path: str = ".", sources: list[str] | None = None) -> dict:
        """Scan a file or directory for documented requirements (docstrings,
        Pydantic models, type hints) that have no test. Read-only — writes
        nothing. Returns the gap list with file and line locations."""
        return impl_find_edge_cases(path, sources)

    @mcp.tool()
    def write_verified_tests(path: str = ".") -> dict:
        """Generate a pytest test for every uncovered requirement under path,
        run each through the 5-gate pipeline (Gate 5 injects the violation and
        requires the test to fail), and write only proven tests to disk."""
        return impl_write_verified_tests(path)

    @mcp.tool()
    def get_prs_score() -> dict:
        """Project-wide requirement-coverage score (0-100) with tier
        (Production Ready / Review Needed / Needs Work) and per-file detail."""
        return impl_get_prs_score()

    @mcp.tool()
    def prove_file(file: str, function: str | None = None) -> dict:
        """Coverage ratio for one file, optionally narrowed to one function.
        Use after editing a function to check whether its documented behavior
        is tested."""
        return impl_prove_file(file, function)

    @mcp.tool()
    def reproduce_bug(description: str, file: str | None = None) -> dict:
        """Convert a natural-language bug description into a verified failing
        pytest test (e.g. 'payment accepts zero amount'). Optionally scope to
        a file."""
        return impl_reproduce_bug(description, file)

    return mcp


def main() -> None:
    """Console-script entry point (stdio transport)."""
    try:
        server = create_server()
    except ImportError:
        print(
            "Error: the 'mcp' package is required for the Quelltest MCP server.\n"
            'Install it with: pip install "quelltest[mcp]"',
            file=sys.stderr,
        )
        sys.exit(1)
    server.run()  # stdio is FastMCP's default transport


if __name__ == "__main__":
    main()
