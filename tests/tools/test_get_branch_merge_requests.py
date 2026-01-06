"""Tests for get_branch_merge_requests tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.get_branch_merge_requests import get_branch_merge_requests


@pytest.mark.asyncio
async def test_get_branch_merge_requests_returns_mrs(gitlab_credentials, sample_merge_request):
    """Test that get_branch_merge_requests returns MRs for a branch."""
    with patch(
        "gitlab_mr_mcp.tools.get_branch_merge_requests.api_get_branch_merge_requests", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = (200, [sample_merge_request], "")

        with patch(
            "gitlab_mr_mcp.tools.get_branch_merge_requests.get_merge_request_pipeline", new_callable=AsyncMock
        ) as mock_pipeline:
            mock_pipeline.return_value = (200, None, "")

            with patch(
                "gitlab_mr_mcp.tools.get_branch_merge_requests.get_merge_request_changes", new_callable=AsyncMock
            ) as mock_changes:
                mock_changes.return_value = (200, {"changes": []}, "")

                result = await get_branch_merge_requests(
                    gitlab_credentials["gitlab_url"],
                    gitlab_credentials["project_id"],
                    gitlab_credentials["access_token"],
                    {"branch_name": "feature-branch"},
                )

    assert len(result) == 1
    assert sample_merge_request["title"] in result[0].text


@pytest.mark.asyncio
async def test_get_branch_merge_requests_no_mrs(gitlab_credentials):
    """Test when branch has no MRs."""
    with patch(
        "gitlab_mr_mcp.tools.get_branch_merge_requests.api_get_branch_merge_requests", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = (200, [], "")

        result = await get_branch_merge_requests(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {"branch_name": "no-mr-branch"},
        )

    assert len(result) == 1
    assert "no merge requests" in result[0].text.lower() or "0" in result[0].text
