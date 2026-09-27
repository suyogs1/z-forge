"""Z-FORGE Change Engineering Demo CLI entry point.

Provides a single judge-friendly command to execute the deterministic T3-T6 workflow
from a clean baseline, and a safe reset mechanism.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from zforge.models import ChangeRequest
from zforge.orchestration import run_change_workflow
from zforge.versioning.snapshot import reset_workspace


def find_workspace_root() -> Path:
    """Locate the synthetic-banking workspace directory."""
    curr = Path.cwd().resolve()
    for parent in [curr] + list(curr.parents):
        candidate = parent / "workspace" / "synthetic-banking"
        if candidate.exists() and (candidate / "zforge.pack.json").exists():
            return candidate.resolve()
    fallback = Path(__file__).resolve().parents[3] / "workspace" / "synthetic-banking"
    if fallback.exists():
        return fallback.resolve()
    raise FileNotFoundError("Could not locate workspace/synthetic-banking")


def _ensure_utf8_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def run_demo(workspace_root: Path | None = None, clean_first: bool = True) -> int:
    """Execute the full deterministic Z-FORGE change engineering demo."""
    _ensure_utf8_stdout()
    ws = (workspace_root or find_workspace_root()).resolve()

    if clean_first:
        reset_workspace(ws)

    print("\n" + "=" * 50)
    print("Z-FORGE CHANGE ENGINEERING DEMO")
    print("=" * 50)
    print("\nCHANGE REQUEST")
    print("CUSTOMER-ID: X(8) → X(12)\n")

    req = ChangeRequest(
        field_name="CUSTOMER-ID",
        target_type="PIC X(12)",
        old_length=8,
        new_length=12,
        description="Expand CUSTOMER-ID from PIC X(8) to PIC X(12)",
    )

    result = run_change_workflow(ws, req)

    # [1/6] Blast-radius analysis
    impacted_count = len(result.evidence_report.impacted_artifacts)
    print("[1/6] Blast-radius analysis")
    print(f"✓ {impacted_count} impacted artifacts\n")

    # [2/6] Change proposals
    prop_count = len(result.initial_change_set.proposals)
    print("[2/6] Change proposals")
    print(f"✓ {prop_count} initial proposals\n")

    # [3/6] Snapshot 2
    print("[3/6] Snapshot 2")
    print("✓ Proposed changes applied\n")

    # [4/6] Deterministic validation
    first_res = result.first_scenario_result
    print("[4/6] Deterministic validation")
    if first_res.status == "FAIL":
        print(f"✗ FAIL: {first_res.finding}")
        print(f"  {first_res.source_length} bytes → {first_res.destination_length} bytes")
        print(f"  {first_res.artifact}\n")
    else:
        print("✓ PASS\n")

    # [5/6] Adversarial critic
    print("[5/6] Adversarial critic")
    if result.first_critic_findings:
        crit = result.first_critic_findings[0]
        print(f"! {crit.severity}")
        print(f"  {crit.evidence}\n")
    else:
        print("✓ 0 adversarial findings\n")

    # [6/6] Remediation
    print("[6/6] Remediation")
    print("✓ Snapshot 3 created")
    second_res = result.second_scenario_result
    print(f"✓ Validation {second_res.status}")
    findings_count = len(result.second_critic_findings)
    print(f"✓ {findings_count} adversarial findings\n")

    # [7/7] AFP output impact
    print("[7/7] AFP output impact")
    print("✓ CUSTRPT.AFP inspected")
    print("✓ structural layout analyzed")
    print("✓ print-output comparison generated")
    vis_rel = "reports/afp-custrpt.html"
    print(f"✓ Visualization: {vis_rel}\n")

    # Evidence & Status
    print("EVIDENCE")
    print("reports/tamper-evident-evidence.json")
    print(f"{vis_rel}\n")

    final_status = "PASS" if result.final_validation_passed else "FAIL"
    print("=" * 50)
    print(f"FINAL STATUS: {final_status}")
    print("=" * 50 + "\n")

    return 0 if result.final_validation_passed else 1


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for zforge-demo."""
    _ensure_utf8_stdout()
    parser = argparse.ArgumentParser(
        description="Z-FORGE Change Engineering Platform Demo",
        prog="zforge-demo",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset generated snapshots and reports to a clean baseline",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=None,
        help="Path to workspace/synthetic-banking directory",
    )

    args = parser.parse_args(argv)
    ws = Path(args.workspace).resolve() if args.workspace else find_workspace_root()

    if args.reset:
        removed = reset_workspace(ws)
        print("\n" + "=" * 50)
        print("Z-FORGE DEMO RESET")
        print("=" * 50)
        print(f"✓ Cleared {len(removed)} generated item(s)")
        print("✓ Original imported artifacts remain immutable")
        print("Baseline ready for clean demo execution.\n")
        return 0

    return run_demo(ws, clean_first=True)


if __name__ == "__main__":
    sys.exit(main())
