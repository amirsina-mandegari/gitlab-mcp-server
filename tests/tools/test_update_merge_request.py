"""Tests for update_merge_request tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.update_merge_request import update_merge_request


@pytest.mark.asyncio
async def test_update_merge_request_title(gitlab_credentials, sample_merge_request):
    """Test updating merge request title."""
    updated_mr = {**sample_merge_request, "title": "Updated title"}

    with patch(
        "gitlab_mr_mcp.tools.update_merge_request.get_merge_request_details", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = (200, sample_merge_request, "")

        with patch(
            "gitlab_mr_mcp.tools.update_merge_request.api_update_merge_request", new_callable=AsyncMock
        ) as mock_update:
            mock_update.return_value = (200, updated_mr, "")

            with patch(
                "gitlab_mr_mcp.tools.update_merge_request.get_project_members", new_callable=AsyncMock
            ) as mock_members:
                mock_members.return_value = (200, [], "")

                with patch(
                    "gitlab_mr_mcp.tools.update_merge_request.get_project_labels", new_callable=AsyncMock
                ) as mock_labels:
                    mock_labels.return_value = (200, [], "")

                    result = await update_merge_request(
                        gitlab_credentials["gitlab_url"],
                        gitlab_credentials["project_id"],
                        gitlab_credentials["access_token"],
                        {"merge_request_iid": 42, "title": "Updated title"},
                    )

    assert len(result) == 1
    assert "updated" in result[0].text.lower() or "Updated title" in result[0].text


@pytest.mark.asyncio
async def test_update_merge_request_draft_status(gitlab_credentials, sample_merge_request):
    """Test updating merge request draft status."""
    updated_mr = {**sample_merge_request, "draft": True}

    with patch(
        "gitlab_mr_mcp.tools.update_merge_request.get_merge_request_details", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = (200, sample_merge_request, "")

        with patch(
            "gitlab_mr_mcp.tools.update_merge_request.api_update_merge_request", new_callable=AsyncMock
        ) as mock_update:
            mock_update.return_value = (200, updated_mr, "")

            with patch(
                "gitlab_mr_mcp.tools.update_merge_request.get_project_members", new_callable=AsyncMock
            ) as mock_members:
                mock_members.return_value = (200, [], "")

                with patch(
                    "gitlab_mr_mcp.tools.update_merge_request.get_project_labels", new_callable=AsyncMock
                ) as mock_labels:
                    mock_labels.return_value = (200, [], "")

                    result = await update_merge_request(
                        gitlab_credentials["gitlab_url"],
                        gitlab_credentials["project_id"],
                        gitlab_credentials["access_token"],
                        {"merge_request_iid": 42, "draft": True},
                    )

    assert len(result) == 1
