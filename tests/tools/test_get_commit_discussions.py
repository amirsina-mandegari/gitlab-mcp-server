"""Tests for get_commit_discussions tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.get_commit_discussions import get_commit_discussions


@pytest.mark.asyncio
async def test_get_commit_discussions_returns_discussions(gitlab_credentials, sample_discussion):
    """Test that commit discussions are returned."""
    mock_commits = [
        {
            "id": "abc123",
            "short_id": "abc123",
            "title": "Fix bug",
            "author_name": "Developer",
            "created_at": "2024-01-15T10:00:00Z",
        }
    ]

    with patch(
        "gitlab_mr_mcp.tools.get_commit_discussions.get_merge_request_commits", new_callable=AsyncMock
    ) as mock_commits_fn:
        mock_commits_fn.return_value = (200, mock_commits, "")

        with patch(
            "gitlab_mr_mcp.tools.get_commit_discussions.get_merge_request_discussions_paginated", new_callable=AsyncMock
        ) as mock_discussions:
            mock_discussions.return_value = (200, [sample_discussion], "")

            result = await get_commit_discussions(
                gitlab_credentials["gitlab_url"],
                gitlab_credentials["project_id"],
                gitlab_credentials["access_token"],
                {"merge_request_iid": 42},
            )

    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_commit_discussions_no_commits(gitlab_credentials):
    """Test when MR has no commits."""
    with patch(
        "gitlab_mr_mcp.tools.get_commit_discussions.get_merge_request_commits", new_callable=AsyncMock
    ) as mock_commits:
        mock_commits.return_value = (200, [], "")

        with patch(
            "gitlab_mr_mcp.tools.get_commit_discussions.get_merge_request_discussions_paginated", new_callable=AsyncMock
        ) as mock_discussions:
            mock_discussions.return_value = (200, [], "")

            result = await get_commit_discussions(
                gitlab_credentials["gitlab_url"],
                gitlab_credentials["project_id"],
                gitlab_credentials["access_token"],
                {"merge_request_iid": 42},
            )

    assert len(result) == 1
