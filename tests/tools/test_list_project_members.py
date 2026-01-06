"""Tests for list_project_members tool."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.list_project_members import list_project_members


@pytest.mark.asyncio
async def test_list_project_members_returns_formatted_list(gitlab_credentials, sample_project_member):
    """Test that list_project_members returns formatted member list."""
    with patch("gitlab_mr_mcp.tools.list_project_members.api_get_project_members", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (200, [sample_project_member], "")

        result = await list_project_members(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {},
        )

    assert len(result) == 1
    assert sample_project_member["username"] in result[0].text
    assert sample_project_member["name"] in result[0].text


@pytest.mark.asyncio
async def test_list_project_members_empty(gitlab_credentials):
    """Test list_project_members with no members."""
    with patch("gitlab_mr_mcp.tools.list_project_members.api_get_project_members", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (200, [], "")

        result = await list_project_members(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {},
        )

    assert len(result) == 1
    assert "no" in result[0].text.lower() or "0" in result[0].text
