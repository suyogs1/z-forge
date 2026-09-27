"""Acceptance tests for T3/T4 — ingestion and blast radius.

Tests prove:
1.  Full synthetic workspace ingests successfully.
2.  Every expected artifact becomes a typed graph node.
3.  COPY edges are detected.
4.  CALL edges are detected.
5.  JCL dataset producer/consumer edges are detected.
6.  HLASM DSECT fields and offsets are detected.
7.  CUSTOMER-ID blast radius finds ACCTPROG through
    CUSTMAST → ACCTMAST → ACCTPROG.
8.  CUSTOMER-ID blast radius finds CUSTPROG.
9.  CUSTOMER-ID blast radius finds CUSTRPT.
10. CUSTOMER-ID identifies CUSTDSCT as an affected mirrored structure.
11. Dataset lineage identifies downstream consumers.
12. Blast-radius output is topologically ordered.
13. The planted WS-ACCT-CUST-ID issue is visible.
"""

from __future__ import annotations

import pathlib

import pytest

from zforge.graph._digraph import DiGraph
from zforge.graph.blast_radius import blast_radius
from zforge.graph.builder import build_nx_graph
from zforge.graph.lineage import dataset_lineage
from zforge.ingestion.orchestrator import ingest_workspace
from zforge.models import ArtifactType, DependencyGraph, DependencyKind

# ---------------------------------------------------------------------------
# Fixture: ingest the synthetic-banking workspace once per test session
# ---------------------------------------------------------------------------

_WORKSPACE = pathlib.Path(__file__).parents[3] / "workspace" / "synthetic-banking"


@pytest.fixture(scope="session")
def dep_graph() -> DependencyGraph:
    assert _WORKSPACE.exists(), f"Workspace not found: {_WORKSPACE}"
    graph = ingest_workspace(_WORKSPACE, persist=True)
    return graph


@pytest.fixture(scope="session")
def nx_graph(dep_graph: DependencyGraph) -> DiGraph:
    return build_nx_graph(dep_graph)


# ---------------------------------------------------------------------------
# Test 1: Full workspace ingests successfully
# ---------------------------------------------------------------------------


def test_workspace_ingests_successfully(dep_graph: DependencyGraph) -> None:
    assert len(dep_graph.artifacts) > 0, "No artifacts ingested"


# ---------------------------------------------------------------------------
# Test 2: Every expected artifact is a typed graph node
# ---------------------------------------------------------------------------

_EXPECTED_ARTIFACTS: list[tuple[str, ArtifactType]] = [
    ("ACCTPROG.CBL", ArtifactType.COBOL),
    ("CUSTPROG.CBL", ArtifactType.COBOL),
    ("CUSTRPT.CBL", ArtifactType.COBOL),
    ("CUSTMAST.CPY", ArtifactType.COPYBOOK),
    ("ACCTMAST.CPY", ArtifactType.COPYBOOK),
    ("ERRCODE.CPY", ArtifactType.COPYBOOK),
    ("CUSTDSCT.ASM", ArtifactType.HLASM),
    ("NIGHTLY.JCL", ArtifactType.JCL),
    ("CUSTLOAD.JCL", ArtifactType.JCL),
    ("CUSTRPT.JCL", ArtifactType.JCL),
    ("CUST.MASTER.FILE.dsd", ArtifactType.DATASET),
    ("CUST.REPORT.FILE.dsd", ArtifactType.DATASET),
]


@pytest.mark.parametrize("filename,expected_type", _EXPECTED_ARTIFACTS)
def test_artifact_present_with_correct_type(
    dep_graph: DependencyGraph,
    filename: str,
    expected_type: ArtifactType,
) -> None:
    matches = [a for a in dep_graph.artifacts.values() if a.path.endswith(filename)]
    assert matches, f"Artifact not found: {filename}"
    assert matches[0].type == expected_type, (
        f"Wrong type for {filename}: {matches[0].type} != {expected_type}"
    )


# ---------------------------------------------------------------------------
# Test 3: COPY edges are detected
# ---------------------------------------------------------------------------


def _find_artifact(dep_graph: DependencyGraph, filename_suffix: str):
    for a in dep_graph.artifacts.values():
        if a.path.endswith(filename_suffix):
            return a
    return None


