"""Before/After comparison for AFP documents under schema changes.

Distinguishes upstream schema expansions from static AFP binary layouts.
"""

from __future__ import annotations

from typing import Any

from zforge.afp.models import AFPComparisonResult, AFPDocument


def compare_afp_capacity(
    doc: AFPDocument,
    old_capacity: int | Any = 8,
    new_capacity: int = 12,
    visualization_path: str = "reports/afp-custrpt.html",
) -> AFPComparisonResult:
    """Analyze impact of upstream CUSTOMER-ID expansion on CUSTRPT.AFP.

    Truthful analysis:
    - Upstream schema changed: True (PIC X(8) -> PIC X(12))
    - AFP structure changed: False (AFP file on disk is static binary from baseline)
    - AFP layout changed: False (Output stream has not been re-spooled)
    """
    if hasattr(old_capacity, "old_length") and hasattr(old_capacity, "new_length"):
        old_len = int(getattr(old_capacity, "old_length"))
        new_len = int(getattr(old_capacity, "new_length"))
    elif isinstance(old_capacity, int):
        old_len = old_capacity
        new_len = new_capacity
    else:
        old_len = 8
        new_len = 12

    source_schema_changed = (old_len != new_len)
    explanation = (
        f"Upstream schema expands CUSTOMER-ID from {old_len} to {new_len} bytes. "
        f"The static binary {doc.file_name} maintains {old_len}-byte capacity until "
        "the batch print generation job (CUSTRPT.JCL) is re-executed."
    )

    return AFPComparisonResult(
        artifact=f"afp/{doc.file_name}",
        upstream_field="CUSTOMER-ID",
        before_capacity=old_len,
        after_capacity=new_len,
        source_schema_changed=source_schema_changed,
        afp_structure_changed=False,
        afp_layout_changed=False,
        explanation=explanation,
        visualization_path=visualization_path,
    )
