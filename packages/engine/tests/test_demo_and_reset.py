"""Tests for demo entry point, machine-readable result, reset, and determinism."""

from __future__ import annotations

import io
import pathlib
import sys

from zforge.demo import main, run_demo
from zforge.models import ChangeRequest
from zforge.orchestration import execute_workflow, run_change_workflow
from zforge.versioning.snapshot import hash_file, reset_workspace

_WORKSPACE = pathlib.Path(__file__).parents[3] / "workspace" / "synthetic-banking"


def test_demo_entry_point_captures_all_steps() -> None:
    captured = io.StringIO()
    old_stdout = sys.stdout
    try:
        sys.stdout = captured
        code = run_demo(_WORKSPACE, clean_first=True)
    finally:
        sys.stdout = old_stdout

    assert code == 0
    output = captured.getvalue()

    assert "Z-FORGE CHANGE ENGINEERING DEMO" in output
    assert "CUSTOMER-ID: X(8)" in output
    assert "[1/6] Blast-radius analysis" in output
    assert "9 impacted artifacts" in output
    assert "[2/6] Change proposals" in output
    assert "3 initial proposals" in output
    assert "[3/6] Snapshot 2" in output
    assert "[4/6] Deterministic validation" in output
    assert "FAIL: DATA_TRUNCATION" in output
    assert "12 bytes" in output and "8 bytes" in output
    assert "cobol/ACCTPROG.CBL" in output
    assert "[5/6] Adversarial critic" in output
    assert "CRITICAL" in output
    assert "[6/6] Remediation" in output
    assert "Snapshot 3 created" in output
    assert "Validation PASS" in output
    assert "0 adversarial findings" in output
    assert "reports/tamper-evident-evidence.json" in output
    assert "FINAL STATUS: PASS" in output


def test_demo_reset_command() -> None:
    # First create some demo artifacts
    run_demo(_WORKSPACE, clean_first=False)
    snap_dir = _WORKSPACE / "snapshots"
    rep_dir = _WORKSPACE / "reports"
    assert any(snap_dir.iterdir())
    assert any(rep_dir.iterdir())

    # Run reset command via main CLI
    captured = io.StringIO()
    old_stdout = sys.stdout
    try:
        sys.stdout = captured
        code = main(["--reset", "--workspace", str(_WORKSPACE)])
    finally:
        sys.stdout = old_stdout

    assert code == 0
    assert "Z-FORGE DEMO RESET" in captured.getvalue()
    assert "Original imported artifacts remain immutable" in captured.getvalue()

    # Verify generated directories are now empty
    assert list(snap_dir.iterdir()) == []
    assert list(rep_dir.iterdir()) == []


def test_structured_workflow_result() -> None:
    reset_workspace(_WORKSPACE)
    req = ChangeRequest(
        field_name="CUSTOMER-ID",
        target_type="PIC X(12)",
        old_length=8,
        new_length=12,
    )
    res = execute_workflow(_WORKSPACE, req)

    # Required machine-readable keys for Bob/MCP integration
    assert res["status"] == "PASS"
    assert res["change_request"] == {
        "field": "CUSTOMER-ID",
        "old_length": 8,
        "new_length": 12,
    }
    assert isinstance(res["impacted_artifacts"], list)
    assert len(res["impacted_artifacts"]) == 9
    assert isinstance(res["initial_proposals"], list)
    assert len(res["initial_proposals"]) == 3
    assert res["initial_snapshot"] == "snapshot-2-proposed"
    assert res["first_validation"] == {
        "status": "FAIL",
        "finding": "DATA_TRUNCATION",
    }
    assert isinstance(res["adversarial_findings"], list)
    assert len(res["adversarial_findings"]) >= 1
    assert res["remediation"] == {
        "status": "APPLIED",
        "snapshot": "snapshot-3-remediated",
    }
    assert res["final_validation"] == {"status": "PASS"}
    assert res["evidence_report"] == "reports/tamper-evident-evidence.json"


def test_original_workspace_immutability() -> None:
    # Hash all original files before demo
    original_subdirs = ["cobol", "copybooks", "hlasm", "jcl", "datasets", "afp"]
    before_hashes = {}
    for sub in original_subdirs:
        for f in (_WORKSPACE / sub).rglob("*"):
            if f.is_file():
                rel = f.relative_to(_WORKSPACE).as_posix()
                before_hashes[rel] = hash_file(f)

    # Run full demo including reset
    code = run_demo(_WORKSPACE, clean_first=True)
    assert code == 0

    # Verify hashes after demo
    for rel, before_h in before_hashes.items():
        after_h = hash_file(_WORKSPACE / rel)
        assert after_h == before_h, f"Original imported artifact was modified: {rel}"


def test_repeated_clean_run_determinism() -> None:
    req = ChangeRequest(
        field_name="CUSTOMER-ID",
        target_type="PIC X(12)",
        old_length=8,
        new_length=12,
    )

    # Run 1
    reset_workspace(_WORKSPACE)
    res1 = run_change_workflow(_WORKSPACE, req)
    hashes1 = res1.evidence_report.deterministic_hashes

    # Run 2
    reset_workspace(_WORKSPACE)
    res2 = run_change_workflow(_WORKSPACE, req)
    hashes2 = res2.evidence_report.deterministic_hashes

    # Verify complete determinism
    assert hashes1 == hashes2
    assert res1.first_scenario_result == res2.first_scenario_result
    assert res1.second_scenario_result == res2.second_scenario_result
    assert [f.model_dump() for f in res1.first_critic_findings] == [
        f.model_dump() for f in res2.first_critic_findings
    ]
