"""Tests for list_project_labels tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.list_project_labels import list_project_labels


@pytest.mark.asyncio
async def test_list_project_labels_returns_formatted_list(gitlab_credentials, sample_label):
    """Test that list_project_labels returns formatted label list."""
    with patch("gitlab_mr_mcp.tools.list_project_labels.api_get_project_labels", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (200, [sample_label], "")

        result = await list_project_labels(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {},
        )

    assert len(result) == 1
    assert sample_label["name"] in result[0].text


@pytest.mark.asyncio
async def test_list_project_labels_empty(gitlab_credentials):
    """Test list_project_labels with no labels."""
    with patch("gitlab_mr_mcp.tools.list_project_labels.api_get_project_labels", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (200, [], "")

        result = await list_project_labels(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {},
        )

    assert len(result) == 1
    assert "no" in result[0].text.lower() or "0" in result[0].text
