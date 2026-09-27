"""Tests for Task B & Task C: Deterministic scenario runtime and adversarial critic."""

from __future__ import annotations

import pathlib

import pytest

from zforge.adversarial.critic import AdversarialCritic
from zforge.change.proposals import apply_proposals, generate_proposals
from zforge.graph.blast_radius import blast_radius
from zforge.ingestion.orchestrator import ingest_workspace
from zforge.models import ChangeRequest, DependencyGraph
from zforge.runtime.deterministic_adapter import DeterministicScenarioAdapter
from zforge.runtime.local_syntax_adapter import LocalSyntaxAdapter

_WORKSPACE = pathlib.Path(__file__).parents[3] / "workspace" / "synthetic-banking"


@pytest.fixture(scope="module")
def dep_graph() -> DependencyGraph:
    return ingest_workspace(_WORKSPACE, persist=False)


def test_deterministic_scenario_detects_truncation_on_unremediated_snapshot(
    dep_graph: DependencyGraph,
) -> None:
    br = blast_radius("CUSTOMER-ID", "Expand PIC X(8) to PIC X(12)", dep_graph)
    req = ChangeRequest(field_name="CUSTOMER-ID", new_length=12)

    # Apply initial proposals (WITHOUT local ACCTPROG remediation)
    change_set, _ = generate_proposals(dep_graph, br, req, include_remediation=False)
    snapshot = apply_proposals(
        workspace_root=_WORKSPACE,
        change_set=change_set,
        snapshot_id="test-snap-unremediated",
        label="Unremediated Proposed",
        dep_graph=dep_graph,
    )

    adapter = DeterministicScenarioAdapter()
    snap_dir = _WORKSPACE / "snapshots" / snapshot.id
    result = adapter.run_scenario(snap_dir)

    assert result.status == "FAIL"
    assert result.finding == "DATA_TRUNCATION"
    assert result.source_length == 12
    assert result.destination_length == 8
    assert result.artifact == "cobol/ACCTPROG.CBL"
    assert "WS-ACCT-CUST-ID PIC X(8)" in result.evidence


def test_adversarial_critic_catches_planted_acctprog_failure(
    dep_graph: DependencyGraph,
) -> None:
    snap_dir = _WORKSPACE / "snapshots" / "test-snap-unremediated"

    critic = AdversarialCritic()
    findings = critic.inspect_snapshot(snap_dir)

    assert len(findings) >= 1
    acct_finding = next((f for f in findings if f.artifact == "cobol/ACCTPROG.CBL"), None)
    assert acct_finding is not None
    assert acct_finding.severity == "CRITICAL"
    assert acct_finding.finding_type == "DATA_TRUNCATION"
    assert "CUSTOMER-ID is 12 bytes but WS-ACCT-CUST-ID remains X(8)" in acct_finding.evidence
    assert "Change WS-ACCT-CUST-ID to X(12)" in acct_finding.remediation


def test_scenario_and_critic_pass_after_remediation(dep_graph: DependencyGraph) -> None:
    br = blast_radius("CUSTOMER-ID", "Expand PIC X(8) to PIC X(12)", dep_graph)
    req = ChangeRequest(field_name="CUSTOMER-ID", new_length=12)

    # Apply proposals WITH local remediation
    change_set, _ = generate_proposals(dep_graph, br, req, include_remediation=True)
    snapshot = apply_proposals(
        workspace_root=_WORKSPACE,
        change_set=change_set,
        snapshot_id="test-snap-remediated",
        label="Remediated Proposed",
        dep_graph=dep_graph,
    )

    snap_dir = _WORKSPACE / "snapshots" / snapshot.id

    # 1. Deterministic adapter must now PASS
    adapter = DeterministicScenarioAdapter()
    result = adapter.run_scenario(snap_dir)
    assert result.status == "PASS"
    assert result.finding is None
    assert result.source_length == 12
    assert result.destination_length == 12
    assert "WS-ACCT-CUST-ID PIC X(12)" in result.evidence

    # 2. Adversarial critic must find NO issues
    critic = AdversarialCritic()
    findings = critic.inspect_snapshot(snap_dir)
    assert len(findings) == 0


def test_local_syntax_adapter_alone_misses_truncation(dep_graph: DependencyGraph) -> None:
    """Proves why DeterministicScenarioAdapter and critic are required."""
    snap_dir = _WORKSPACE / "snapshots" / "test-snap-unremediated"
    acct_file = snap_dir / "cobol" / "ACCTPROG.CBL"
    content = acct_file.read_text(encoding="utf-8")

    acct_art = next(a for a in dep_graph.artifacts.values() if a.path.endswith("ACCTPROG.CBL"))
    syntax_adapter = LocalSyntaxAdapter()
    val_result = syntax_adapter.validate(acct_art, content)

    # Syntax is valid COBOL, so LocalSyntaxAdapter passes!
    assert val_result.passed is True
