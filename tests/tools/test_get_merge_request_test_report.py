"""Tests for get_merge_request_test_report tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.get_merge_request_test_report import get_merge_request_test_report


@pytest.mark.asyncio
async def test_get_test_report_returns_formatted_results(gitlab_credentials, sample_pipeline, sample_test_report):
    """Test that test report is formatted correctly."""
    with patch(
        "gitlab_mr_mcp.tools.get_merge_request_test_report.get_merge_request_pipeline", new_callable=AsyncMock
    ) as mock_pipeline:
        mock_pipeline.return_value = (200, sample_pipeline, "")

        with patch(
            "gitlab_mr_mcp.tools.get_merge_request_test_report.get_pipeline_test_report", new_callable=AsyncMock
        ) as mock_report:
            mock_report.return_value = (200, sample_test_report, "")

            result = await get_merge_request_test_report(
                gitlab_credentials["gitlab_url"],
                gitlab_credentials["project_id"],
                gitlab_credentials["access_token"],
                {"merge_request_iid": 42},
            )

    assert len(result) == 1
    # Should contain test counts
    assert "100" in result[0].text or "98" in result[0].text  # total or success count


@pytest.mark.asyncio
async def test_get_test_report_no_pipeline(gitlab_credentials):
    """Test when MR has no pipeline."""
    with patch(
        "gitlab_mr_mcp.tools.get_merge_request_test_report.get_merge_request_pipeline", new_callable=AsyncMock
    ) as mock_pipeline:
        mock_pipeline.return_value = (200, None, "")

        result = await get_merge_request_test_report(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {"merge_request_iid": 42},
        )

    assert len(result) == 1
    assert "no pipeline" in result[0].text.lower() or "not found" in result[0].text.lower()
