"""Test MCP protocol compliance."""

import json
import os
import subprocess


def test_mcp_initialize_response():
    """Test that server responds correctly to MCP initialize request."""
    # Set required env vars
    env = os.environ.copy()
    env["GITLAB_URL"] = "https://gitlab.com"
    env["GITLAB_ACCESS_TOKEN"] = "test-token"
    env["GITLAB_PROJECT_ID"] = "123"

    # Send initialize request
    init_request = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        }
    )

    result = subprocess.run(
        ["gitlab-mcp"],
        input=init_request,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    # Parse response
    response = json.loads(result.stdout.strip())

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    assert "protocolVersion" in response["result"]
    assert "capabilities" in response["result"]
    assert "serverInfo" in response["result"]


def test_mcp_list_tools_response():
    """Test that server returns all tools."""
    env = os.environ.copy()
    env["GITLAB_URL"] = "https://gitlab.com"
    env["GITLAB_ACCESS_TOKEN"] = "test-token"
    env["GITLAB_PROJECT_ID"] = "123"

    # Send initialize + list_tools
    requests = (
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        )
        + "\n"
        + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    )

    result = subprocess.run(
        ["gitlab-mcp"],
        input=requests,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    # Parse the second response (tools/list)
    lines = result.stdout.strip().split("\n")
    assert len(lines) >= 2

    tools_response = json.loads(lines[1])

    assert tools_response["jsonrpc"] == "2.0"
    assert tools_response["id"] == 2
    assert "result" in tools_response
    assert "tools" in tools_response["result"]

    tools = tools_response["result"]["tools"]
    tool_names = [t["name"] for t in tools]

    # Check all expected tools are present
    expected_tools = [
        "list_merge_requests",
        "get_merge_request_details",
        "get_merge_request_reviews",
        "get_merge_request_pipeline",
        "create_merge_request",
        "update_merge_request",
    ]

    for expected in expected_tools:
        assert expected in tool_names, f"Missing tool: {expected}"


def test_mcp_tool_has_schema():
    """Test that tools have proper input schemas."""
    env = os.environ.copy()
    env["GITLAB_URL"] = "https://gitlab.com"
    env["GITLAB_ACCESS_TOKEN"] = "test-token"
    env["GITLAB_PROJECT_ID"] = "123"

    requests = (
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        )
        + "\n"
        + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    )

    result = subprocess.run(
        ["gitlab-mcp"],
        input=requests,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    lines = result.stdout.strip().split("\n")
    tools_response = json.loads(lines[1])
    tools = tools_response["result"]["tools"]

    for tool in tools:
        assert "name" in tool, "Tool missing name"
        assert "description" in tool, f"Tool {tool.get('name')} missing description"
        assert "inputSchema" in tool, f"Tool {tool.get('name')} missing inputSchema"
        assert tool["inputSchema"]["type"] == "object", f"Tool {tool.get('name')} schema not object type"
