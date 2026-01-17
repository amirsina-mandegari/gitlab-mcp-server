import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import (
    create_merge_request_discussion,
    reply_to_merge_request_discussion,
    resolve_merge_request_discussion,
)
from gitlab_mr_mcp.utils import truncate_text


async def reply_to_review_comment(gitlab_url, project_id, access_token, args):
    """Reply to a specific discussion thread in a merge request review"""
    logging.info(f"reply_to_review_comment called with args: {args}")

    mr_iid = args["merge_request_iid"]
    discussion_id = args["discussion_id"]
    reply_body = args["body"]

    try:
        status, response_data, error_text = await reply_to_merge_request_discussion(
            gitlab_url, project_id, access_token, mr_iid, discussion_id, reply_body
        )

        if status == 201:
            author = response_data.get("author", {}).get("name", "Unknown")
            note_id = response_data.get("id", "unknown")

            result = "# Reply Posted\n\n"
            result += f"**MR**: !{mr_iid}\n"
            result += f"**Discussion**: `{discussion_id}`\n"
            result += f"**Note ID**: `{note_id}`\n"
            result += f"**Author**: {author}\n"
            result += f"**Reply**: {truncate_text(reply_body)}\n"

            return [TextContent(type="text", text=result)]
        else:
            result = "# Error Posting Reply\n\n"
            result += f"**Status**: {status}\n"
            result += f"**Error**: {error_text}\n"
            result += f"**MR**: !{mr_iid}\n"
            result += f"**Discussion**: `{discussion_id}`\n"

            return [TextContent(type="text", text=result)]

    except Exception as e:
        logging.error(f"Unexpected error in reply_to_review_comment: {e}")
        result = "# Unexpected Error\n\n"
        result += f"**Error**: {str(e)}\n"
        result += f"**MR**: !{mr_iid}\n"
        result += f"**Discussion**: `{discussion_id}`\n"

        return [TextContent(type="text", text=result)]


async def create_review_comment(gitlab_url, project_id, access_token, args):
    """Create a new discussion thread in a merge request review"""
    logging.info(f"create_review_comment called with args: {args}")

    mr_iid = args["merge_request_iid"]
    comment_body = args["body"]

    try:
        status, response_data, error_text = await create_merge_request_discussion(
            gitlab_url, project_id, access_token, mr_iid, comment_body
        )

        if status == 201:
            discussion_id = response_data.get("id", "unknown")

            result = "# Discussion Created\n\n"
            result += f"**MR**: !{mr_iid}\n"
            result += f"**Discussion ID**: `{discussion_id}`\n"
            result += f"**Comment**: {truncate_text(comment_body)}\n"

            return [TextContent(type="text", text=result)]
        else:
            result = "# Error Creating Discussion\n\n"
            result += f"**Status**: {status}\n"
            result += f"**Error**: {error_text}\n"
            result += f"**MR**: !{mr_iid}\n"

            return [TextContent(type="text", text=result)]

    except Exception as e:
        logging.error(f"Unexpected error in create_review_comment: {e}")
        result = "# Unexpected Error\n\n"
        result += f"**Error**: {str(e)}\n"
        result += f"**MR**: !{mr_iid}\n"

        return [TextContent(type="text", text=result)]


async def resolve_review_discussion(gitlab_url, project_id, access_token, args):
    """Resolve or unresolve a discussion thread in a merge request review"""
    logging.info(f"resolve_review_discussion called with args: {args}")

    mr_iid = args["merge_request_iid"]
    discussion_id = args["discussion_id"]
    resolved = args.get("resolved", True)

    action = "resolved" if resolved else "reopened"

    try:
        status, response_data, error_text = await resolve_merge_request_discussion(
            gitlab_url, project_id, access_token, mr_iid, discussion_id, resolved
        )

        if status == 200:
            result = f"# Discussion {action.title()}\n\n"
            result += f"**MR**: !{mr_iid}\n"
            result += f"**Discussion**: `{discussion_id}`\n"
            result += f"**Status**: {action.title()}\n"

            return [TextContent(type="text", text=result)]
        else:
            result = f"# Error {action.title()} Discussion\n\n"
            result += f"**Status**: {status}\n"
            result += f"**Error**: {error_text}\n"
            result += f"**MR**: !{mr_iid}\n"
            result += f"**Discussion**: `{discussion_id}`\n"

            return [TextContent(type="text", text=result)]

    except Exception as e:
        logging.error(f"Unexpected error in resolve_review_discussion: {e}")
        result = "# Unexpected Error\n\n"
        result += f"**Error**: {str(e)}\n"
        result += f"**MR**: !{mr_iid}\n"
        result += f"**Discussion**: `{discussion_id}`\n"

        return [TextContent(type="text", text=result)]
