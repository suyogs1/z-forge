"""Z-FORGE MCP Server — exposes zforge_change_workflow to IBM Bob."""

from __future__ import annotations

import json
from pathlib import Path

# MCP Python SDK: Support modern FastMCP / MCPServer (mcp >= 2.0 renames FastMCP to MCPServer)
try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except (ImportError, ModuleNotFoundError):
    from mcp.server.fastmcp import FastMCP  # type: ignore[attr-defined,no-redef]

# Workspace root relative to this file: packages/mcp/ → project root → workspace/synthetic-banking
_WORKSPACE_ROOT = (
    Path(__file__).resolve().parent.parent.parent / "workspace" / "synthetic-banking"
)

mcp = FastMCP("zforge-mcp")


@mcp.tool(
    description=(
        "Execute the full Z-FORGE change-engineering workflow for an IBM Z mainframe field resize. "
        "Runs blast-radius analysis, generates initial proposals (Snapshot 2), performs deterministic "
        "validation (expects FAIL + DATA_TRUNCATION on first pass), runs the adversarial critic, "
        "applies targeted remediation (Snapshot 3), re-validates (expects PASS), and returns a "
        "tamper-evident evidence report with AFP output impact."
    )
)
def zforge_change_workflow(field: str, new_length: int) -> str:
    """Run the end-to-end Z-FORGE change workflow.

    Args:
        field: COBOL field name to resize (e.g. CUSTOMER-ID).
        new_length: New byte length for the field (e.g. 12).

    Returns:
        JSON string with the complete workflow result.
    """
    from zforge.models import ChangeRequest
    from zforge.orchestration import execute_workflow

    request = ChangeRequest(
        field_name=field,
        target_type=f"PIC X({new_length})",
        old_length=8,
        new_length=new_length,
        description=f"Expand {field} from PIC X(8) to PIC X({new_length})",
    )

    result = execute_workflow(_WORKSPACE_ROOT, request)
    return json.dumps(result, indent=2)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
