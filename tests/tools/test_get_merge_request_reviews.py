"""Tests for get_merge_request_reviews tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.get_merge_request_reviews import get_merge_request_reviews


@pytest.mark.asyncio
async def test_get_merge_request_reviews_returns_discussions(
    gitlab_credentials, sample_merge_request, sample_discussion
):
    """Test that get_merge_request_reviews returns formatted discussions."""
    # The api function returns a dict with "discussions" and "approvals" keys
    reviews_response = {
        "discussions": (200, [sample_discussion], ""),
        "approvals": (200, {"approved": False, "approved_by": []}, ""),
    }

    with patch(
        "gitlab_mr_mcp.tools.get_merge_request_reviews.api_get_merge_request_reviews", new_callable=AsyncMock
    ) as mock_reviews:
        mock_reviews.return_value = reviews_response

        with patch(
            "gitlab_mr_mcp.tools.get_merge_request_reviews.get_merge_request_details", new_callable=AsyncMock
        ) as mock_details:
            mock_details.return_value = (200, sample_merge_request, "")

            with patch(
                "gitlab_mr_mcp.tools.get_merge_request_reviews.get_merge_request_pipeline", new_callable=AsyncMock
            ) as mock_pipeline:
                mock_pipeline.return_value = (200, None, "")

                with patch(
                    "gitlab_mr_mcp.tools.get_merge_request_reviews.get_merge_request_changes", new_callable=AsyncMock
                ) as mock_changes:
                    mock_changes.return_value = (200, {"changes": []}, "")

                    result = await get_merge_request_reviews(
                        gitlab_credentials["gitlab_url"],
                        gitlab_credentials["project_id"],
                        gitlab_credentials["access_token"],
                        {"merge_request_iid": 42},
                    )

    assert len(result) == 1
    # Should contain discussion content
    assert "42" in result[0].text  # MR iid should be present


@pytest.mark.asyncio
async def test_get_merge_request_reviews_no_discussions(gitlab_credentials, sample_merge_request):
    """Test when MR has no discussions."""
    reviews_response = {
        "discussions": (200, [], ""),
        "approvals": (200, {"approved": False, "approved_by": []}, ""),
    }

    with patch(
        "gitlab_mr_mcp.tools.get_merge_request_reviews.api_get_merge_request_reviews", new_callable=AsyncMock
    ) as mock_reviews:
        mock_reviews.return_value = reviews_response

        with patch(
            "gitlab_mr_mcp.tools.get_merge_request_reviews.get_merge_request_details", new_callable=AsyncMock
        ) as mock_details:
            mock_details.return_value = (200, sample_merge_request, "")

            with patch(
                "gitlab_mr_mcp.tools.get_merge_request_reviews.get_merge_request_pipeline", new_callable=AsyncMock
            ) as mock_pipeline:
                mock_pipeline.return_value = (200, None, "")

                with patch(
                    "gitlab_mr_mcp.tools.get_merge_request_reviews.get_merge_request_changes", new_callable=AsyncMock
                ) as mock_changes:
                    mock_changes.return_value = (200, {"changes": []}, "")

                    result = await get_merge_request_reviews(
                        gitlab_credentials["gitlab_url"],
                        gitlab_credentials["project_id"],
                        gitlab_credentials["access_token"],
                        {"merge_request_iid": 42},
                    )

    assert len(result) == 1
