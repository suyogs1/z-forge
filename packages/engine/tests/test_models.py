"""Smoke test: engine package imports and core models are available."""

from zforge.models import (
    Artifact,
    ArtifactType,
    ChangeProposal,
    DependencyGraph,
    ProposalStatus,
    ZPackManifest,
)


def test_artifact_id_is_deterministic() -> None:
    a = Artifact(
        id=Artifact.make_id("cobol/CUSTPROG.CBL", ArtifactType.COBOL),
        path="cobol/CUSTPROG.CBL",
        type=ArtifactType.COBOL,
    )
    b = Artifact(
        id=Artifact.make_id("cobol/CUSTPROG.CBL", ArtifactType.COBOL),
        path="cobol/CUSTPROG.CBL",
        type=ArtifactType.COBOL,
    )
    assert a.id == b.id
    assert len(a.id) == 16


def test_dependency_graph_empty() -> None:
    graph = DependencyGraph()
    assert graph.artifacts == {}
    assert graph.edges == []
    assert graph.lineage == []


def test_proposal_default_status() -> None:
    proposal = ChangeProposal(
        id="p001",
        artifact_id="abc",
        description="Test",
        original_content="old",
        proposed_content="new",
    )
    assert proposal.status == ProposalStatus.PENDING
    assert proposal.confidence == 1.0


def test_zpack_manifest_version() -> None:
    manifest = ZPackManifest(
        workspace_id="ws-001",
        name="test",
        created_at="2024-01-01T00:00:00Z",
    )
    assert manifest.version == "1.0"
