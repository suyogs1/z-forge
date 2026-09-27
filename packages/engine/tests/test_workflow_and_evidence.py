"""Tests for Task D & Task E: Validation loop orchestration and tamper-evident evidence report."""

from __future__ import annotations

import json
import pathlib

from zforge.models import ChangeRequest
from zforge.orchestration import run_change_workflow

_WORKSPACE = pathlib.Path(__file__).parents[3] / "workspace" / "synthetic-banking"


def test_full_change_engineering_workflow() -> None:
    req = ChangeRequest(
        field_name="CUSTOMER-ID",
        target_type="PIC X(12)",
        old_length=8,
        new_length=12,
        description="Expand CUSTOMER-ID from PIC X(8) to PIC X(12)",
    )

    result = run_change_workflow(_WORKSPACE, req)

    # 1. Snapshot 1: Baseline
    assert result.snapshot_1.id == "snapshot-1-baseline"
    assert result.snapshot_1.label == "Original workspace"

    # 2. Snapshot 2: Initial proposals
    assert result.snapshot_2.id == "snapshot-2-proposed"
    assert result.snapshot_2.label == "Initial proposed CUSTOMER-ID expansion"

    # 3. First validation: FAIL
    assert result.initial_validation_passed is False
    assert result.first_scenario_result.status == "FAIL"
    assert result.first_scenario_result.finding == "DATA_TRUNCATION"
    assert result.first_scenario_result.source_length == 12
    assert result.first_scenario_result.destination_length == 8

    # 4. Planted ACCTPROG finding caught by critic
    assert len(result.first_critic_findings) >= 1
    acct_finding = next(
        f for f in result.first_critic_findings if f.artifact == "cobol/ACCTPROG.CBL"
    )
    assert acct_finding.severity == "CRITICAL"
    assert acct_finding.finding_type == "DATA_TRUNCATION"

    # 5. Snapshot 3: Remediated
    assert result.snapshot_3.id == "snapshot-3-remediated"
    assert result.snapshot_3.label == "Remediated proposal"

    # 6. Final validation: PASS
    assert result.final_validation_passed is True
    assert result.second_scenario_result.status == "PASS"
    assert result.second_scenario_result.finding is None
    assert len(result.second_critic_findings) == 0

    # 7. Evidence Report: Tamper-Evident
    ev = result.evidence_report
    assert ev.report_title == "TAMPER-EVIDENT EVIDENCE REPORT"
    assert ev.report_type == "TAMPER-EVIDENT"
    assert ev.final_status == "PASS"

    # Hashes present and non-empty
    assert "workspace_baseline_sha256" in ev.deterministic_hashes
    assert "snapshot-2-proposed_sha256" in ev.deterministic_hashes
    assert "snapshot-3-remediated_sha256" in ev.deterministic_hashes
    assert "report_sha256" in ev.deterministic_hashes
    assert len(ev.deterministic_hashes["report_sha256"]) == 64

    # Report file saved on disk
    report_file = _WORKSPACE / "reports" / "tamper-evident-evidence.json"
    assert report_file.exists()
    disk_data = json.loads(report_file.read_text(encoding="utf-8"))
    assert disk_data["report_title"] == "TAMPER-EVIDENT EVIDENCE REPORT"
    assert disk_data["final_status"] == "PASS"
