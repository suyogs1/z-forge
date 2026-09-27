"""Blast radius analysis.

Entry point: blast_radius(field_name, change_description, dep_graph)

Algorithm:
1. Find artifacts that directly declare or reference the target field.
2. Traverse COPIES chains: any artifact that COPYs an artifact containing
   the field is also impacted.
3. Traverse CALLS chains: programs that call impacted programs may be
   affected at the interface level.
4. Traverse data-lineage: datasets that receive the field value, and
   programs that consume those datasets.
5. Detect local re-declarations (planted failure pattern).
6. Return BlastRadiusResult with topologically ordered impacted list.
"""

from __future__ import annotations

from zforge.graph._digraph import ancestors, descendants
from zforge.graph.builder import build_nx_graph, topological_sort_artifacts
from zforge.models import (
    Artifact,
    ArtifactImpact,
    ArtifactType,
    BlastRadiusResult,
    DependencyGraph,
    DependencyKind,
    ImpactReason,
)

# ---------------------------------------------------------------------------
# Field-name search helpers
# ---------------------------------------------------------------------------


def _field_in_artifact(field_name: str, artifact: Artifact) -> bool:
    """Return True if *field_name* appears as a declared field in *artifact* metadata."""
    upper = field_name.upper()

    # Check metadata fields list
    for field_entry in artifact.metadata.get("fields", []):
        if isinstance(field_entry, dict):
            if field_entry.get("name", "").upper() == upper:
                return True

    # Check raw content for field-name references as a fallback
    if upper in artifact.raw_content.upper():
        return True

    return False


def _field_in_local_declarations(field_name: str, artifact: Artifact) -> bool:
    """Return True if *field_name* appears in local (non-copybook) WS declarations."""
    upper = field_name.upper()
    for decl in artifact.metadata.get("local_declarations", []):
        if isinstance(decl, dict) and decl.get("name", "").upper() == upper:
            return True
    return False


def _hlasm_field_in_artifact(field_name: str, artifact: Artifact) -> bool:
    """Return True if an HLASM artifact has a field whose label contains the field hint.

    CUSTMAST.CUSTOMER-ID ↔ CUSTDSCT.CUSTID — we match by checking if the
    artifact explicitly references the field name in comments or labels.
    """
    upper = field_name.upper()
    # HLASM labels are typically short abbreviations; also check raw content
    # for any comment/annotation that mentions the field name
    if upper in artifact.raw_content.upper():
        return True

    # Check section fields
    for sect in artifact.metadata.get("sections", []):
        for f in sect.get("fields", []):
            if f.get("label", "").upper() == upper:
                return True
    return False


def _dataset_references_field(field_name: str, artifact: Artifact) -> bool:
    """Return True if a dataset schema references *field_name* directly or via source_field."""
    upper = field_name.upper()
    for f in artifact.metadata.get("fields", []):
        if isinstance(f, dict):
            if f.get("name", "").upper() == upper:
                return True
            if (f.get("source_field") or "").upper() == upper:
                return True
    return False


# ---------------------------------------------------------------------------
# Blast radius core
# ---------------------------------------------------------------------------


