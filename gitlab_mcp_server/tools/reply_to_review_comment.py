import logging

from mcp.types import TextContent

from gitlab_mcp_server.gitlab_api import (
    create_merge_request_discussion,
    reply_to_merge_request_discussion,
    resolve_merge_request_discussion,
)


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
            author_name = response_data.get("author", {}).get("name", "Unknown")
            note_id = response_data.get("id", "unknown")

            result = "✅ **Reply posted successfully!**\n\n"
            result += f"**Merge Request**: !{mr_iid}\n"
            result += f"**Discussion ID**: `{discussion_id}`\n"
            result += f"**Note ID**: `{note_id}`\n"
            result += f"**Author**: {author_name}\n"
            reply_preview = reply_body[:100] + ("..." if len(reply_body) > 100 else "")
            result += f"**Reply**: {reply_preview}\n"

            return [TextContent(type="text", text=result)]
        else:
            error_msg = "❌ **Error posting reply**\n\n"
            error_msg += f"**Status**: {status}\n"
            error_msg += f"**Error**: {error_text}\n"
            error_msg += f"**MR**: !{mr_iid}\n"
            error_msg += f"**Discussion**: {discussion_id}\n"

            return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        logging.error(f"Unexpected error in reply_to_review_comment: {e}")
        error_result = "❌ **Unexpected error**\n\n"
        error_result += f"**Error**: {str(e)}\n"
        error_result += f"**MR**: !{mr_iid}\n"
        error_result += f"**Discussion**: {discussion_id}\n"

        return [TextContent(type="text", text=error_result)]


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
            author_name = response_data.get("author", {}).get("name", "Unknown")
            discussion_id = response_data.get("id", "unknown")

            result = "✅ **New discussion created!**\n\n"
            result += f"**Merge Request**: !{mr_iid}\n"
            result += f"**Discussion ID**: `{discussion_id}`\n"
            result += f"**Author**: {author_name}\n"
            result += f"**Comment**: {comment_body[:100]}{'...' if len(comment_body) > 100 else ''}\n"

            return [TextContent(type="text", text=result)]
        else:
            error_msg = "❌ **Error creating discussion**\n\n"
            error_msg += f"**Status**: {status}\n"
            error_msg += f"**Error**: {error_text}\n"
            error_msg += f"**MR**: !{mr_iid}\n"

            return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        logging.error(f"Unexpected error in create_review_comment: {e}")
        error_result = "❌ **Unexpected error**\n\n"
        error_result += f"**Error**: {str(e)}\n"
        error_result += f"**MR**: !{mr_iid}\n"

        return [TextContent(type="text", text=error_result)]


async def resolve_review_discussion(gitlab_url, project_id, access_token, args):
    """Resolve or unresolve a discussion thread in a merge request review"""
    logging.info(f"resolve_review_discussion called with args: {args}")

    mr_iid = args["merge_request_iid"]
    discussion_id = args["discussion_id"]
    resolved = args.get("resolved", True)

    try:
        status, response_data, error_text = await resolve_merge_request_discussion(
            gitlab_url, project_id, access_token, mr_iid, discussion_id, resolved
        )

        if status == 200:
            action = "resolved" if resolved else "reopened"

            result = f"✅ **Discussion {action}!**\n\n"
            result += f"**Merge Request**: !{mr_iid}\n"
            result += f"**Discussion ID**: `{discussion_id}`\n"
            result += f"**Status**: {'✅ Resolved' if resolved else '🔄 Reopened'}\n"

            return [TextContent(type="text", text=result)]
        else:
            error_msg = f"❌ **Error {action} discussion**\n\n"
            error_msg += f"**Status**: {status}\n"
            error_msg += f"**Error**: {error_text}\n"
            error_msg += f"**MR**: !{mr_iid}\n"
            error_msg += f"**Discussion**: {discussion_id}\n"

            return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        logging.error(f"Unexpected error in resolve_review_discussion: {e}")
        error_result = "❌ **Unexpected error**\n\n"
        error_result += f"**Error**: {str(e)}\n"
        error_result += f"**MR**: !{mr_iid}\n"
        error_result += f"**Discussion**: {discussion_id}\n"

        return [TextContent(type="text", text=error_result)]
