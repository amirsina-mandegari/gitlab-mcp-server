"""Tests for list_project_members tool using pytest-mock."""

import importlib

import pytest

# Import the actual module file directly
members_module = importlib.import_module("gitlab_mr_mcp.tools.list_project_members")


@pytest.fixture
def sample_project_member():
    """Return a sample project member object."""
    return {
        "id": 1,
        "username": "developer",
        "name": "Developer Name",
        "state": "active",
        "access_level": 30,
        "web_url": "https://gitlab.example.com/developer",
    }


@pytest.mark.asyncio
async def test_list_project_members_returns_formatted_list(mocker, sample_project_member):
    """Test that list_project_members returns formatted member list."""
    mocker.patch.object(members_module, "api_get_project_members", return_value=(200, [sample_project_member], ""))

    result = await members_module.list_project_members(
        "https://gitlab.example.com",
        "123",
        "test-token",
        {},
    )

    assert len(result) == 1
    assert sample_project_member["username"] in result[0].text
    assert sample_project_member["name"] in result[0].text


@pytest.mark.asyncio
async def test_list_project_members_empty(mocker):
    """Test list_project_members with no members."""
    mocker.patch.object(members_module, "api_get_project_members", return_value=(200, [], ""))

    result = await members_module.list_project_members(
        "https://gitlab.example.com",
        "123",
        "test-token",
        {},
    )

    assert len(result) == 1
