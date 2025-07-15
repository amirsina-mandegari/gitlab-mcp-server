from gitlab_api import (
    get_merge_request_reviews as api_get_merge_request_reviews
)
from mcp.types import TextContent
import logging


def get_approval_text(approvals):
    result = ""
    if approvals and approvals.get('approved_by'):
        result += "## Approvals\n"
        for approval in approvals['approved_by']:
            user = approval['user']
            result += f"✅ **{user['name']}** (@{user['username']})\n"
        result += "\n"
    return result


async def get_merge_request_reviews(
    gitlab_url, project_id, access_token, args
):
    logging.info(f"get_merge_request_reviews called with args: {args}")
    mr_iid = args["merge_request_iid"]
    api_result = await api_get_merge_request_reviews(
        gitlab_url, project_id, access_token, mr_iid
    )
    discussions_result = api_result["discussions"]
    discussions_status, discussions, discussions_text = discussions_result
    approvals_status, approvals, approvals_text = api_result["approvals"]
    
    if discussions_status != 200:
        logging.error(
            f"Error fetching discussions {discussions_status}: "
            f"{discussions_text}"
        )
        error_msg = (
            f"Error fetching discussions: {discussions_status} - "
            f"{discussions_text}"
        )
        raise Exception(error_msg)
    
    result = f"# Reviews for MR !{mr_iid}\n\n"
    result += get_approval_text(approvals)
    result += "## Discussions & Reviews\n\n"
    
    for discussion in discussions:
        for note in discussion['notes']:
            if note['system']:
                continue  # Skip system notes
            author_name = note['author']['name']
            author_username = note['author']['username']
            result += f"**{author_name}** (@{author_username})\n"
            result += f"*{note['created_at']}*\n\n"
            if note.get('position'):
                pos = note['position']
                if pos.get('new_path'):
                    result += f"📝 **File**: {pos['new_path']}\n"
                    if pos.get('new_line'):
                        result += f"📍 **Line**: {pos['new_line']}\n"
            result += f"{note['body']}\n\n"
            result += "---\n\n"
    
    return [TextContent(type="text", text=result)] 