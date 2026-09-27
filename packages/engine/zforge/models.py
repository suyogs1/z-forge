"""Z-FORGE core domain model — Pydantic/dataclass definitions for all entities."""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ArtifactType(str, Enum):
    COBOL = "COBOL"
    COPYBOOK = "COPYBOOK"
    HLASM = "HLASM"
    JCL = "JCL"
    DATASET = "DATASET"
    AFP = "AFP"
    UNKNOWN = "UNKNOWN"


class DependencyKind(str, Enum):
    COPIES = "COPIES"  # COBOL COPY statement
    CALLS = "CALLS"  # COBOL CALL statement
    USES_DD = "USES_DD"  # JCL DD → dataset
    WRITES_TO = "WRITES_TO"  # program writes dataset
    READS_FROM = "READS_FROM"  # program reads dataset
    INCLUDES = "INCLUDES"  # HLASM COPY / INCLUDE


class ChangeKind(str, Enum):
    FIELD_RESIZE = "FIELD_RESIZE"
    OFFSET_SHIFT = "OFFSET_SHIFT"
    INTERFACE_CHANGE = "INTERFACE_CHANGE"
    JCL_PARAM = "JCL_PARAM"
    SCHEMA_UPDATE = "SCHEMA_UPDATE"


class ProposalStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"
    MERGED = "MERGED"


# ---------------------------------------------------------------------------
# Source location
# ---------------------------------------------------------------------------


class SourceLocation(BaseModel):
    line: int
    column: int = 0
    end_line: int | None = None


# ---------------------------------------------------------------------------
# Artifact
# ---------------------------------------------------------------------------


class Artifact(BaseModel):
    id: str
    path: str
    type: ArtifactType
    raw_content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def make_id(cls, path: str, artifact_type: ArtifactType) -> str:
        return hashlib.sha256(f"{path}:{artifact_type}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Graph edges
# ---------------------------------------------------------------------------


class Dependency(BaseModel):
    source_id: str
    target_id: str
    kind: DependencyKind
    location: SourceLocation = Field(default_factory=lambda: SourceLocation(line=0))


class DataLineageEdge(BaseModel):
    producer_id: str
    consumer_id: str
    dataset_name: str
    dd_name: str = ""


# ---------------------------------------------------------------------------
# Dependency graph (serialisable)
# ---------------------------------------------------------------------------


class DependencyGraph(BaseModel):
    artifacts: dict[str, Artifact] = Field(default_factory=dict)
    edges: list[Dependency] = Field(default_factory=list)
    lineage: list[DataLineageEdge] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Blast radius
# ---------------------------------------------------------------------------


class ImpactReason(str, Enum):
    DIRECT_FIELD_REFERENCE = "DIRECT_FIELD_REFERENCE"
    COPYBOOK_CHAIN = "COPYBOOK_CHAIN"
    CALL_CHAIN = "CALL_CHAIN"
    DATA_LINEAGE = "DATA_LINEAGE"
    SCHEMA_DEPENDENCY = "SCHEMA_DEPENDENCY"
    LOCAL_REDECLARATION = "LOCAL_REDECLARATION"


class ArtifactImpact(BaseModel):
    artifact: Artifact
    reason: ImpactReason
    details: str = ""


class BlastRadiusResult(BaseModel):
    field_name: str
    change_description: str
    # Artifacts that are directly or transitively impacted and require modification
    impacted: list[ArtifactImpact] = Field(default_factory=list)
    # Artifacts inspected but determined not to need modification
    inspected_unchanged: list[ArtifactImpact] = Field(default_factory=list)
    # Adversarial findings (populated after critic pass)
    adversarial_findings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Change proposal
# ---------------------------------------------------------------------------


class SemanticChange(BaseModel):
    kind: ChangeKind
    location: SourceLocation
    before: str
    after: str
    impact_description: str = ""


class SemanticDiff(BaseModel):
    changes: list[SemanticChange] = Field(default_factory=list)


class ChangeProposal(BaseModel):
    id: str
    artifact_id: str
    description: str
    original_content: str
    proposed_content: str
    semantic_diff: SemanticDiff = Field(default_factory=SemanticDiff)
    rationale: str = ""
    confidence: float = 1.0
    status: ProposalStatus = ProposalStatus.PENDING


class ChangeSet(BaseModel):
    id: str
    proposals: list[ChangeProposal] = Field(default_factory=list)
    ordered_artifact_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class Diagnostic(BaseModel):
    severity: str  # "error" | "warning" | "info"
    message: str
    location: SourceLocation | None = None


class ValidationResult(BaseModel):
    proposal_id: str
    passed: bool
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    runtime_adapter: str = "none"


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------


class Snapshot(BaseModel):
    id: str
    label: str
    timestamp: str
    workspace_hash: str
    proposals_applied: list[str] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)  # artifact_id → content hash


class SnapshotRef(BaseModel):
    id: str
    label: str
    timestamp: str


# ---------------------------------------------------------------------------
# Z-PACK manifest
# ---------------------------------------------------------------------------


class ArtifactRef(BaseModel):
    id: str
    path: str
    type: ArtifactType
    content_hash: str = ""


class ZPackManifest(BaseModel):
    version: str = "1.0"
    workspace_id: str
    name: str
    created_at: str
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    snapshots: list[SnapshotRef] = Field(default_factory=list)
    lineage_graph_path: str = "graph/lineage.json"


# ---------------------------------------------------------------------------
# Change Request and Proposal Report
# ---------------------------------------------------------------------------


class ChangeRequest(BaseModel):
    field_name: str
    target_type: str = "PIC X(12)"
    old_length: int = 8
    new_length: int = 12
    description: str = "Expand CUSTOMER-ID from PIC X(8) to PIC X(12)"


class ProposalReportItem(BaseModel):
    artifact: str
    reason: str
    change_kind: ChangeKind
    old_value: str
    new_value: str
    confidence: float = 1.0
    dependency_reason: str


class ProposalReport(BaseModel):
    change_request: str
    proposals: list[ProposalReportItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Runtime & Adversarial
# ---------------------------------------------------------------------------


class ScenarioResult(BaseModel):
    status: str  # "PASS" | "FAIL"
    scenario: str
    finding: str | None = None
    source_length: int
    destination_length: int
    artifact: str
    evidence: str


class AdversarialFinding(BaseModel):
    severity: str
    artifact: str
    finding_type: str
    evidence: str
    remediation: str


# ---------------------------------------------------------------------------
# Evidence Report
# ---------------------------------------------------------------------------


class TamperEvidentReport(BaseModel):
    report_title: str = "TAMPER-EVIDENT EVIDENCE REPORT"
    report_type: str = "TAMPER-EVIDENT"
    generated_at: str
    change_request: dict[str, Any]
    impacted_artifacts: list[dict[str, Any]]
    proposals: list[dict[str, Any]]
    snapshot_ids: list[str]
    scenarios: list[ScenarioResult]
    failures: list[dict[str, Any]]
    adversarial_findings: list[AdversarialFinding]
    final_status: str
    deterministic_hashes: dict[str, str]
    afp_impact: dict[str, Any] | None = None