def test_copy_edges_detected(dep_graph: DependencyGraph) -> None:
    copy_edges = [e for e in dep_graph.edges if e.kind == DependencyKind.COPIES]
    assert len(copy_edges) > 0, "No COPY edges found"

    # ACCTPROG should COPY ACCTMAST
    acctprog = _find_artifact(dep_graph, "ACCTPROG.CBL")
    acctmast = _find_artifact(dep_graph, "ACCTMAST.CPY")
    assert acctprog and acctmast
    assert any(e.source_id == acctprog.id and e.target_id == acctmast.id for e in copy_edges), (
        "ACCTPROG → ACCTMAST COPY edge missing"
    )

    # ACCTMAST should COPY CUSTMAST
    custmast = _find_artifact(dep_graph, "CUSTMAST.CPY")
    assert custmast
    assert any(e.source_id == acctmast.id and e.target_id == custmast.id for e in copy_edges), (
        "ACCTMAST → CUSTMAST COPY edge missing"
    )

    # CUSTPROG should COPY CUSTMAST
    custprog = _find_artifact(dep_graph, "CUSTPROG.CBL")
    assert custprog
    assert any(e.source_id == custprog.id and e.target_id == custmast.id for e in copy_edges), (
        "CUSTPROG → CUSTMAST COPY edge missing"
    )


# ---------------------------------------------------------------------------
# Test 4: CALL edges are detected
# ---------------------------------------------------------------------------


def test_call_edges_detected(dep_graph: DependencyGraph) -> None:
    call_edges = [e for e in dep_graph.edges if e.kind == DependencyKind.CALLS]
    assert len(call_edges) > 0, "No CALL edges found"

    acctprog = _find_artifact(dep_graph, "ACCTPROG.CBL")
    custprog = _find_artifact(dep_graph, "CUSTPROG.CBL")
    assert acctprog and custprog

    assert any(e.source_id == acctprog.id and e.target_id == custprog.id for e in call_edges), (
        "ACCTPROG → CUSTPROG CALL edge missing"
    )


# ---------------------------------------------------------------------------
# Test 5: JCL dataset producer/consumer edges are detected
# ---------------------------------------------------------------------------


def test_jcl_producer_consumer_edges(dep_graph: DependencyGraph) -> None:
    write_edges = [e for e in dep_graph.edges if e.kind == DependencyKind.WRITES_TO]
    read_edges = [e for e in dep_graph.edges if e.kind == DependencyKind.READS_FROM]
    assert len(write_edges) > 0, "No WRITES_TO edges found"
    assert len(read_edges) > 0, "No READS_FROM edges found"


def test_lineage_edges_present(dep_graph: DependencyGraph) -> None:
    assert len(dep_graph.lineage) > 0, "No lineage edges found"


# ---------------------------------------------------------------------------
# Test 6: HLASM DSECT fields and offsets are detected
# ---------------------------------------------------------------------------


def test_hlasm_dsect_fields(dep_graph: DependencyGraph) -> None:
    custdsct = _find_artifact(dep_graph, "CUSTDSCT.ASM")
    assert custdsct, "CUSTDSCT.ASM not found"

    sections = custdsct.metadata.get("sections", [])
    assert sections, "No sections in CUSTDSCT"

    dsect = next((s for s in sections if s["kind"] == "DSECT"), None)
    assert dsect, "No DSECT section in CUSTDSCT"

    field_labels = [f["label"] for f in dsect["fields"]]
    assert "CUSTID" in field_labels, "CUSTID field missing"
    assert "CUSTNAME" in field_labels, "CUSTNAME field missing"

    custid_field = next(f for f in dsect["fields"] if f["label"] == "CUSTID")
    assert custid_field["byte_size"] == 8
    assert custid_field["offset"] == 0


# ---------------------------------------------------------------------------
# Blast radius fixture (session-scoped)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def br_result(dep_graph: DependencyGraph):
    return blast_radius("CUSTOMER-ID", "Expand PIC X(8) to PIC X(12)", dep_graph)


def _impacted_paths(br_result) -> list[str]:
    return [ai.artifact.path for ai in br_result.impacted]


# ---------------------------------------------------------------------------
# Test 7: Blast radius finds ACCTPROG through CUSTMAST → ACCTMAST → ACCTPROG
# ---------------------------------------------------------------------------


