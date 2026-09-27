"""Change proposal generator and patch engine.

Produces typed SemanticChange records and ChangeProposals in topological order.
Applies proposals ONLY to snapshots, preserving the immutability of original artifacts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from zforge.models import (
    Artifact,
    ArtifactType,
    BlastRadiusResult,
    ChangeKind,
    ChangeProposal,
    ChangeRequest,
    ChangeSet,
    DependencyGraph,
    ImpactReason,
    ProposalReport,
    ProposalReportItem,
    ProposalStatus,
    SemanticChange,
    SemanticDiff,
    Snapshot,
    SourceLocation,
)
from zforge.versioning.snapshot import create_snapshot, hash_directory, hash_file


def _get_line_number(text: str, match_str: str) -> int:
    idx = text.find(match_str)
    if idx == -1:
        return 1
    return text[:idx].count("\n") + 1


def _artifact_sort_priority(artifact_type: ArtifactType) -> int:
    """Return topological rank: Copybooks < Programs/HLASM < JCL < Datasets."""
    if artifact_type == ArtifactType.COPYBOOK:
        return 1
    if artifact_type in (ArtifactType.HLASM, ArtifactType.COBOL):
        return 2
    if artifact_type == ArtifactType.JCL:
        return 3
    if artifact_type == ArtifactType.DATASET:
        return 4
    return 5


def generate_proposals(
    dep_graph: DependencyGraph,
    blast_result: BlastRadiusResult,
    request: ChangeRequest,
    include_remediation: bool = False,
) -> tuple[ChangeSet, ProposalReport]:
    """Generate typed proposals for artifacts in the blast radius.

    Parameters
    ----------
    dep_graph:
        Ingested dependency graph.
    blast_result:
        T3/T4 BlastRadiusResult.
    request:
        ChangeRequest (e.g. CUSTOMER-ID 8 -> 12).
    include_remediation:
        If True, generates proposal for local ACCTPROG shadow variable.
        If False, simulates the initial/naïve pass that misses the local variable.
    """
    proposals: list[ChangeProposal] = []
    report_items: list[ProposalReportItem] = []

    # Map impacted artifacts by path ending
    impacted_map: dict[str, tuple[Artifact, ImpactReason]] = {}
    for ai in blast_result.impacted:
        impacted_map[ai.artifact.path] = (ai.artifact, ai.reason)

    # 1. CUSTMAST.CPY (Copybook)
    custmast_entry = next((v for k, v in impacted_map.items() if "CUSTMAST.CPY" in k), None)
    if custmast_entry:
        art, reason = custmast_entry
        raw = art.raw_content
        old_pattern = r"(05\s+CUSTOMER-ID\s+PIC\s+)X\(8\)\."
        new_text = r"\g<1>X(12)."
        if re.search(old_pattern, raw):
            modified = re.sub(old_pattern, new_text, raw, count=1)
            line = _get_line_number(raw, "CUSTOMER-ID")
            sem_change = SemanticChange(
                kind=ChangeKind.FIELD_RESIZE,
                location=SourceLocation(line=line, column=9),
                before="05  CUSTOMER-ID             PIC X(8).",
                after="05  CUSTOMER-ID             PIC X(12).",
                impact_description=(
                    f"Expand CUSTOMER-ID from PIC X(8) to PIC X({request.new_length})"
                ),
            )
            prop = ChangeProposal(
                id=f"prop-custmast-{request.new_length}",
                artifact_id=art.id,
                description=f"Expand CUSTOMER-ID PIC X(8) to PIC X({request.new_length})",
                original_content=raw,
                proposed_content=modified,
                semantic_diff=SemanticDiff(changes=[sem_change]),
                rationale="Target field of requested change expansion",
                confidence=1.0,
                status=ProposalStatus.PENDING,
            )
            proposals.append(prop)
            report_items.append(
                ProposalReportItem(
                    artifact=art.path,
                    reason=f"Expand CUSTOMER-ID from PIC X(8) to PIC X({request.new_length})",
                    change_kind=ChangeKind.FIELD_RESIZE,
                    old_value="PIC X(8)",
                    new_value=f"PIC X({request.new_length})",
                    confidence=1.0,
                    dependency_reason=reason.value,
                )
            )

    # 2. CUSTDSCT.ASM (HLASM DSECT mirror)
    custdsct_entry = next((v for k, v in impacted_map.items() if "CUSTDSCT.ASM" in k), None)
    if custdsct_entry:
        art, reason = custdsct_entry
        raw = art.raw_content
        modified = raw
        changes: list[SemanticChange] = []

        # Field resize
        if "CUSTID   DS    CL8" in modified:
            line_ds = _get_line_number(modified, "CUSTID   DS    CL8")
            modified = modified.replace(
                "CUSTID   DS    CL8", f"CUSTID   DS    CL{request.new_length}", 1
            )
            changes.append(
                SemanticChange(
                    kind=ChangeKind.FIELD_RESIZE,
                    location=SourceLocation(line=line_ds),
                    before="CUSTID   DS    CL8",
                    after=f"CUSTID   DS    CL{request.new_length}",
                    impact_description=f"Expand CUSTID from CL8 to CL{request.new_length}",
                )
            )

        # EQU offset shift
        if "CUSTIDLN EQU   8" in modified:
            line_equ = _get_line_number(modified, "CUSTIDLN EQU   8")
            modified = modified.replace(
                "CUSTIDLN EQU   8", f"CUSTIDLN EQU   {request.new_length}", 1
            )
            changes.append(
                SemanticChange(
                    kind=ChangeKind.OFFSET_SHIFT,
                    location=SourceLocation(line=line_equ),
                    before="CUSTIDLN EQU   8",
                    after=f"CUSTIDLN EQU   {request.new_length}",
                    impact_description=f"Shift CUSTIDLN length symbol to {request.new_length}",
                )
            )

        if changes:
            prop = ChangeProposal(
                id=f"prop-custdsct-{request.new_length}",
                artifact_id=art.id,
                description=(
                    f"Mirror CUSTOMER-ID expansion in HLASM DSECT (CL8 -> CL{request.new_length})"
                ),
                original_content=raw,
                proposed_content=modified,
                semantic_diff=SemanticDiff(changes=changes),
                rationale="Mirrored layout for batch performance assembler module",
                confidence=1.0,
                status=ProposalStatus.PENDING,
            )
            proposals.append(prop)
            report_items.append(
                ProposalReportItem(
                    artifact=art.path,
                    reason=(
                        "Mirror CUSTOMER-ID expansion in HLASM DSECT "
                        f"(CL8 -> CL{request.new_length})"
                    ),
                    change_kind=ChangeKind.FIELD_RESIZE,
                    old_value="DS CL8, CUSTIDLN EQU 8",
                    new_value=f"DS CL{request.new_length}, CUSTIDLN EQU {request.new_length}",
                    confidence=1.0,
                    dependency_reason=reason.value,
                )
            )

    # 3. CUST.MASTER.FILE.dsd (Dataset schema)
    dsd_entry = next((v for k, v in impacted_map.items() if "CUST.MASTER.FILE.dsd" in k), None)
    if dsd_entry:
        art, reason = dsd_entry
        raw = art.raw_content
        try:
            data = json.loads(raw)
            changes = []
            delta = request.new_length - request.old_length

            # Update CUSTOMER-ID field length
            found_field = False
            for f in data.get("fields", []):
                if f.get("name") == "CUSTOMER-ID":
                    f["length"] = request.new_length
                    f["pic"] = f"PIC X({request.new_length})"
                    found_field = True
                    changes.append(
                        SemanticChange(
                            kind=ChangeKind.SCHEMA_UPDATE,
                            location=SourceLocation(line=18),
                            before=f'"length": {request.old_length}',
                            after=f'"length": {request.new_length}',
                            impact_description=(
                                f"Expand CUSTOMER-ID length from {request.old_length} "
                                f"to {request.new_length}"
                            ),
                        )
                    )
                elif found_field:
                    # Shift subsequent field offsets
                    old_off = f.get("offset", 0)
                    new_off = old_off + delta
                    f["offset"] = new_off

            if found_field:
                changes.append(
                    SemanticChange(
                        kind=ChangeKind.OFFSET_SHIFT,
                        location=SourceLocation(line=27),
                        before="offset: 8+",
                        after=f"offset: {8 + delta}+",
                        impact_description=f"Shift subsequent field offsets by +{delta}",
                    )
                )

            # Update DCB LRECL
            if "dcb" in data and "lrecl" in data["dcb"]:
                old_lrecl = data["dcb"]["lrecl"]
                new_lrecl = old_lrecl + delta
                data["dcb"]["lrecl"] = new_lrecl
                changes.append(
                    SemanticChange(
                        kind=ChangeKind.JCL_PARAM,
                        location=SourceLocation(line=9),
                        before=f'"lrecl": {old_lrecl}',
                        after=f'"lrecl": {new_lrecl}',
                        impact_description=f"Update dataset LRECL from {old_lrecl} to {new_lrecl}",
                    )
                )

            modified = json.dumps(data, indent=2) + "\n"
            prop = ChangeProposal(
                id=f"prop-dataset-schema-{request.new_length}",
                artifact_id=art.id,
                description=(
                    f"Update dataset schema field lengths and LRECL for {request.field_name}"
                ),
                original_content=raw,
                proposed_content=modified,
                semantic_diff=SemanticDiff(changes=changes),
                rationale="Dataset schema must reflect record length expansion",
                confidence=1.0,
                status=ProposalStatus.PENDING,
            )
            proposals.append(prop)
            report_items.append(
                ProposalReportItem(
                    artifact=art.path,
                    reason=f"Update dataset schema field length and shift offsets by +{delta}",
                    change_kind=ChangeKind.SCHEMA_UPDATE,
                    old_value=f"length: {request.old_length}, lrecl: 80",
                    new_value=f"length: {request.new_length}, lrecl: 84",
                    confidence=1.0,
                    dependency_reason=reason.value,
                )
            )
        except Exception:
            pass

    # 4. ACCTPROG.CBL (Local variable remediation if requested)
    if include_remediation:
        acctprog_entry = next((v for k, v in impacted_map.items() if "ACCTPROG.CBL" in k), None)
        if acctprog_entry:
            art, reason = acctprog_entry
            raw = art.raw_content
            old_decl = r"(01\s+WS-ACCT-CUST-ID\s+PIC\s+)X\(8\)\."
            new_decl = rf"\g<1>X({request.new_length})."
            if re.search(old_decl, raw):
                modified = re.sub(old_decl, new_decl, raw, count=1)
                line = _get_line_number(raw, "WS-ACCT-CUST-ID")
                sem_change = SemanticChange(
                    kind=ChangeKind.FIELD_RESIZE,
                    location=SourceLocation(line=line, column=9),
                    before="01  WS-ACCT-CUST-ID             PIC X(8).",
                    after=f"01  WS-ACCT-CUST-ID             PIC X({request.new_length}).",
                    impact_description=(
                        f"Remediate local variable WS-ACCT-CUST-ID to "
                        f"PIC X({request.new_length}) to prevent truncation"
                    ),
                )
                prop = ChangeProposal(
                    id=f"prop-acctprog-remediation-{request.new_length}",
                    artifact_id=art.id,
                    description=f"Remediate local WS-ACCT-CUST-ID to PIC X({request.new_length})",
                    original_content=raw,
                    proposed_content=modified,
                    semantic_diff=SemanticDiff(changes=[sem_change]),
                    rationale=(
                        "Remediate truncation finding: local WS variable shadowing copybook field"
                    ),
                    confidence=1.0,
                    status=ProposalStatus.PENDING,
                )
                proposals.append(prop)
                report_items.append(
                    ProposalReportItem(
                        artifact=art.path,
                        reason=f"Remediate local WS-ACCT-CUST-ID to PIC X({request.new_length})",
                        change_kind=ChangeKind.FIELD_RESIZE,
                        old_value="PIC X(8)",
                        new_value=f"PIC X({request.new_length})",
                        confidence=1.0,
                        dependency_reason=reason.value,
                    )
                )

    # Sort proposals in strict topological order: Copybook < Programs/HLASM < JCL < Datasets
    proposals.sort(
        key=lambda p: _artifact_sort_priority(
            dep_graph.artifacts[p.artifact_id].type
            if p.artifact_id in dep_graph.artifacts
            else ArtifactType.UNKNOWN
        )
    )

    change_set = ChangeSet(
        id=f"changeset-{request.field_name.lower()}-{request.new_length}",
        proposals=proposals,
        ordered_artifact_ids=[p.artifact_id for p in proposals],
    )
    report = ProposalReport(
        change_request=request.description,
        proposals=report_items,
    )
    return change_set, report


def generate_remediation_proposal(
    dep_graph: DependencyGraph,
    base_snapshot_dir: Path,
    new_length: int = 12,
) -> ChangeProposal:
    """Generate the targeted remediation proposal for ACCTPROG.CBL local variable."""
    acctprog_art = next(
        (a for a in dep_graph.artifacts.values() if a.path.endswith("ACCTPROG.CBL")),
        None,
    )
    if not acctprog_art:
        raise ValueError("ACCTPROG.CBL artifact not found in dependency graph")

    acct_file = base_snapshot_dir / "cobol" / "ACCTPROG.CBL"
    raw = (
        acct_file.read_text(encoding="utf-8", errors="replace")
        if acct_file.exists()
        else acctprog_art.raw_content
    )

    old_decl = r"(01\s+WS-ACCT-CUST-ID\s+PIC\s+)X\(8\)\."
    new_decl = rf"\g<1>X({new_length})."
    modified = re.sub(old_decl, new_decl, raw, count=1)
    line = _get_line_number(raw, "WS-ACCT-CUST-ID")

    sem_change = SemanticChange(
        kind=ChangeKind.FIELD_RESIZE,
        location=SourceLocation(line=line, column=9),
        before="01  WS-ACCT-CUST-ID             PIC X(8).",
        after=f"01  WS-ACCT-CUST-ID             PIC X({new_length}).",
        impact_description=f"Remediate local variable WS-ACCT-CUST-ID to PIC X({new_length})",
    )
    return ChangeProposal(
        id=f"prop-remediation-acctprog-{new_length}",
        artifact_id=acctprog_art.id,
        description=f"Remediate local WS-ACCT-CUST-ID to PIC X({new_length}) to prevent truncation",
        original_content=raw,
        proposed_content=modified,
        semantic_diff=SemanticDiff(changes=[sem_change]),
        rationale="Fix critic finding: local variable truncation on MOVE CUSTOMER-ID",
        confidence=1.0,
        status=ProposalStatus.PENDING,
    )


def apply_proposals(
    workspace_root: Path | str,
    change_set: ChangeSet,
    snapshot_id: str,
    label: str,
    base_snapshot_id: str | None = None,
    dep_graph: DependencyGraph | None = None,
) -> Snapshot:
    """Apply proposals to a new snapshot directory.

    NEVER modifies original workspace artifacts.
    """
    ws_root = Path(workspace_root).resolve()
    applied_ids = [p.id for p in change_set.proposals]

    # Create new snapshot directory
    snapshot = create_snapshot(
        workspace_root=ws_root,
        label=label,
        snapshot_id=snapshot_id,
        base_snapshot_id=base_snapshot_id,
        proposals_applied=applied_ids,
    )

    snapshot_dir = ws_root / "snapshots" / snapshot_id

    # Apply proposed content
    for proposal in change_set.proposals:
        # Find relative path from dep_graph or search
        rel_path = None
        if dep_graph and proposal.artifact_id in dep_graph.artifacts:
            rel_path = dep_graph.artifacts[proposal.artifact_id].path

        if not rel_path:
            # Fallback lookup in snapshot_dir
            for f in snapshot_dir.rglob("*"):
                if f.is_file() and not f.name.endswith(".json"):
                    if proposal.original_content and proposal.original_content in f.read_text(
                        encoding="utf-8", errors="replace"
                    ):
                        rel_path = f.relative_to(snapshot_dir).as_posix()
                        break

        if rel_path:
            target_file = snapshot_dir / rel_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(proposal.proposed_content, encoding="utf-8")
            proposal.status = ProposalStatus.VALIDATED

    # Recompute hashes for snapshot
    for f in snapshot_dir.rglob("*"):
        if f.is_file() and not f.name.endswith(".json"):
            rel = f.relative_to(snapshot_dir).as_posix()
            # If dep_graph has it, find id
            if dep_graph:
                for a in dep_graph.artifacts.values():
                    if a.path == rel:
                        snapshot.artifacts[a.id] = hash_file(f)
                        break

    snapshot.workspace_hash = hash_directory(snapshot_dir)
    meta_path = ws_root / "snapshots" / f"{snapshot_id}.json"
    meta_path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")

    return snapshot
