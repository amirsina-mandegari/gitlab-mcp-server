"""Tests for create_merge_request tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.create_merge_request import create_merge_request


@pytest.mark.asyncio
async def test_create_merge_request_success(gitlab_credentials, sample_merge_request):
    """Test successful merge request creation."""
    with patch(
        "gitlab_mr_mcp.tools.create_merge_request.api_create_merge_request", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = (201, sample_merge_request, "")

        with patch(
            "gitlab_mr_mcp.tools.create_merge_request.get_project_members", new_callable=AsyncMock
        ) as mock_members:
            mock_members.return_value = (200, [], "")

            with patch(
                "gitlab_mr_mcp.tools.create_merge_request.get_project_labels", new_callable=AsyncMock
            ) as mock_labels:
                mock_labels.return_value = (200, [], "")

                result = await create_merge_request(
                    gitlab_credentials["gitlab_url"],
                    gitlab_credentials["project_id"],
                    gitlab_credentials["access_token"],
                    {
                        "source_branch": "feature-branch",
                        "target_branch": "main",
                        "title": "Add new feature",
                    },
                )

    assert len(result) == 1
    assert "created" in result[0].text.lower() or sample_merge_request["title"] in result[0].text
    assert sample_merge_request["web_url"] in result[0].text


@pytest.mark.asyncio
async def test_create_merge_request_with_assignees(gitlab_credentials, sample_merge_request, sample_project_member):
    """Test creating MR with assignees."""
    with patch(
        "gitlab_mr_mcp.tools.create_merge_request.api_create_merge_request", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = (201, sample_merge_request, "")

        with patch(
            "gitlab_mr_mcp.tools.create_merge_request.get_project_members", new_callable=AsyncMock
        ) as mock_members:
            mock_members.return_value = (200, [sample_project_member], "")

            with patch(
                "gitlab_mr_mcp.tools.create_merge_request.get_project_labels", new_callable=AsyncMock
            ) as mock_labels:
                mock_labels.return_value = (200, [], "")

                result = await create_merge_request(
                    gitlab_credentials["gitlab_url"],
                    gitlab_credentials["project_id"],
                    gitlab_credentials["access_token"],
                    {
                        "source_branch": "feature-branch",
                        "target_branch": "main",
                        "title": "Add new feature",
                        "assignees": [sample_project_member["username"]],
                    },
                )

    assert len(result) == 1
    assert "created" in result[0].text.lower() or sample_merge_request["web_url"] in result[0].text
