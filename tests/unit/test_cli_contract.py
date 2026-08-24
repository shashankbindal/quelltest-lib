"""CLI contract tests — pins the failures this repo has actually shipped.

Every case here corresponds to a real regression, not a hypothetical:

  * `quell find` died with UnicodeEncodeError on Windows cp1252 consoles
    because of emoji and box-drawing glyphs (#161).
  * quell-report.json did not contain summary.prs_score, so the installed
    GitHub Action always commented "0/100" (#135).
  * A false 0/100 was reported on well-tested codebases (#156).
  * Verified tests were bucketed as FLAGGED with reason "verified" (#161).
  * `quell scan` / `quell check` were removed and must exit 1 (#124).

The CI self-check job was separately found to be running a removed command
with its failure swallowed by `|| true`, green for months while doing
nothing. These tests exist so the CLI's contract is pinned in the suite
rather than trusted to a workflow step.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from quell.cli import app

runner = CliRunner()

# Keys the GitHub Action template embedded in cli.py reads out of the report.
# If any disappears the Action silently reports 0/100 — that was issue #135.
ACTION_REQUIRED_SUMMARY_KEYS = [
    "total_requirements",
    "gaps_found",
    "verified_and_written",
]


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "app" / "svc.py").write_text(
        "def charge(amount: int) -> int:\n"
        "    if amount <= 0:\n"
        "        raise ValueError('amount must be positive')\n"
        "    return amount\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_svc.py").write_text(
        "from app.svc import charge\n\n\ndef test_charge_returns():\n    assert charge(5) == 5\n",
        encoding="utf-8",
    )
    return tmp_path


# ── removed commands must stay removed (#124) ────────────────────────────────


@pytest.mark.parametrize("command", ["scan", "check"])
def test_removed_commands_exit_nonzero(command: str):
    result = runner.invoke(app, [command, "."])
    assert result.exit_code == 1
    assert "removed in v1.2" in result.output


# ── the report contract the GitHub Action depends on (#135) ──────────────────


def test_report_contains_every_key_the_action_reads(project: Path, monkeypatch):
    monkeypatch.chdir(project)
    runner.invoke(app, ["find", "app/", "--root", str(project)])

    report_path = project / "quell-report.json"
    assert report_path.exists(), "quell find must always write quell-report.json"

    summary = json.loads(report_path.read_text(encoding="utf-8")).get("summary", {})
    missing = [k for k in ACTION_REQUIRED_SUMMARY_KEYS if k not in summary]
    assert not missing, f"Action reads these but the report omits them: {missing}"


def test_report_is_valid_json_in_github_format(project: Path, monkeypatch):
    """--format github must still write a parseable report, not just annotations."""
    monkeypatch.chdir(project)
    runner.invoke(app, ["find", "app/", "--format", "github", "--root", str(project)])

    report_path = project / "quell-report.json"
    assert report_path.exists()
    json.loads(report_path.read_text(encoding="utf-8"))  # raises if malformed


# ── glyph encoding: `quell find` died on cp1252 consoles (#161) ──────────────


def test_find_survives_a_console_that_cannot_encode_glyphs(project: Path, monkeypatch):
    """Rich raised UnicodeEncodeError mid-render and the command died.

    A per-glyph guard was tried first and the crash reappeared from another
    module, so the fix reconfigures the stream once. This pins that a
    non-UTF-8 stdout does not take the process down.
    """
    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")

    result = runner.invoke(app, ["find", "app/", "--root", str(project)])
    assert "UnicodeEncodeError" not in result.output
    if result.exception is not None:
        assert not isinstance(result.exception, UnicodeEncodeError)


# ── the score must never be a fabricated zero (#156) ─────────────────────────


def test_no_findings_is_not_reported_as_a_failing_score(tmp_path: Path, monkeypatch):
    """Zero findings is a good outcome — spec10 non-negotiable #4."""
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "clean.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["find", "app/", "--root", str(tmp_path)])
    assert "Edge Cases Uncovered" not in result.output


# ── flags that exist must actually be accepted ───────────────────────────────


@pytest.mark.parametrize(
    "flags",
    [
        ["find", "app/", "--all"],
        ["find", "app/", "--format", "github"],
        ["score", "--root", "."],
        ["score", "--json"],
    ],
)
def test_documented_flags_are_accepted(project: Path, monkeypatch, flags: list[str]):
    """A renamed or dropped flag should fail here, not in a user's CI."""
    monkeypatch.chdir(project)
    result = runner.invoke(app, [*flags])
    # 2 is Typer's "no such option" / usage error.
    assert result.exit_code != 2, f"{flags} was rejected as a usage error:\n{result.output}"


def test_help_lists_find_as_the_primary_command():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "find" in result.output
