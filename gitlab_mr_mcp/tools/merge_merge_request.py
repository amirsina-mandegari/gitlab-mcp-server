import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_merge_request_details
from gitlab_mr_mcp.gitlab_api import merge_merge_request as api_merge_merge_request


async def merge_merge_request(gitlab_url, project_id, access_token, args):
    """Merge a merge request"""
    logging.info(f"merge_merge_request called with args: {args}")

    mr_iid = args.get("merge_request_iid")
    if not mr_iid:
        raise ValueError("merge_request_iid is required")

    # Build merge options
    merge_data = {}

    if args.get("squash") is not None:
        merge_data["squash"] = args["squash"]

    if args.get("should_remove_source_branch") is not None:
        merge_data["should_remove_source_branch"] = args["should_remove_source_branch"]

    if args.get("merge_when_pipeline_succeeds") is not None:
        merge_data["merge_when_pipeline_succeeds"] = args["merge_when_pipeline_succeeds"]

    if args.get("sha"):
        merge_data["sha"] = args["sha"]

    if args.get("merge_commit_message"):
        merge_data["merge_commit_message"] = args["merge_commit_message"]

    if args.get("squash_commit_message"):
        merge_data["squash_commit_message"] = args["squash_commit_message"]

    status, data, error = await api_merge_merge_request(gitlab_url, project_id, access_token, mr_iid, merge_data)

    if status == 200:
        mr_title = data.get("title", "Unknown")
        mr_state = data.get("state", "unknown")
        mr_url = data.get("web_url", "")
        source_branch = data.get("source_branch", "")
        target_branch = data.get("target_branch", "")

        result = "# Merge Request Merged\n\n"
        result += f"**!{mr_iid}**: {mr_title}\n\n"
        result += f"**State**: {mr_state}\n"
        result += f"**Merged**: `{source_branch}` -> `{target_branch}`\n"

        if data.get("merge_commit_sha"):
            result += f"**Merge Commit**: `{data['merge_commit_sha'][:8]}`\n"

        if data.get("squash_commit_sha"):
            result += f"**Squash Commit**: `{data['squash_commit_sha'][:8]}`\n"

        merged_by = data.get("merged_by") or data.get("merge_user")
        if merged_by:
            result += f"**Merged By**: @{merged_by.get('username', 'unknown')}\n"

        result += f"\n**URL**: {mr_url}\n"

        return [TextContent(type="text", text=result)]

    elif status == 401:
        result = "# Merge Failed: Unauthorized\n\n"
        result += "Your access token doesn't have permission to merge.\n"
        result += "Ensure your token has `api` scope (not just `read_api`).\n"
        return [TextContent(type="text", text=result)]

    elif status == 405:
        # Method not allowed - MR can't be merged
        error_msg = data.get("message", error) if isinstance(data, dict) else error

        result = "# Merge Failed: Not Allowed\n\n"
        result += f"**MR**: !{mr_iid}\n"
        result += f"**Error**: {error_msg}\n\n"

        # Get MR details to explain why (best effort, don't fail if this errors)
        try:
            details_status, mr_details, _ = await get_merge_request_details(
                gitlab_url, project_id, access_token, mr_iid
            )
            if details_status == 200:
                result += "**Possible reasons**:\n"
                if mr_details.get("has_conflicts"):
                    result += "- Merge conflicts exist\n"
                if mr_details.get("draft") or mr_details.get("work_in_progress"):
                    result += "- MR is in draft/WIP status\n"
                if mr_details.get("merge_status") == "cannot_be_merged":
                    result += "- MR cannot be merged (check pipeline/approvals)\n"
                if mr_details.get("state") != "opened":
                    result += f"- MR is not open (state: {mr_details.get('state')})\n"
        except Exception:
            pass  # nosec B110 - intentional: supplementary info, failure is acceptable

        return [TextContent(type="text", text=result)]

    elif status == 406:
        # SHA mismatch
        result = "# Merge Failed: SHA Mismatch\n\n"
        result += f"**MR**: !{mr_iid}\n"
        result += "The SHA provided doesn't match the current HEAD.\n"
        result += "New commits may have been pushed since you last checked.\n"
        return [TextContent(type="text", text=result)]

    elif status == 409:
        # Conflict
        result = "# Merge Failed: Conflict\n\n"
        result += f"**MR**: !{mr_iid}\n"
        result += "SHA doesn't match or merge request is in an unmergeable state.\n"
        return [TextContent(type="text", text=result)]

    else:
        error_msg = data.get("message", error) if isinstance(data, dict) else error
        logging.error(f"Error merging MR: {status} - {error_msg}")
        raise Exception(f"Error merging merge request: {status} - {error_msg}")
