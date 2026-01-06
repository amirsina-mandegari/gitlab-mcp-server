"""Tests for list_project_labels tool using pytest-mock."""

import importlib

import pytest

# Import the actual module file directly
labels_module = importlib.import_module("gitlab_mr_mcp.tools.list_project_labels")


@pytest.fixture
def sample_label():
    """Return a sample label object."""
    return {
        "id": 1,
        "name": "bug",
        "color": "#ff0000",
        "description": "Bug label",
    }


@pytest.mark.asyncio
async def test_list_project_labels_returns_formatted_list(mocker, sample_label):
    """Test that list_project_labels returns formatted label list."""
    mocker.patch.object(labels_module, "api_get_project_labels", return_value=(200, [sample_label], ""))

    result = await labels_module.list_project_labels(
        "https://gitlab.example.com",
        "123",
        "test-token",
        {},
    )

    assert len(result) == 1
    assert sample_label["name"] in result[0].text


@pytest.mark.asyncio
async def test_list_project_labels_empty(mocker):
    """Test list_project_labels with no labels."""
    mocker.patch.object(labels_module, "api_get_project_labels", return_value=(200, [], ""))

    result = await labels_module.list_project_labels(
        "https://gitlab.example.com",
        "123",
        "test-token",
        {},
    )

    assert len(result) == 1
