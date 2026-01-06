"""Tests for list_merge_requests tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.list_merge_requests import list_merge_requests


@pytest.mark.asyncio
async def test_list_merge_requests_returns_formatted_results(gitlab_credentials, sample_merge_request):
    """Test that list_merge_requests formats API response correctly."""
    with patch("gitlab_mr_mcp.tools.list_merge_requests.get_merge_requests", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (200, [sample_merge_request], "")

        with patch(
            "gitlab_mr_mcp.tools.list_merge_requests.get_merge_request_pipeline", new_callable=AsyncMock
        ) as mock_pipeline:
            mock_pipeline.return_value = (200, {"status": "success"}, "")

            with patch(
                "gitlab_mr_mcp.tools.list_merge_requests.get_merge_request_changes", new_callable=AsyncMock
            ) as mock_changes:
                mock_changes.return_value = (200, {"changes": []}, "")

                result = await list_merge_requests(
                    gitlab_credentials["gitlab_url"],
                    gitlab_credentials["project_id"],
                    gitlab_credentials["access_token"],
                    {"state": "opened", "limit": 10},
                )

    assert len(result) == 1
    assert sample_merge_request["title"] in result[0].text
    assert str(sample_merge_request["iid"]) in result[0].text


@pytest.mark.asyncio
async def test_list_merge_requests_empty_result(gitlab_credentials):
    """Test list_merge_requests with no results."""
    with patch("gitlab_mr_mcp.tools.list_merge_requests.get_merge_requests", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (200, [], "")

        result = await list_merge_requests(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {"state": "opened", "limit": 10},
        )

    assert len(result) == 1
    assert "No merge requests found" in result[0].text


@pytest.mark.asyncio
async def test_list_merge_requests_with_draft(gitlab_credentials, sample_merge_request):
    """Test list_merge_requests shows draft status."""
    sample_merge_request["draft"] = True

    with patch("gitlab_mr_mcp.tools.list_merge_requests.get_merge_requests", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (200, [sample_merge_request], "")

        with patch(
            "gitlab_mr_mcp.tools.list_merge_requests.get_merge_request_pipeline", new_callable=AsyncMock
        ) as mock_pipeline:
            mock_pipeline.return_value = (200, None, "")

            with patch(
                "gitlab_mr_mcp.tools.list_merge_requests.get_merge_request_changes", new_callable=AsyncMock
            ) as mock_changes:
                mock_changes.return_value = (200, {"changes": []}, "")

                result = await list_merge_requests(
                    gitlab_credentials["gitlab_url"],
                    gitlab_credentials["project_id"],
                    gitlab_credentials["access_token"],
                    {"state": "opened", "limit": 10},
                )

    assert len(result) == 1
    # Draft MRs should be indicated somehow in the output
    assert "draft" in result[0].text.lower() or "Draft" in result[0].text
