"""Tests for get_merge_request_details tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.get_merge_request_details import get_merge_request_details


@pytest.mark.asyncio
async def test_get_merge_request_details_returns_formatted_result(gitlab_credentials, sample_merge_request):
    """Test that get_merge_request_details formats response correctly."""
    with patch(
        "gitlab_mr_mcp.tools.get_merge_request_details.api_get_merge_request_details", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = (200, sample_merge_request, "")

        with patch(
            "gitlab_mr_mcp.tools.get_merge_request_details.get_merge_request_pipeline", new_callable=AsyncMock
        ) as mock_pipeline:
            mock_pipeline.return_value = (200, None, "")

            with patch(
                "gitlab_mr_mcp.tools.get_merge_request_details.get_merge_request_changes", new_callable=AsyncMock
            ) as mock_changes:
                mock_changes.return_value = (200, {"changes": []}, "")

                with patch(
                    "gitlab_mr_mcp.tools.get_merge_request_details.get_merge_request_reviews", new_callable=AsyncMock
                ) as mock_reviews:
                    mock_reviews.return_value = (200, [], "")

                    result = await get_merge_request_details(
                        gitlab_credentials["gitlab_url"],
                        gitlab_credentials["project_id"],
                        gitlab_credentials["access_token"],
                        {"merge_request_iid": 42},
                    )

    assert len(result) == 1
    assert sample_merge_request["title"] in result[0].text
    assert sample_merge_request["source_branch"] in result[0].text
    assert sample_merge_request["target_branch"] in result[0].text


@pytest.mark.asyncio
async def test_get_merge_request_details_with_pipeline(gitlab_credentials, sample_merge_request, sample_pipeline):
    """Test that pipeline info is included when available."""
    with patch(
        "gitlab_mr_mcp.tools.get_merge_request_details.api_get_merge_request_details", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = (200, sample_merge_request, "")

        with patch(
            "gitlab_mr_mcp.tools.get_merge_request_details.get_merge_request_pipeline", new_callable=AsyncMock
        ) as mock_pipeline:
            mock_pipeline.return_value = (200, sample_pipeline, "")

            with patch(
                "gitlab_mr_mcp.tools.get_merge_request_details.get_merge_request_changes", new_callable=AsyncMock
            ) as mock_changes:
                mock_changes.return_value = (200, {"changes": []}, "")

                with patch(
                    "gitlab_mr_mcp.tools.get_merge_request_details.get_merge_request_reviews", new_callable=AsyncMock
                ) as mock_reviews:
                    mock_reviews.return_value = (200, [], "")

                    result = await get_merge_request_details(
                        gitlab_credentials["gitlab_url"],
                        gitlab_credentials["project_id"],
                        gitlab_credentials["access_token"],
                        {"merge_request_iid": 42},
                    )

    assert len(result) == 1
    # Pipeline status should be mentioned
    assert "success" in result[0].text.lower() or "✅" in result[0].text
