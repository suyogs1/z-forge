"""Tamper-evident evidence report generator.

Produces structured JSON reports with SHA-256 deterministic hashes
covering the workspace, snapshots, scenarios, and adversarial findings.
Does NOT use 'signed' or 'cryptographically signed' without private keys.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from zforge.models import (
    AdversarialFinding,
    ChangeRequest,
    ChangeSet,
    ScenarioResult,
    TamperEvidentReport,
)
from zforge.versioning.snapshot import hash_directory


def generate_tamper_evident_report(
    workspace_root: Path | str,
    request: ChangeRequest,
    impacted_artifacts: list[dict[str, Any]],
    proposals: ChangeSet,
    snapshot_ids: list[str],
    scenarios: list[ScenarioResult],
    failures: list[dict[str, Any]],
    adversarial_findings: list[AdversarialFinding],
    final_status: str,
    generated_at: str | None = None,
    afp_impact: dict[str, Any] | None = None,
) -> TamperEvidentReport:
    """Generate a tamper-evident evidence report with deterministic hashes."""
    ws_root = Path(workspace_root).resolve()
    snapshots_dir = ws_root / "snapshots"

    # Compute deterministic hashes for baseline and snapshots
    baseline_hash = hash_directory(ws_root)
    deterministic_hashes: dict[str, str] = {
        "workspace_baseline_sha256": baseline_hash,
    }

    for snap_id in snapshot_ids:
        snap_path = snapshots_dir / snap_id
        if snap_path.exists():
            deterministic_hashes[f"{snap_id}_sha256"] = hash_directory(snap_path)

    # Format proposals
    proposal_records: list[dict[str, Any]] = []
    for p in proposals.proposals:
        proposal_records.append(
            {
                "id": p.id,
                "artifact_id": p.artifact_id,
                "description": p.description,
                "confidence": p.confidence,
                "status": p.status.value,
                "semantic_changes": [
                    {
                        "kind": c.kind.value,
                        "line": c.location.line,
                        "before": c.before,
                        "after": c.after,
                        "impact": c.impact_description,
                    }
                    for c in p.semantic_diff.changes
                ],
            }
        )

    # Compute deterministic report hash over payload contents
    report_dict: dict[str, Any] = {
        "change_request": request.model_dump(),
        "impacted_artifacts": impacted_artifacts,
        "proposals": proposal_records,
        "snapshot_ids": snapshot_ids,
        "scenarios": [s.model_dump() for s in scenarios],
        "failures": failures,
        "adversarial_findings": [f.model_dump() for f in adversarial_findings],
        "final_status": final_status,
    }
    if afp_impact is not None:
        report_dict["afp_impact"] = afp_impact

    canonical_bytes = json.dumps(report_dict, sort_keys=True).encode("utf-8")
    report_hash = hashlib.sha256(canonical_bytes).hexdigest()
    deterministic_hashes["report_sha256"] = report_hash

    report_time = generated_at if generated_at is not None else "2024-01-15T00:00:00Z"

    report = TamperEvidentReport(
        report_title="TAMPER-EVIDENT EVIDENCE REPORT",
        report_type="TAMPER-EVIDENT",
        generated_at=report_time,
        change_request=request.model_dump(),
        impacted_artifacts=impacted_artifacts,
        proposals=proposal_records,
        snapshot_ids=snapshot_ids,
        scenarios=scenarios,
        failures=failures,
        adversarial_findings=adversarial_findings,
        final_status=final_status,
        deterministic_hashes=deterministic_hashes,
        afp_impact=afp_impact,
    )

    # Save to reports directory
    reports_dir = ws_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / "tamper-evident-evidence.json"
    report_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    return report
