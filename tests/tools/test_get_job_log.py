"""Tests for get_job_log tool using pytest-mock."""

import importlib

import pytest

# Import the actual module file directly
job_log_module = importlib.import_module("gitlab_mr_mcp.tools.get_job_log")


@pytest.mark.asyncio
async def test_get_job_log_returns_log_content(mocker):
    """Test that get_job_log returns log content."""
    mock_log = "Running tests...\nTest 1 passed\nTest 2 passed\nAll tests passed!"

    mocker.patch.object(job_log_module, "get_job_trace", return_value=(200, mock_log, mock_log))

    result = await job_log_module.get_job_log(
        "https://gitlab.example.com",
        "123",
        "test-token",
        {"job_id": 789},
    )

    assert len(result) == 1
    assert "789" in result[0].text


@pytest.mark.asyncio
async def test_get_job_log_handles_error(mocker):
    """Test get_job_log with API error."""
    mocker.patch.object(job_log_module, "get_job_trace", return_value=(404, None, "Not found"))

    with pytest.raises(Exception) as exc_info:
        await job_log_module.get_job_log(
            "https://gitlab.example.com",
            "123",
            "test-token",
            {"job_id": 789},
        )

    assert "404" in str(exc_info.value) or "Not found" in str(exc_info.value)
