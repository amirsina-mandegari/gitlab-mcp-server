"""Test that all imports work correctly."""


def test_package_import():
    """Test main package can be imported."""
    import gitlab_mr_mcp

    assert hasattr(gitlab_mr_mcp, "__version__")
    assert gitlab_mr_mcp.__version__ == "1.0.0"


def test_server_import():
    """Test server module can be imported."""
    from gitlab_mr_mcp.server import GitLabMCPServer, main, main_sync

    assert GitLabMCPServer is not None
    assert main is not None
    assert main_sync is not None


def test_config_import():
    """Test config module can be imported."""
    from gitlab_mr_mcp.config import get_gitlab_config, get_headers

    assert get_gitlab_config is not None
    assert get_headers is not None


def test_tools_import():
    """Test all tools can be imported."""
    from gitlab_mr_mcp import tools

    # Check all expected tools exist and are callable
    expected_tools = [
        "create_merge_request",
        "create_review_comment",
        "get_branch_merge_requests",
        "get_commit_discussions",
        "get_job_log",
        "get_merge_request_details",
        "get_merge_request_pipeline",
        "get_merge_request_reviews",
        "get_merge_request_test_report",
        "get_pipeline_test_summary",
        "list_merge_requests",
        "list_project_labels",
        "list_project_members",
        "reply_to_review_comment",
        "resolve_review_discussion",
        "update_merge_request",
    ]

    for tool_name in expected_tools:
        assert hasattr(tools, tool_name), f"Missing tool: {tool_name}"
        assert callable(getattr(tools, tool_name)), f"Not callable: {tool_name}"
