"""Deterministic scenario runtime adapter.

Validates the synthetic CUSTOMER-ID expansion scenario deterministically.
Does NOT pretend to emulate z/OS or claim mainframe execution fidelity.
"""

from __future__ import annotations

import re
from pathlib import Path

from zforge.models import (
    Artifact,
    Diagnostic,
    ScenarioResult,
    ValidationResult,
)


class DeterministicScenarioAdapter:
    """Deterministic validation adapter for synthetic demonstration workspace."""

    name: str = "DeterministicScenarioAdapter"

    def is_available(self) -> bool:
        return True

    def run_scenario(
        self,
        snapshot_dir: Path | str,
        scenario_name: str = "customer-id-expansion",
        customer_id_value: str = "ZENITH123456",  # 12-character synthetic value
    ) -> ScenarioResult:
        """Execute the deterministic scenario against a snapshot directory.

        Detects 12-byte source -> 8-byte destination truncation in ACCTPROG.
        Returns PASS once WS-ACCT-CUST-ID is expanded to 12 bytes.
        """
        snap_path = Path(snapshot_dir).resolve()

        # 1. Determine source field length from CUSTMAST.CPY in snapshot or input value
        source_length = len(customer_id_value)
        custmast_file = snap_path / "copybooks" / "CUSTMAST.CPY"
        if custmast_file.exists():
            text = custmast_file.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^\s*\d{2}\s+CUSTOMER-ID\s+PIC\s+X\((\d+)\)", text, re.MULTILINE)
            if m:
                source_length = int(m.group(1))

        # 2. Inspect destination field in ACCTPROG.CBL
        acctprog_file = snap_path / "cobol" / "ACCTPROG.CBL"
        if not acctprog_file.exists():
            return ScenarioResult(
                status="FAIL",
                scenario=scenario_name,
                finding="ARTIFACT_NOT_FOUND",
                source_length=source_length,
                destination_length=0,
                artifact="cobol/ACCTPROG.CBL",
                evidence="File missing in snapshot",
            )

        content = acctprog_file.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^\s*\d{2}\s+WS-ACCT-CUST-ID\s+PIC\s+X\((\d+)\)", content, re.MULTILINE)
        dest_length = int(m.group(1)) if m else 8
        evidence_text = f"WS-ACCT-CUST-ID PIC X({dest_length})"

        # 3. Check for truncation in MOVE CUSTOMER-ID TO WS-ACCT-CUST-ID
        if source_length > dest_length:
            return ScenarioResult(
                status="FAIL",
                scenario=scenario_name,
                finding="DATA_TRUNCATION",
                source_length=source_length,
                destination_length=dest_length,
                artifact="cobol/ACCTPROG.CBL",
                evidence=evidence_text,
            )

        return ScenarioResult(
            status="PASS",
            scenario=scenario_name,
            finding=None,
            source_length=source_length,
            destination_length=dest_length,
            artifact="cobol/ACCTPROG.CBL",
            evidence=evidence_text,
        )

    def validate(self, artifact: Artifact, content: str) -> ValidationResult:
        """Adapter interface compliance: validate a single artifact content."""
        # For ACCTPROG, verify whether local WS variable matches copybook expectation
        if artifact.path.endswith("ACCTPROG.CBL"):
            m = re.search(r"WS-ACCT-CUST-ID\s+PIC\s+X\((\d+)\)", content)
            if m and int(m.group(1)) < 12:
                return ValidationResult(
                    proposal_id=artifact.id,
                    passed=False,
                    diagnostics=[
                        Diagnostic(
                            severity="error",
                            message=(
                                f"Local WS-ACCT-CUST-ID PIC X({m.group(1)}) will "
                                "truncate expanded 12-byte CUSTOMER-ID"
                            ),
                        )
                    ],
                    runtime_adapter=self.name,
                )
        return ValidationResult(
            proposal_id=artifact.id,
            passed=True,
            diagnostics=[],
            runtime_adapter=self.name,
        )
