"""Tests for reply_to_review_comment tools using pytest-mock."""

import importlib

import pytest

# Import the actual module file directly
reply_module = importlib.import_module("gitlab_mr_mcp.tools.reply_to_review_comment")


@pytest.mark.asyncio
async def test_reply_to_review_comment_success(mocker):
    """Test successful reply to review comment."""
    mock_note = {
        "id": 123,
        "body": "Thanks for the feedback!",
        "author": {"username": "developer", "name": "Developer"},
        "created_at": "2024-01-15T10:00:00Z",
    }

    mocker.patch.object(reply_module, "reply_to_merge_request_discussion", return_value=(201, mock_note, ""))

    result = await reply_module.reply_to_review_comment(
        "https://gitlab.example.com",
        "123",
        "test-token",
        {
            "merge_request_iid": 42,
            "discussion_id": "abc123",
            "body": "Thanks for the feedback!",
        },
    )

    assert len(result) == 1
    assert "success" in result[0].text.lower() or "reply" in result[0].text.lower()


@pytest.mark.asyncio
async def test_create_review_comment_success(mocker):
    """Test successful creation of review comment."""
    mock_discussion = {
        "id": "new123",
        "notes": [
            {
                "id": 456,
                "body": "This needs attention",
                "author": {"username": "reviewer", "name": "Reviewer"},
            }
        ],
    }

    mocker.patch.object(reply_module, "create_merge_request_discussion", return_value=(201, mock_discussion, ""))

    result = await reply_module.create_review_comment(
        "https://gitlab.example.com",
        "123",
        "test-token",
        {
            "merge_request_iid": 42,
            "body": "This needs attention",
        },
    )

    assert len(result) == 1
    assert "success" in result[0].text.lower() or "created" in result[0].text.lower()


@pytest.mark.asyncio
async def test_resolve_review_discussion_success(mocker):
    """Test successful resolution of discussion."""
    mock_discussion = {
        "id": "abc123",
        "notes": [{"resolved": True}],
    }

    mocker.patch.object(reply_module, "resolve_merge_request_discussion", return_value=(200, mock_discussion, ""))

    result = await reply_module.resolve_review_discussion(
        "https://gitlab.example.com",
        "123",
        "test-token",
        {
            "merge_request_iid": 42,
            "discussion_id": "abc123",
            "resolved": True,
        },
    )

    assert len(result) == 1
    assert "success" in result[0].text.lower() or "resolved" in result[0].text.lower()
