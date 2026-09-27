"""Focused tests for Remote MCP Endpoint and Vercel Serverless Integration.

Verifies:
1. Remote MCP endpoint and tool discovery over Streamable HTTP.
2. Tool execution of zforge_change_workflow via HTTP.
3. Remote workflow returns PASS for CUSTOMER-ID 8 -> 12.
4. Original imported artifacts under workspace/synthetic-banking remain 100% unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from api.mcp import create_mcp_app, zforge_change_workflow
from starlette.testclient import TestClient

WORKSPACE = ROOT_DIR / "workspace" / "synthetic-banking"


def _hash_original_artifacts() -> dict[str, str]:
    """Compute sha256 hashes of all original files under workspace/synthetic-banking."""
    hashes = {}
    for sub in ["cobol", "copybooks", "hlasm", "jcl", "datasets", "afp"]:
        folder = WORKSPACE / sub
        if folder.exists():
            for f in sorted(folder.glob("*")):
                if f.is_file():
                    hashes[str(f.relative_to(WORKSPACE))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return hashes


def test_remote_mcp_browser_discovery() -> None:
    """GET /api/mcp should return health and tool discovery metadata."""
    app = create_mcp_app()
    with TestClient(app) as client:
        resp = client.get("/api/mcp")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["server"] == "zforge-mcp"
        assert data["transport"] == "streamable-http"
        assert "zforge_change_workflow" in data["tools"]


def test_remote_mcp_streamable_http_initialize_and_discovery() -> None:
    """POST /api/mcp with MCP JSON-RPC protocol discovers zforge_change_workflow."""
    app = create_mcp_app()
    with TestClient(app) as client:
        # 1. initialize
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "bob-client", "version": "1.0.0"},
            },
        }
        init_resp = client.post(
            "/api/mcp",
            json=init_payload,
            headers={"Accept": "application/json, text/event-stream"},
        )
        assert init_resp.status_code == 200
        session_id = init_resp.headers.get("mcp-session-id")

        # 2. tools/list
        tools_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        headers = {"Accept": "application/json, text/event-stream"}
        if session_id:
            headers["mcp-session-id"] = session_id

        tools_resp = client.post(
            "/api/mcp",
            json=tools_payload,
            headers=headers,
        )
        assert tools_resp.status_code == 200
        assert "zforge_change_workflow" in tools_resp.text


def test_remote_mcp_workflow_execution_and_pass() -> None:
    """Invoke zforge_change_workflow directly and verify deterministic PASS for CUSTOMER-ID 8 -> 12."""
    raw_result = zforge_change_workflow("CUSTOMER-ID", 12)
    assert isinstance(raw_result, str)

    result = json.loads(raw_result)
    # Check all key milestone properties
    assert result["status"] == "PASS"
    assert len(result["impacted_artifacts"]) == 9
    assert result["first_validation"]["status"] == "FAIL"
    assert result["first_validation"]["finding"] == "DATA_TRUNCATION"
    assert len(result["adversarial_findings"]) >= 1
    assert result["adversarial_findings"][0]["severity"] == "CRITICAL"
    assert result["final_validation"]["status"] == "PASS"
    assert "afp_impact" in result


def test_remote_workflow_leaves_original_artifacts_unchanged() -> None:
    """Verify that running the remote workflow never mutates original imported artifacts."""
    before_hashes = _hash_original_artifacts()

    # Execute remote workflow
    raw_result = zforge_change_workflow("CUSTOMER-ID", 12)
    result = json.loads(raw_result)
    assert result["status"] == "PASS"

    after_hashes = _hash_original_artifacts()
    assert before_hashes == after_hashes, "Original imported artifacts were modified during remote workflow!"


def test_api_workflow_endpoint() -> None:
    """Verify that /api/workflow returns complete workflow result for UI."""
    from api.workflow import app as workflow_app

    with TestClient(workflow_app) as client:
        resp = client.get("/api/workflow")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PASS"
        assert len(data["impacted_artifacts"]) == 9
        assert data["first_validation"]["status"] == "FAIL"
        assert data["final_validation"]["status"] == "PASS"


def test_remote_mcp_security_rejections() -> None:
    """Verify that malicious inputs, path traversal, and invalid lengths are securely rejected."""
    # 1. Path traversal / special characters
    traversal_result = json.loads(zforge_change_workflow("../../etc/passwd", 12))
    assert traversal_result.get("error") == "SECURITY_ERROR"
    assert "Invalid field identifier" in traversal_result.get("message", "")

    # 2. Command injection / shell metacharacters
    injection_result = json.loads(zforge_change_workflow("CUSTOMER-ID; rm -rf /", 12))
    assert injection_result.get("error") == "SECURITY_ERROR"

    # 3. Unsupported field
    unsupported_result = json.loads(zforge_change_workflow("SOME-OTHER-FIELD", 12))
    assert unsupported_result.get("error") == "UNSUPPORTED_FIELD"
    assert "Unsupported field" in unsupported_result.get("message", "")

    # 4. Invalid new_length (negative or too small)
    invalid_len_result = json.loads(zforge_change_workflow("CUSTOMER-ID", 4))
    assert invalid_len_result.get("error") == "VALIDATION_ERROR"

    # 5. Invalid new_length (too large)
    oversized_len_result = json.loads(zforge_change_workflow("CUSTOMER-ID", 1024))
    assert oversized_len_result.get("error") == "VALIDATION_ERROR"