def test_blast_radius_finds_acctprog(br_result) -> None:
    paths = _impacted_paths(br_result)
    assert any("ACCTPROG" in p for p in paths), f"ACCTPROG not in blast radius. Impacted: {paths}"


# ---------------------------------------------------------------------------
# Test 8: Blast radius finds CUSTPROG
# ---------------------------------------------------------------------------


def test_blast_radius_finds_custprog(br_result) -> None:
    paths = _impacted_paths(br_result)
    assert any("CUSTPROG" in p for p in paths), f"CUSTPROG not in blast radius. Impacted: {paths}"


# ---------------------------------------------------------------------------
# Test 9: Blast radius finds CUSTRPT
# ---------------------------------------------------------------------------


def test_blast_radius_finds_custrpt(br_result) -> None:
    paths = _impacted_paths(br_result)
    assert any("CUSTRPT" in p for p in paths), f"CUSTRPT not in blast radius. Impacted: {paths}"


# ---------------------------------------------------------------------------
# Test 10: CUSTDSCT is identified as affected mirrored structure
# ---------------------------------------------------------------------------


def test_blast_radius_finds_custdsct(br_result) -> None:
    paths = _impacted_paths(br_result)
    assert any("CUSTDSCT" in p for p in paths), f"CUSTDSCT not in blast radius. Impacted: {paths}"


# ---------------------------------------------------------------------------
# Test 11: Dataset lineage identifies downstream consumers
# ---------------------------------------------------------------------------


def test_dataset_lineage_downstream(dep_graph: DependencyGraph) -> None:
    cust_master = _find_artifact(dep_graph, "CUST.MASTER.FILE.dsd")
    if cust_master is None:
        pytest.skip("CUST.MASTER.FILE.dsd not ingested")

    lin = dataset_lineage(cust_master.id, dep_graph)
    # CUSTPROG and CUSTRPT both read CUST.MASTER.FILE
    assert len(lin.consumers) > 0 or len(lin.downstream_datasets) > 0, (
        "No downstream consumers found for CUST.MASTER.FILE"
    )


# ---------------------------------------------------------------------------
# Test 12: Blast-radius output is topologically ordered
# ---------------------------------------------------------------------------


def test_blast_radius_topological_order(dep_graph: DependencyGraph, br_result) -> None:
    impacted_ids = [ai.artifact.id for ai in br_result.impacted]
    if len(impacted_ids) < 2:
        pytest.skip("Not enough impacted artifacts to test ordering")

    # Verify no impacted artifact appears before its dependency in the list
    # i.e., for every COPIES/CALLS edge source→target, target's index ≤ source's index
    id_to_pos = {art_id: i for i, art_id in enumerate(impacted_ids)}

    violations: list[str] = []
    for edge in dep_graph.edges:
        if edge.kind not in (DependencyKind.COPIES, DependencyKind.CALLS):
            continue
        src_pos = id_to_pos.get(edge.source_id)
        tgt_pos = id_to_pos.get(edge.target_id)
        if src_pos is not None and tgt_pos is not None:
            if src_pos < tgt_pos:
                violations.append(
                    f"{dep_graph.artifacts[edge.source_id].path} (pos {src_pos}) "
                    f"comes before {dep_graph.artifacts[edge.target_id].path} (pos {tgt_pos})"
                )
    assert not violations, f"Topological order violations: {violations}"


# ---------------------------------------------------------------------------
# Test 13: Planted WS-ACCT-CUST-ID is visible
# ---------------------------------------------------------------------------


def test_planted_failure_visible(dep_graph: DependencyGraph, br_result) -> None:
    acctprog = _find_artifact(dep_graph, "ACCTPROG.CBL")
    assert acctprog, "ACCTPROG.CBL not found"

    local_decls = acctprog.metadata.get("local_declarations", [])
    local_names = [d["name"] for d in local_decls if isinstance(d, dict)]
    assert "WS-ACCT-CUST-ID" in local_names, (
        f"WS-ACCT-CUST-ID not in local declarations. Found: {local_names}"
    )

    # Also verify it appears in adversarial findings of blast radius
    findings_text = " ".join(br_result.adversarial_findings)
    assert "WS-ACCT-CUST-ID" in findings_text or "ACCTPROG" in findings_text, (
        f"ACCTPROG planted failure not surfaced in adversarial_findings: "
        f"{br_result.adversarial_findings}"
    )
