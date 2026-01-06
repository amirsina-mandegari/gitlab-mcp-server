"""Tests for reply_to_review_comment, create_review_comment, and resolve_review_discussion tools."""

from unittest.mock import AsyncMock, patch

import pytest

from gitlab_mr_mcp.tools.reply_to_review_comment import (
    create_review_comment,
    reply_to_review_comment,
    resolve_review_discussion,
)


@pytest.mark.asyncio
async def test_reply_to_review_comment_success(gitlab_credentials):
    """Test successful reply to review comment."""
    mock_note = {
        "id": 123,
        "body": "Thanks for the feedback!",
        "author": {"username": "developer", "name": "Developer"},
        "created_at": "2024-01-15T10:00:00Z",
    }

    with patch(
        "gitlab_mr_mcp.tools.reply_to_review_comment.reply_to_merge_request_discussion", new_callable=AsyncMock
    ) as mock_reply:
        mock_reply.return_value = (201, mock_note, "")

        result = await reply_to_review_comment(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {
                "merge_request_iid": 42,
                "discussion_id": "abc123",
                "body": "Thanks for the feedback!",
            },
        )

    assert len(result) == 1
    assert "reply" in result[0].text.lower() or "success" in result[0].text.lower()


@pytest.mark.asyncio
async def test_create_review_comment_success(gitlab_credentials):
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

    with patch(
        "gitlab_mr_mcp.tools.reply_to_review_comment.create_merge_request_discussion", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = (201, mock_discussion, "")

        result = await create_review_comment(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {
                "merge_request_iid": 42,
                "body": "This needs attention",
            },
        )

    assert len(result) == 1
    assert "created" in result[0].text.lower() or "success" in result[0].text.lower()


@pytest.mark.asyncio
async def test_resolve_review_discussion_success(gitlab_credentials):
    """Test successful resolution of discussion."""
    mock_discussion = {
        "id": "abc123",
        "notes": [{"resolved": True}],
    }

    with patch(
        "gitlab_mr_mcp.tools.reply_to_review_comment.resolve_merge_request_discussion", new_callable=AsyncMock
    ) as mock_resolve:
        mock_resolve.return_value = (200, mock_discussion, "")

        result = await resolve_review_discussion(
            gitlab_credentials["gitlab_url"],
            gitlab_credentials["project_id"],
            gitlab_credentials["access_token"],
            {
                "merge_request_iid": 42,
                "discussion_id": "abc123",
                "resolved": True,
            },
        )

    assert len(result) == 1
    assert "resolved" in result[0].text.lower() or "success" in result[0].text.lower()
