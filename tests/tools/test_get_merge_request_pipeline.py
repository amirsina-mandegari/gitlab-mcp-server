"""Tests for get_merge_request_pipeline tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.get_merge_request_pipeline import get_merge_request_pipeline


@pytest.mark.asyncio
async def test_get_merge_request_pipeline_returns_formatted_result(gitlab_credentials, sample_pipeline, sample_job):
    """Test that get_merge_request_pipeline formats response correctly."""
    with patch(
        "gitlab_mr_mcp.tools.get_merge_request_pipeline.api_get_merge_request_pipeline", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = (200, sample_pipeline, "")

        with patch(
            "gitlab_mr_mcp.tools.get_merge_request_pipeline.get_pipeline_jobs", new_callable=AsyncMock
        ) as mock_jobs:
            mock_jobs.return_value = (200, [sample_job], "")

            result = await get_merge_request_pipeline(
                gitlab_credentials["gitlab_url"],
                gitlab_credentials["project_id"],
                gitlab_credentials["access_token"],
                {"merge_request_iid": 42},
            )

    assert len(result) == 1
    assert str(sample_pipeline["id"]) in result[0].text
    assert sample_job["name"] in result[0].text


@pytest.mark.asyncio
async def test_get_merge_request_pipeline_no_pipeline(gitlab_credentials):
    """Test when MR has no pipeline."""
    with patch(
        "gitlab_mr_mcp.tools.get_merge_request_pipeline.api_get_merge_request_pipeline", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = (200, None, "")

        result = await get_merge_request_pipeline(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {"merge_request_iid": 42},
        )

    assert len(result) == 1
    assert "no pipeline" in result[0].text.lower() or "not found" in result[0].text.lower()