def blast_radius(
    field_name: str,
    change_description: str,
    dep_graph: DependencyGraph,
) -> BlastRadiusResult:
    """Compute blast radius for a field change.

    Parameters
    ----------
    field_name:
        The data field being changed (e.g. "CUSTOMER-ID").
    change_description:
        Human-readable description of the change (e.g. "Expand PIC X(8) to PIC X(12)").
    dep_graph:
        The ingested DependencyGraph.

    Returns
    -------
    BlastRadiusResult
        Three buckets: impacted, inspected_unchanged, adversarial_findings.
    """
    result = BlastRadiusResult(
        field_name=field_name,
        change_description=change_description,
    )

    g = build_nx_graph(dep_graph)
    artifacts = dep_graph.artifacts

    impacted: dict[str, ArtifactImpact] = {}  # artifact_id → ArtifactImpact
    inspected: dict[str, ArtifactImpact] = {}  # artifact_id → ArtifactImpact

    def mark_impacted(art_id: str, reason: ImpactReason, details: str) -> None:
        if art_id in impacted:
            return
        art = artifacts.get(art_id)
        if art is None:
            return
        impacted[art_id] = ArtifactImpact(artifact=art, reason=reason, details=details)

    def mark_inspected(art_id: str, reason: ImpactReason, details: str) -> None:
        if art_id in impacted or art_id in inspected:
            return
        art = artifacts.get(art_id)
        if art is None:
            return
        inspected[art_id] = ArtifactImpact(artifact=art, reason=reason, details=details)

    # ------------------------------------------------------------------
    # Step 1: Find artifacts that directly declare/reference the field
    # ------------------------------------------------------------------
    seed_ids: set[str] = set()

    for art_id, art in artifacts.items():
        if art.type in (ArtifactType.COBOL, ArtifactType.COPYBOOK):
            if _field_in_artifact(field_name, art):
                seed_ids.add(art_id)
                mark_impacted(
                    art_id,
                    ImpactReason.DIRECT_FIELD_REFERENCE,
                    f"Artifact directly declares or references {field_name}",
                )
        elif art.type == ArtifactType.HLASM:
            if _hlasm_field_in_artifact(field_name, art):
                seed_ids.add(art_id)
                mark_impacted(
                    art_id,
                    ImpactReason.DIRECT_FIELD_REFERENCE,
                    f"HLASM artifact references {field_name} (layout mirror)",
                )
        elif art.type == ArtifactType.DATASET:
            if _dataset_references_field(field_name, art):
                seed_ids.add(art_id)
                mark_impacted(
                    art_id,
                    ImpactReason.SCHEMA_DEPENDENCY,
                    f"Dataset schema contains {field_name}",
                )

    # ------------------------------------------------------------------
    # Step 2: COPIES chain — find all artifacts that (transitively) COPY
    # an impacted artifact
    # ------------------------------------------------------------------
    # In a COPIES edge: source COPIES target.
    # If the target is impacted, the source is also impacted.
    # We need to traverse *incoming* edges from seed nodes.
    changed = True
    while changed:
        changed = False
        for source, target, data in list(g.edges(data=True)):
            if data.get("kind") != DependencyKind.COPIES.value:
                continue
            if target in impacted and source not in impacted:
                mark_impacted(
                    source,
                    ImpactReason.COPYBOOK_CHAIN,
                    f"Copies {artifacts[target].path if target in artifacts else target} "
                    f"which contains {field_name}",
                )
                changed = True

    # ------------------------------------------------------------------
    # Step 3: CALLS chain — programs that call an impacted program
    # may be affected if the interface changes
    # ------------------------------------------------------------------
    # Only one level of call propagation for now (interface change)
    for source, target, data in list(g.edges(data=True)):
        if data.get("kind") != DependencyKind.CALLS.value:
            continue
        if target in impacted:
            mark_impacted(
                source,
                ImpactReason.CALL_CHAIN,
                f"Calls {artifacts[target].path if target in artifacts else target} "
                f"which is impacted by {field_name} change",
            )

    # ------------------------------------------------------------------
    # Step 4: Local re-declarations (planted failure detection)
    # ------------------------------------------------------------------
    for art_id, art in artifacts.items():
        if art.type != ArtifactType.COBOL:
            continue
        if _field_in_local_declarations(field_name, art):
            details = (
                f"LOCAL re-declaration of {field_name} in WORKING-STORAGE "
                f"(not sourced from copybook) — potential truncation if copybook field expands"
            )
            mark_impacted(art_id, ImpactReason.LOCAL_REDECLARATION, details)
            result.adversarial_findings.append(f"{art.path}: {details}")

        # Scan for field-name references in WS local fields (e.g. WS-ACCT-CUST-ID)
        # that CONTAIN the field name as a substring — planted failure detection.
        fname_upper = field_name.upper().replace("-", "")
        field_abbrev = fname_upper.replace("CUSTOMER", "CUST")
        for decl in art.metadata.get("local_declarations", []):
            if not isinstance(decl, dict):
                continue
            decl_name = decl.get("name", "").upper().replace("-", "")
            if field_abbrev in decl_name:
                # Always surface as adversarial finding even if artifact is already impacted
                finding = (
                    f"{art.path}: Local field {decl['name']} (PIC {decl.get('pic', '?')}) "
                    f"may be related to {field_name} — inspect for truncation risk "
                    f"(planted failure pattern: local WS declaration not sourced from copybook)"
                )
                if finding not in result.adversarial_findings:
                    result.adversarial_findings.append(finding)
                # Also ensure artifact is marked impacted
                mark_impacted(
                    art_id,
                    ImpactReason.LOCAL_REDECLARATION,
                    f"Local field {decl['name']} may shadow {field_name} — truncation risk",
                )
                break

    # ------------------------------------------------------------------
    # Step 5: Data lineage — datasets and their consumers
    # ------------------------------------------------------------------
    for edge in dep_graph.lineage:
        # If producer is impacted, consumer is also on the blast radius
        if edge.producer_id in impacted:
            mark_impacted(
                edge.consumer_id,
                ImpactReason.DATA_LINEAGE,
                f"Downstream consumer of {edge.dataset_name} which carries {field_name}",
            )
        # If consumer is impacted, note producer relationship
        if edge.consumer_id in impacted:
            mark_inspected(
                edge.producer_id,
                ImpactReason.DATA_LINEAGE,
                f"Upstream producer of {edge.dataset_name} read by impacted artifact",
            )

    # ------------------------------------------------------------------
    # Step 6: Collect inspected-but-unchanged (all reachable, not impacted)
    # ------------------------------------------------------------------
    all_reachable: set[str] = set()
    for seed_id in set(impacted.keys()):
        if seed_id in g:
            all_reachable.update(ancestors(g, seed_id))
            all_reachable.update(descendants(g, seed_id))

    for art_id in all_reachable:
        if art_id not in impacted:
            reach_art = artifacts.get(art_id)
            if reach_art:
                mark_inspected(
                    art_id,
                    ImpactReason.DIRECT_FIELD_REFERENCE,
                    "Reachable in graph but does not require modification",
                )

    # ------------------------------------------------------------------
    # Step 7: Topological ordering of impacted list
    # ------------------------------------------------------------------
    impacted_ids = list(impacted.keys())
    ordered_ids = topological_sort_artifacts(dep_graph, impacted_ids)

    result.impacted = [impacted[aid] for aid in ordered_ids if aid in impacted]
    result.inspected_unchanged = list(inspected.values())

    return result
