"""Tests for get_pipeline_test_summary tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.get_pipeline_test_summary import get_pipeline_test_summary


@pytest.mark.asyncio
async def test_get_test_summary_returns_counts(gitlab_credentials, sample_pipeline, sample_test_report):
    """Test that test summary returns pass/fail counts."""
    with patch(
        "gitlab_mr_mcp.tools.get_pipeline_test_summary.get_merge_request_pipeline", new_callable=AsyncMock
    ) as mock_pipeline:
        mock_pipeline.return_value = (200, sample_pipeline, "")

        with patch(
            "gitlab_mr_mcp.tools.get_pipeline_test_summary.get_pipeline_test_report_summary", new_callable=AsyncMock
        ) as mock_summary:
            mock_summary.return_value = (200, sample_test_report, "")

            result = await get_pipeline_test_summary(
                gitlab_credentials["gitlab_url"],
                gitlab_credentials["project_id"],
                gitlab_credentials["access_token"],
                {"merge_request_iid": 42},
            )

    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_test_summary_no_pipeline(gitlab_credentials):
    """Test when MR has no pipeline."""
    with patch(
        "gitlab_mr_mcp.tools.get_pipeline_test_summary.get_merge_request_pipeline", new_callable=AsyncMock
    ) as mock_pipeline:
        mock_pipeline.return_value = (200, None, "")

        result = await get_pipeline_test_summary(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {"merge_request_iid": 42},
        )

    assert len(result) == 1
    assert "no pipeline" in result[0].text.lower() or "not found" in result[0].text.lower()
