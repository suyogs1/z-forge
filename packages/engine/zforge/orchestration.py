"""End-to-end Z-FORGE change and validation workflow orchestration.

Orchestrates:
1. Request analysis + blast radius
2. Baseline Snapshot 1 creation
3. Initial proposal generation (topological order)
4. Application to Snapshot 2
5. Deterministic scenario execution (FAIL on truncation)
6. Adversarial critic pass (identifies planted failure)
7. Targeted remediation proposal generation
8. Application to Snapshot 3
9. Deterministic scenario re-run (PASS)
10. Adversarial critic re-run (PASS)
11. Tamper-evident evidence report generation
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from zforge.adversarial.critic import AdversarialCritic
from zforge.change.proposals import (
    apply_proposals,
    generate_proposals,
    generate_remediation_proposal,
)
from zforge.graph.blast_radius import blast_radius
from zforge.ingestion.orchestrator import ingest_workspace
from zforge.models import (
    AdversarialFinding,
    ChangeProposal,
    ChangeRequest,
    ChangeSet,
    ProposalReport,
    ScenarioResult,
    Snapshot,
    TamperEvidentReport,
)
from zforge.report.evidence import generate_tamper_evident_report
from zforge.runtime.deterministic_adapter import DeterministicScenarioAdapter
from zforge.versioning.snapshot import create_snapshot


@dataclass
class WorkflowResult:
    snapshot_1: Snapshot
    snapshot_2: Snapshot
    snapshot_3: Snapshot
    initial_change_set: ChangeSet
    initial_report: ProposalReport
    first_scenario_result: ScenarioResult
    first_critic_findings: list[AdversarialFinding]
    initial_validation_passed: bool
    remediation_proposal: ChangeProposal
    second_scenario_result: ScenarioResult
    second_critic_findings: list[AdversarialFinding]
    final_validation_passed: bool
    evidence_report: TamperEvidentReport

    def to_dict(self) -> dict[str, Any]:
        """Return a clean, serializable machine-readable workflow result for Bob/MCP."""
        return {
            "status": "PASS" if self.final_validation_passed else "FAIL",
            "change_request": {
                "field": self.evidence_report.change_request.get("field_name", "CUSTOMER-ID"),
                "old_length": self.evidence_report.change_request.get("old_length", 8),
                "new_length": self.evidence_report.change_request.get("new_length", 12),
            },
            "impacted_artifacts": self.evidence_report.impacted_artifacts,
            "initial_proposals": [
                {
                    "id": p.id,
                    "artifact_id": p.artifact_id,
                    "description": p.description,
                    "confidence": p.confidence,
                }
                for p in self.initial_change_set.proposals
            ],
            "initial_snapshot": self.snapshot_2.id,
            "first_validation": {
                "status": self.first_scenario_result.status,
                "finding": self.first_scenario_result.finding,
            },
            "adversarial_findings": [f.model_dump() for f in self.first_critic_findings],
            "remediation": {
                "status": "APPLIED",
                "snapshot": self.snapshot_3.id,
            },
            "final_validation": {
                "status": "PASS" if self.final_validation_passed else "FAIL",
            },
            "evidence_report": "reports/tamper-evident-evidence.json",
            "afp_impact": self.evidence_report.afp_impact,
        }


def execute_workflow(
    workspace_root: Path | str,
    request: ChangeRequest | None = None,
) -> dict[str, Any]:
    """Execute change workflow and return machine-readable dictionary for Bob/MCP."""
    return run_change_workflow(workspace_root, request).to_dict()


def run_change_workflow(
    workspace_root: Path | str,
    request: ChangeRequest | None = None,
) -> WorkflowResult:
    """Execute the complete deterministic T5/T6 workflow."""
    ws_root = Path(workspace_root).resolve()
    if request is None:
        request = ChangeRequest(
            field_name="CUSTOMER-ID",
            target_type="PIC X(12)",
            old_length=8,
            new_length=12,
            description="Expand CUSTOMER-ID from PIC X(8) to PIC X(12)",
        )

    # 1. Ingest workspace and compute blast radius
    dep_graph = ingest_workspace(ws_root, persist=False)
    br_result = blast_radius(request.field_name, request.description, dep_graph)

    # 2. Snapshot 1: Original pristine workspace
    snap_1 = create_snapshot(
        workspace_root=ws_root,
        label="Original workspace",
        snapshot_id="snapshot-1-baseline",
    )

    # 3. Create initial proposals (without remediation)
    initial_change_set, initial_report = generate_proposals(
        dep_graph=dep_graph,
        blast_result=br_result,
        request=request,
        include_remediation=False,
    )

    # 4. Snapshot 2: Initial proposed expansion
    snap_2 = apply_proposals(
        workspace_root=ws_root,
        change_set=initial_change_set,
        snapshot_id="snapshot-2-proposed",
        label="Initial proposed CUSTOMER-ID expansion",
        base_snapshot_id=None,
        dep_graph=dep_graph,
    )

    # 5. First validation pass on Snapshot 2
    adapter = DeterministicScenarioAdapter()
    snap_2_dir = ws_root / "snapshots" / snap_2.id
    first_scenario = adapter.run_scenario(
        snapshot_dir=snap_2_dir,
        scenario_name="customer-id-expansion",
        customer_id_value="ZENITH123456",
    )

    critic = AdversarialCritic()
    first_critic_findings = critic.inspect_snapshot(snap_2_dir)

    initial_passed = (first_scenario.status == "PASS") and (len(first_critic_findings) == 0)

    failures: list[dict[str, Any]] = []
    if not initial_passed:
        if first_scenario.status != "PASS":
            failures.append(
                {
                    "phase": "initial_validation",
                    "type": "RUNTIME_SCENARIO_FAILURE",
                    "details": first_scenario.model_dump(),
                }
            )
        for f in first_critic_findings:
            failures.append(
                {
                    "phase": "adversarial_critic",
                    "type": f.finding_type,
                    "details": f.model_dump(),
                }
            )

    # 6. Remediation step: Fix ACCTPROG local declaration
    remediation_prop = generate_remediation_proposal(
        dep_graph=dep_graph,
        base_snapshot_dir=snap_2_dir,
        new_length=request.new_length,
    )

    remediation_change_set = ChangeSet(
        id=f"changeset-remediation-{request.new_length}",
        proposals=[remediation_prop],
        ordered_artifact_ids=[remediation_prop.artifact_id],
    )

    # 7. Snapshot 3: Remediated proposal
    snap_3 = apply_proposals(
        workspace_root=ws_root,
        change_set=remediation_change_set,
        snapshot_id="snapshot-3-remediated",
        label="Remediated proposal",
        base_snapshot_id=snap_2.id,
        dep_graph=dep_graph,
    )

    # 8. Second validation pass on Snapshot 3
    snap_3_dir = ws_root / "snapshots" / snap_3.id
    second_scenario = adapter.run_scenario(
        snapshot_dir=snap_3_dir,
        scenario_name="customer-id-expansion",
        customer_id_value="ZENITH123456",
    )
    second_critic_findings = critic.inspect_snapshot(snap_3_dir)

    final_passed = (second_scenario.status == "PASS") and (len(second_critic_findings) == 0)

    # Combine all proposals for evidence report
    all_proposals = ChangeSet(
        id=f"changeset-final-{request.new_length}",
        proposals=initial_change_set.proposals + [remediation_prop],
        ordered_artifact_ids=[p.artifact_id for p in initial_change_set.proposals]
        + [remediation_prop.artifact_id],
    )

    impacted_records: list[dict[str, Any]] = [
        {
            "id": ai.artifact.id,
            "path": ai.artifact.path,
            "type": ai.artifact.type.value,
            "reason": ai.reason.value,
            "details": ai.details,
        }
        for ai in br_result.impacted
    ]

    # 9. AFP downstream impact analysis (isolated, optional)
    afp_impact_dict: dict[str, Any] | None = None
    afp_path = ws_root / "afp" / "CUSTRPT.AFP"
    if afp_path.exists():
        try:
            from zforge.afp import (
                compare_afp_capacity,
                get_afp_lineage_impact,
                parse_afp_file,
                save_afp_visualization,
            )

            afp_doc = parse_afp_file(afp_path)
            afp_comp = compare_afp_capacity(afp_doc, request)
            vis_file = ws_root / "reports" / "afp-custrpt.html"
            save_afp_visualization(afp_doc, vis_file, comparison=afp_comp)

            afp_impact_dict = {
                "artifact": "afp/CUSTRPT.AFP",
                "document_name": afp_doc.document_name,
                "pages_count": len(afp_doc.pages),
                "total_elements": sum(len(p.elements) for p in afp_doc.pages),
                "lineage_path": get_afp_lineage_impact()["lineage_path"],
                "comparison": afp_comp.model_dump(),
                "visualization_path": "reports/afp-custrpt.html",
            }
        except Exception:
            afp_impact_dict = None

    # 10. Emit tamper-evident evidence report
    evidence_report = generate_tamper_evident_report(
        workspace_root=ws_root,
        request=request,
        impacted_artifacts=impacted_records,
        proposals=all_proposals,
        snapshot_ids=[snap_1.id, snap_2.id, snap_3.id],
        scenarios=[first_scenario, second_scenario],
        failures=failures,
        adversarial_findings=first_critic_findings,
        final_status="PASS" if final_passed else "FAIL",
        afp_impact=afp_impact_dict,
    )

    return WorkflowResult(
        snapshot_1=snap_1,
        snapshot_2=snap_2,
        snapshot_3=snap_3,
        initial_change_set=initial_change_set,
        initial_report=initial_report,
        first_scenario_result=first_scenario,
        first_critic_findings=first_critic_findings,
        initial_validation_passed=initial_passed,
        remediation_proposal=remediation_prop,
        second_scenario_result=second_scenario,
        second_critic_findings=second_critic_findings,
        final_validation_passed=final_passed,
        evidence_report=evidence_report,
    )
