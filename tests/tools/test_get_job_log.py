"""Tests for get_job_log tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.get_job_log import get_job_log


@pytest.mark.asyncio
async def test_get_job_log_returns_log_content(gitlab_credentials):
    """Test that get_job_log returns log content."""
    mock_log = "Running tests...\nTest 1 passed\nTest 2 passed\nAll tests passed!"

    with patch("gitlab_mr_mcp.tools.get_job_log.get_job_trace", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (200, mock_log, mock_log)

        result = await get_job_log(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {"job_id": 789},
        )

    assert len(result) == 1
    assert "Running tests" in result[0].text or "All tests passed" in result[0].text


@pytest.mark.asyncio
async def test_get_job_log_handles_error(gitlab_credentials):
    """Test get_job_log raises exception on API errors."""
    with patch("gitlab_mr_mcp.tools.get_job_log.get_job_trace", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (404, None, "Not found")

        with pytest.raises(Exception) as exc_info:
            await get_job_log(
                gitlab_credentials["gitlab_url"],
                gitlab_credentials["project_id"],
                gitlab_credentials["access_token"],
                {"job_id": 789},
            )

        assert "404" in str(exc_info.value) or "Not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_job_log_empty_log(gitlab_credentials):
    """Test get_job_log with empty log content."""
    with patch("gitlab_mr_mcp.tools.get_job_log.get_job_trace", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (200, "", "")

        result = await get_job_log(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {"job_id": 789},
        )

    assert len(result) == 1
    # Should handle empty log gracefully
    assert "789" in result[0].text or "log" in result[0].text.lower() or "empty" in result[0].text.lower()
