"""Tests for list_merge_requests tool using pytest-mock."""

import importlib

import pytest

# Import the actual module file directly (not through tools/__init__.py which re-exports functions)
list_mr_module = importlib.import_module("gitlab_mr_mcp.tools.list_merge_requests")


@pytest.fixture
def sample_merge_request():
    """Return a sample merge request object."""
    return {
        "iid": 42,
        "title": "Add new feature",
        "description": "This MR adds a cool new feature",
        "state": "opened",
        "draft": False,
        "author": {"username": "johndoe", "name": "John Doe"},
        "assignees": [{"username": "reviewer1", "name": "Reviewer One"}],
        "reviewers": [{"username": "reviewer2", "name": "Reviewer Two"}],
        "source_branch": "feature-branch",
        "target_branch": "main",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-16T10:00:00Z",
        "merged_at": None,
        "web_url": "https://gitlab.example.com/project/-/merge_requests/42",
        "labels": ["enhancement", "needs-review"],
        "has_conflicts": False,
        "merge_status": "can_be_merged",
    }


@pytest.mark.asyncio
async def test_list_merge_requests_returns_formatted_results(mocker, sample_merge_request):
    """Test that list_merge_requests formats API response correctly."""
    # Patch using mocker.patch.object on the MODULE
    mock_get_mrs = mocker.patch.object(
        list_mr_module, "get_merge_requests", return_value=(200, [sample_merge_request], "")
    )
    mocker.patch.object(list_mr_module, "get_merge_request_pipeline", return_value=(200, {"status": "success"}, ""))
    mocker.patch.object(list_mr_module, "get_merge_request_changes", return_value=(200, {"changes": []}, ""))

    result = await list_mr_module.list_merge_requests(
        "https://gitlab.example.com",
        "123",
        "test-token",
        {"state": "opened", "limit": 10},
    )

    assert len(result) == 1
    assert sample_merge_request["title"] in result[0].text
    assert str(sample_merge_request["iid"]) in result[0].text
    mock_get_mrs.assert_called_once()


@pytest.mark.asyncio
async def test_list_merge_requests_empty_result(mocker):
    """Test list_merge_requests with no results."""
    mocker.patch.object(list_mr_module, "get_merge_requests", return_value=(200, [], ""))

    result = await list_mr_module.list_merge_requests(
        "https://gitlab.example.com",
        "123",
        "test-token",
        {"state": "opened", "limit": 10},
    )

    assert len(result) == 1
    assert "No merge requests found" in result[0].text
