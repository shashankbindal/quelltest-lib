"""Unit tests for the local MCP server (spec9 §3).

The impl_* functions are plain functions with no mcp dependency, so these
tests run whether or not the optional [mcp] extra is installed.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from quell.mcp_server import (
    _resolve_target,
    impl_find_edge_cases,
    impl_get_prs_score,
    impl_prove_file,
    impl_reproduce_bug,
    impl_write_verified_tests,
)

# ── path resolution ───────────────────────────────────────────────────────────


def test_resolve_target_relative(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    assert _resolve_target("src", tmp_path) == (tmp_path / "src").resolve()


def test_resolve_target_missing(tmp_path: Path) -> None:
    assert _resolve_target("nope", tmp_path) is None


# ── error contract: tools never raise ─────────────────────────────────────────


def test_find_edge_cases_missing_path(tmp_path: Path) -> None:
    result = impl_find_edge_cases("does-not-exist", root=tmp_path)
    assert "error" in result
    assert "does-not-exist" in result["error"]


def test_write_verified_tests_missing_path(tmp_path: Path) -> None:
    result = impl_write_verified_tests("does-not-exist", root=tmp_path)
    assert "error" in result


def test_prove_file_missing_file(tmp_path: Path) -> None:
    result = impl_prove_file("ghost.py", root=tmp_path)
    assert "error" in result


def test_reproduce_bug_missing_file(tmp_path: Path) -> None:
    result = impl_reproduce_bug("some bug", file="ghost.py", root=tmp_path)
    assert "error" in result


def test_find_edge_cases_sdk_exception_becomes_error_dict(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    with patch("quell.sdk.Quell") as mock_quell:
        mock_quell.side_effect = RuntimeError("boom")
        result = impl_find_edge_cases("src", root=tmp_path)
    assert "error" in result
    assert "boom" in result["error"]


# ── happy paths with mocked SDK ───────────────────────────────────────────────


def _mock_requirement(covered: bool = False) -> MagicMock:
    req = MagicMock()
    req.id = "r1"
    req.description = "amount must be positive"
    req.constraint_kind.value = "BOUNDARY"
    req.target_function = "process_payment"
    req.target_file = Path("src/payments.py")
    req.source_line = 42
    req.is_covered = covered
    return req


def test_find_edge_cases_reports_gaps(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    uncovered = _mock_requirement(covered=False)
    covered = _mock_requirement(covered=True)

    check_result = MagicMock()
    check_result.requirements = [uncovered, covered]
    check_result.uncovered = [uncovered]
    check_result.covered = [covered]
    check_result.score = 0.5

    with patch("quell.sdk.Quell") as mock_quell:
        mock_quell.return_value.check.return_value = check_result
        result = impl_find_edge_cases("src", root=tmp_path)

    assert result["total_requirements"] == 2
    assert result["uncovered"] == 1
    assert result["coverage_percent"] == 50.0
    assert result["gaps"][0]["function"] == "process_payment"
    assert result["gaps"][0]["constraint_kind"] == "BOUNDARY"


def test_write_verified_tests_reads_report(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    report = tmp_path / "report.json"
    report.write_text('{"written": 3, "skipped": 1, "error": 0}')

    check_result = MagicMock()
    check_result.requirements = [_mock_requirement(True)] * 4
    check_result.score = 1.0
    check_result.report_path = report

    with patch("quell.sdk.Quell") as mock_quell:
        mock_quell.return_value.check.return_value = check_result
        result = impl_write_verified_tests("src", root=tmp_path)

    assert result["written"] == 3
    assert result["skipped"] == 1
    assert result["coverage_percent_after"] == 100.0
    assert "Gate 5" in result["note"]


def test_get_prs_score_tiers(tmp_path: Path) -> None:
    file_score = MagicMock()
    file_score.path = "src/payments.py"
    file_score.total_requirements = 10
    file_score.covered_requirements = 9

    project_score = MagicMock()
    project_score.percentage = 90
    project_score.files = [file_score]

    with patch("quell.sdk.Quell") as mock_quell:
        mock_quell.return_value.score.return_value = project_score
        result = impl_get_prs_score(root=tmp_path)

    assert result["score_percent"] == 90
    assert result["tier"] == "Production Ready"
    assert result["files"][0]["covered_requirements"] == 9


def test_prove_file_ratio(tmp_path: Path) -> None:
    f = tmp_path / "payments.py"
    f.write_text("def pay(): ...")

    with patch("quell.sdk.Quell") as mock_quell:
        mock_quell.return_value.prove.return_value = 0.75
        result = impl_prove_file("payments.py", function="pay", root=tmp_path)

    assert result["coverage_percent"] == 75.0
    assert result["function"] == "pay"


def test_reproduce_bug_written(tmp_path: Path) -> None:
    with patch("quell.sdk.Quell") as mock_quell:
        mock_quell.return_value.reproduce.return_value = True
        result = impl_reproduce_bug("payment accepts zero", root=tmp_path)

    assert result["test_written"] is True


# ── entry point guard ─────────────────────────────────────────────────────────


def test_main_exits_helpfully_without_mcp(capsys) -> None:
    import quell.mcp_server as mod

    with patch.object(mod, "create_server", side_effect=ImportError("no mcp")):
        try:
            mod.main()
            raised = False
        except SystemExit as exc:
            raised = True
            assert exc.code == 1
    assert raised
    assert "quelltest[mcp]" in capsys.readouterr().err
