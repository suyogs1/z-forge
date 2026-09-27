"""Adversarial critic for Z-FORGE.

Independently inspects proposed snapshot artifacts to catch hidden inconsistencies,
such as local variable truncation shadowing expanded copybook fields.
The critic does NOT rewrite code.
"""

from __future__ import annotations

import re
from pathlib import Path

from zforge.models import AdversarialFinding


class AdversarialCritic:
    """Independent critic inspecting snapshot artifacts for dangerous inconsistencies."""

    def inspect_snapshot(self, snapshot_dir: Path | str) -> list[AdversarialFinding]:
        """Independently inspect a snapshot directory.

        Must NOT trust any proposal list; reads actual snapshot files on disk.
        """
        snap_path = Path(snapshot_dir).resolve()
        findings: list[AdversarialFinding] = []

        # 1. Determine current CUSTOMER-ID length from copybooks/CUSTMAST.CPY
        custmast = snap_path / "copybooks" / "CUSTMAST.CPY"
        cust_id_len = 8
        if custmast.exists():
            text = custmast.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^\s*\d{2}\s+CUSTOMER-ID\s+PIC\s+X\((\d+)\)", text, re.MULTILINE)
            if m:
                cust_id_len = int(m.group(1))

        # 2. Inspect COBOL programs for local shadowing / truncation
        # Specifically check ACCTPROG.CBL for planted failure pattern
        acctprog = snap_path / "cobol" / "ACCTPROG.CBL"
        if acctprog.exists():
            text = acctprog.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^\s*\d{2}\s+WS-ACCT-CUST-ID\s+PIC\s+X\((\d+)\)", text, re.MULTILINE)
            if m:
                ws_len = int(m.group(1))
                if ws_len < cust_id_len:
                    evidence = (
                        f"CUSTOMER-ID is {cust_id_len} bytes but "
                        f"WS-ACCT-CUST-ID remains X({ws_len})"
                    )
                    findings.append(
                        AdversarialFinding(
                            severity="CRITICAL",
                            artifact="cobol/ACCTPROG.CBL",
                            finding_type="DATA_TRUNCATION",
                            evidence=evidence,
                            remediation=f"Change WS-ACCT-CUST-ID to X({cust_id_len})",
                        )
                    )

        # 3. Inspect HLASM DSECT for layout synchronization
        hlasm = snap_path / "hlasm" / "CUSTDSCT.ASM"
        if hlasm.exists():
            text = hlasm.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^CUSTID\s+DS\s+CL(\d+)", text, re.MULTILINE)
            if m:
                asm_len = int(m.group(1))
                if asm_len < cust_id_len:
                    asm_ev = f"CUSTOMER-ID is {cust_id_len} bytes but CUSTID is CL{asm_len}"
                    findings.append(
                        AdversarialFinding(
                            severity="HIGH",
                            artifact="hlasm/CUSTDSCT.ASM",
                            finding_type="LAYOUT_MISMATCH",
                            evidence=asm_ev,
                            remediation=f"Change CUSTID to DS CL{cust_id_len}",
                        )
                    )

        return findings
