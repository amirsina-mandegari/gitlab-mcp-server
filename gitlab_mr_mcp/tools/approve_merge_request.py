import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import approve_merge_request as api_approve_merge_request
from gitlab_mr_mcp.gitlab_api import unapprove_merge_request as api_unapprove_merge_request


async def approve_merge_request(gitlab_url, project_id, access_token, args):
    """Approve a merge request"""
    logging.info(f"approve_merge_request called with args: {args}")

    mr_iid = args.get("merge_request_iid")
    if not mr_iid:
        raise ValueError("merge_request_iid is required")

    sha = args.get("sha")

    status, data, error = await api_approve_merge_request(gitlab_url, project_id, access_token, mr_iid, sha)

    if status in (200, 201):
        result = "# Merge Request Approved\n\n"
        result += f"**MR**: !{mr_iid}\n"

        # Show approval info
        approved_by = data.get("approved_by", [])
        if approved_by:
            approvers = ", ".join(f"@{a['user']['username']}" for a in approved_by)
            result += f"**Approved By**: {approvers}\n"

        approvals_required = data.get("approvals_required", 0)
        approvals_left = data.get("approvals_left", 0)
        result += f"**Approvals**: {len(approved_by)}/{approvals_required}\n"

        if approvals_left == 0:
            result += "**Status**: All required approvals received\n"
        else:
            result += f"**Status**: {approvals_left} more approval(s) needed\n"

        return [TextContent(type="text", text=result)]

    elif status == 401:
        result = "# Approval Failed: Unauthorized\n\n"
        result += "Your access token doesn't have permission to approve.\n"
        result += "Ensure your token has `api` scope.\n"
        return [TextContent(type="text", text=result)]

    elif status == 403:
        result = "# Approval Failed: Forbidden\n\n"
        result += f"**MR**: !{mr_iid}\n"
        result += "You cannot approve this merge request.\n\n"
        result += "**Possible reasons**:\n"
        result += "- You are the author (can't self-approve)\n"
        result += "- You already approved\n"
        result += "- You don't have permission to approve\n"
        return [TextContent(type="text", text=result)]

    elif status == 404:
        result = "# Approval Failed: Not Found\n\n"
        result += f"Merge request !{mr_iid} not found.\n"
        return [TextContent(type="text", text=result)]

    else:
        error_msg = data.get("message", error) if isinstance(data, dict) else error
        logging.error(f"Error approving MR: {status} - {error_msg}")
        raise Exception(f"Error approving merge request: {status} - {error_msg}")


async def unapprove_merge_request(gitlab_url, project_id, access_token, args):
    """Unapprove (revoke approval from) a merge request"""
    logging.info(f"unapprove_merge_request called with args: {args}")

    mr_iid = args.get("merge_request_iid")
    if not mr_iid:
        raise ValueError("merge_request_iid is required")

    status, data, error = await api_unapprove_merge_request(gitlab_url, project_id, access_token, mr_iid)

    if status in (200, 201):
        result = "# Approval Revoked\n\n"
        result += f"**MR**: !{mr_iid}\n"
        result += "Your approval has been removed.\n"

        approvals_left = data.get("approvals_left", 0)
        if approvals_left > 0:
            result += f"**Status**: {approvals_left} approval(s) now needed\n"

        return [TextContent(type="text", text=result)]

    elif status == 401:
        result = "# Unapproval Failed: Unauthorized\n\n"
        result += "Your access token doesn't have permission.\n"
        return [TextContent(type="text", text=result)]

    elif status == 403:
        result = "# Unapproval Failed: Forbidden\n\n"
        result += f"**MR**: !{mr_iid}\n"
        result += "You cannot unapprove this merge request.\n"
        result += "You may not have previously approved it.\n"
        return [TextContent(type="text", text=result)]

    elif status == 404:
        result = "# Unapproval Failed: Not Found\n\n"
        result += f"Merge request !{mr_iid} not found.\n"
        return [TextContent(type="text", text=result)]

    else:
        error_msg = data.get("message", error) if isinstance(data, dict) else error
        logging.error(f"Error unapproving MR: {status} - {error_msg}")
        raise Exception(f"Error unapproving merge request: {status} - {error_msg}")
