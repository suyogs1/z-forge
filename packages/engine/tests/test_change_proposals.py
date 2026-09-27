"""Tests for Task A: Change proposals, topological ordering, and snapshot isolation."""

from __future__ import annotations

import pathlib

import pytest

from zforge.change.proposals import apply_proposals, generate_proposals
from zforge.graph.blast_radius import blast_radius
from zforge.ingestion.orchestrator import ingest_workspace
from zforge.models import (
    ArtifactType,
    ChangeKind,
    ChangeRequest,
    DependencyGraph,
)
from zforge.versioning.snapshot import hash_file

_WORKSPACE = pathlib.Path(__file__).parents[3] / "workspace" / "synthetic-banking"


@pytest.fixture(scope="module")
def dep_graph() -> DependencyGraph:
    return ingest_workspace(_WORKSPACE, persist=False)


def test_customer_id_proposals_generation(dep_graph: DependencyGraph) -> None:
    br = blast_radius("CUSTOMER-ID", "Expand PIC X(8) to PIC X(12)", dep_graph)
    req = ChangeRequest(
        field_name="CUSTOMER-ID",
        target_type="PIC X(12)",
        old_length=8,
        new_length=12,
        description="Expand PIC X(8) to PIC X(12)",
    )

    change_set, report = generate_proposals(dep_graph, br, req, include_remediation=False)

    assert len(change_set.proposals) >= 3

    # Check CUSTMAST.CPY proposal
    custmast_prop = next(
        p for p in change_set.proposals if "CUSTMAST.CPY" in dep_graph.artifacts[p.artifact_id].path
    )
    assert "05  CUSTOMER-ID             PIC X(12)." in custmast_prop.proposed_content
    assert custmast_prop.semantic_diff.changes[0].kind == ChangeKind.FIELD_RESIZE

    # Check CUSTDSCT.ASM proposal
    custdsct_prop = next(
        p for p in change_set.proposals if "CUSTDSCT.ASM" in dep_graph.artifacts[p.artifact_id].path
    )
    assert "CUSTID   DS    CL12" in custdsct_prop.proposed_content
    assert "CUSTIDLN EQU   12" in custdsct_prop.proposed_content

    # Check CUST.MASTER.FILE.dsd proposal
    dsd_prop = next(
        p
        for p in change_set.proposals
        if "CUST.MASTER.FILE.dsd" in dep_graph.artifacts[p.artifact_id].path
    )
    assert '"length": 12' in dsd_prop.proposed_content
    assert '"lrecl": 84' in dsd_prop.proposed_content

    # Check report items
    assert len(report.proposals) >= 3
    for item in report.proposals:
        assert item.artifact
        assert item.reason
        assert item.change_kind
        assert item.old_value
        assert item.new_value
        assert item.confidence == 1.0
        assert item.dependency_reason


def test_proposals_in_topological_order(dep_graph: DependencyGraph) -> None:
    br = blast_radius("CUSTOMER-ID", "Expand PIC X(8) to PIC X(12)", dep_graph)
    req = ChangeRequest(field_name="CUSTOMER-ID", new_length=12)
    change_set, _ = generate_proposals(dep_graph, br, req, include_remediation=True)

    types = [dep_graph.artifacts[p.artifact_id].type for p in change_set.proposals]

    # Verify: copybooks appear before programs/hlasm, datasets appear last
    type_priority = {
        ArtifactType.COPYBOOK: 1,
        ArtifactType.HLASM: 2,
        ArtifactType.COBOL: 2,
        ArtifactType.JCL: 3,
        ArtifactType.DATASET: 4,
    }
    priorities = [type_priority[t] for t in types]
    assert priorities == sorted(priorities), f"Proposals not in topological order: {types}"


def test_apply_proposals_never_mutates_original_artifacts(
    dep_graph: DependencyGraph, tmp_path: pathlib.Path
) -> None:
    # Snapshot original files
    custmast_orig = _WORKSPACE / "copybooks" / "CUSTMAST.CPY"
    orig_hash = hash_file(custmast_orig)
    orig_content = custmast_orig.read_text(encoding="utf-8")

    br = blast_radius("CUSTOMER-ID", "Expand PIC X(8) to PIC X(12)", dep_graph)
    req = ChangeRequest(field_name="CUSTOMER-ID", new_length=12)
    change_set, _ = generate_proposals(dep_graph, br, req, include_remediation=False)

    snapshot = apply_proposals(
        workspace_root=_WORKSPACE,
        change_set=change_set,
        snapshot_id="test-snap-proposals",
        label="Test Proposals",
        dep_graph=dep_graph,
    )

    # 1. Verify original file is COMPLETELY UNTOUCHED
    assert custmast_orig.read_text(encoding="utf-8") == orig_content
    assert hash_file(custmast_orig) == orig_hash

    # 2. Verify snapshot directory contains modified file
    snap_custmast = _WORKSPACE / "snapshots" / "test-snap-proposals" / "copybooks" / "CUSTMAST.CPY"
    assert snap_custmast.exists()
    assert "05  CUSTOMER-ID             PIC X(12)." in snap_custmast.read_text(encoding="utf-8")

    # 3. Snapshot metadata exists
    assert snapshot.id == "test-snap-proposals"
    assert len(snapshot.proposals_applied) > 0
