"""AFP impact helper for downstream lineage connections.

Connects CUSTRPT.AFP to upstream COBOL, Copybook, Dataset, and JCL artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def get_afp_lineage_impact(
    workspace_root: Path | str | None = None,
    target_field: str = "CUSTOMER-ID",
) -> dict[str, Any]:
    """Return downstream lineage information for the synthetic AFP document.

    Story:
    CUSTOMER-ID -> CUSTMAST.CPY -> CUSTRPT.CBL -> CUST.REPORT.FILE -> CUSTRPT.JCL -> CUSTRPT.AFP
    """
    if workspace_root is None:
        ws = Path(__file__).resolve().parents[4] / "workspace" / "synthetic-banking"
    else:
        ws = Path(workspace_root).resolve()
    afp_file = ws / "afp" / "CUSTRPT.AFP"

    lineage_path = [
        target_field,
        "copybooks/CUSTMAST.CPY",
        "cobol/CUSTRPT.CBL",
        "datasets/CUST.REPORT.FILE.dsd",
        "jcl/CUSTRPT.JCL",
        "afp/CUSTRPT.AFP",
    ]

    return {
        "artifact": "afp/CUSTRPT.AFP",
        "artifact_id": "afp/CUSTRPT.AFP",
        "type": "AFP",
        "artifact_type": "AFP",
        "exists": afp_file.exists(),
        "description": "Customer Account Statement Print Stream (MO:DCA)",
        "target_field": target_field,
        "producer_jcl": "jcl/CUSTRPT.JCL",
        "dataset": "datasets/CUST.REPORT.FILE.dsd",
        "upstream_program": "cobol/CUSTRPT.CBL",
        "copybook": "copybooks/CUSTMAST.CPY",
        "lineage_chain": lineage_path[1:],
        "lineage_path": lineage_path,
    }
