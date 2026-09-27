from __future__ import annotations

import json

import server


def test_mcp_server_initialization() -> None:
    """Verify that MCP server initializes with expected name."""
    assert server.mcp.name == "zforge-mcp"


def test_tool_registration() -> None:
    """Verify that zforge_change_workflow tool is registered on the server."""
    # FastMCP / MCPServer internal tool list
    if hasattr(server.mcp, "_tool_manager"):
        tool_names = [t.name for t in server.mcp._tool_manager.list_tools()]
        assert "zforge_change_workflow" in tool_names


def test_tool_execution() -> None:
    """Verify invoking zforge_change_workflow produces structured workflow result."""
    result_raw = server.zforge_change_workflow("CUSTOMER-ID", 12)
    assert isinstance(result_raw, str)
    
    data = json.loads(result_raw)
    assert data["status"] == "PASS"
    assert len(data["impacted_artifacts"]) == 9
    assert data["first_validation"]["status"] == "FAIL"
    assert data["first_validation"]["finding"] == "DATA_TRUNCATION"
    assert len(data["adversarial_findings"]) >= 1
    assert data["final_validation"]["status"] == "PASS"
    assert "afp_impact" in data
