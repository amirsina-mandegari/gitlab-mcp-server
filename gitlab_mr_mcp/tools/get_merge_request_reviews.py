import asyncio
import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_merge_request_changes, get_merge_request_details, get_merge_request_pipeline
from gitlab_mr_mcp.gitlab_api import get_merge_request_reviews as api_get_merge_request_reviews
from gitlab_mr_mcp.utils import (
    analyze_mr_readiness,
    calculate_change_stats,
    format_date,
    format_user,
    get_pipeline_status_icon,
)


def format_approval_summary(approvals):
    """Generate approval summary"""
    if not approvals:
        return "No approval information available\n"

    result = ""
    approved_by = approvals.get("approved_by", [])
    approvals_required = approvals.get("approvals_required", 0)
    approvals_left = approvals.get("approvals_left", 0)

    if approved_by:
        approvers = ", ".join(f"@{a['user']['username']}" for a in approved_by)
        result += f"**Approved by**: {approvers}\n"

    if approvals_required > 0:
        if approvals_left == 0:
            result += "**Status**: All required approvals received\n"
        else:
            result += f"**Status**: {approvals_left} more approval(s) needed\n"
        result += f"**Required**: {approvals_required} | **Received**: {len(approved_by)}\n"
    elif not approved_by:
        result += "No approvals yet\n"

    return result


def format_discussion_summary(discussions):
    """Generate discussion summary"""
    if not discussions:
        return "No discussions found\n"

    total = len(discussions)
    resolved = sum(1 for d in discussions if d.get("resolved"))
    unresolved = total - resolved

    result = f"**Total**: {total} | **Resolved**: {resolved} | **Unresolved**: {unresolved}\n"

    if unresolved > 0:
        result += f"\n**{unresolved} unresolved discussion(s)** require attention\n"

    return result


def format_discussion_thread(discussion):
    """Format a single discussion thread"""
    if not discussion.get("notes"):
        return ""

    result = ""
    is_resolved = discussion.get("resolved", False)
    discussion_id = discussion.get("id", "unknown")
    status = "Resolved" if is_resolved else "Unresolved"

    result += f"### Discussion `{discussion_id}` [{status}]\n\n"

    for note in discussion["notes"]:
        if note.get("system"):
            continue

        author = format_user(note.get("author"))
        note_id = note.get("id", "unknown")
        timestamp = format_date(note.get("created_at"))

        result += f"**{author}** ({timestamp}) [note: `{note_id}`]\n"

        # Position info for inline comments
        if note.get("position"):
            pos = note["position"]
            if pos.get("new_path"):
                result += f"File: `{pos['new_path']}`"
                if pos.get("new_line"):
                    result += f" line {pos['new_line']}"
                result += "\n"

        body = note.get("body", "").strip()
        if body:
            result += f"\n{body}\n"

        result += "\n"

    return result


async def get_merge_request_reviews(gitlab_url, project_id, access_token, args):
    logging.info(f"get_merge_request_reviews called with args: {args}")
    mr_iid = args["merge_request_iid"]

    tasks = [
        api_get_merge_request_reviews(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_details(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_pipeline(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_changes(gitlab_url, project_id, access_token, mr_iid),
    ]

    try:
        reviews_result, details_result, pipeline_result, changes_result = await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"Error in parallel API calls: {e}")
        raise Exception(f"Error fetching merge request data: {e}")

    discussions_status, discussions, discussions_text = reviews_result["discussions"]
    approvals_status, approvals, _approvals_text = reviews_result["approvals"]

    details_status, mr_details, _details_text = details_result
    pipeline_status, pipeline_data, _pipeline_text = pipeline_result
    changes_status, changes_data, _changes_text = changes_result

    if discussions_status != 200:
        logging.error(f"Error fetching discussions {discussions_status}: {discussions_text}")
        raise Exception(f"Error fetching discussions: {discussions_status} - {discussions_text}")

    result = f"# Reviews for MR !{mr_iid}\n\n"

    # MR Overview
    if details_status == 200:
        result += "## Overview\n\n"
        result += f"**Title**: {mr_details.get('title', 'N/A')}\n"
        result += f"**Author**: {format_user(mr_details.get('author'))}\n"
        result += f"**State**: {mr_details.get('state', 'N/A')}\n"

        if pipeline_status == 200 and pipeline_data:
            pipeline_icon = get_pipeline_status_icon(pipeline_data.get("status"))
            result += f"**Pipeline**: {pipeline_icon} {pipeline_data.get('status', 'unknown')}\n"

        if changes_status == 200:
            change_stats = calculate_change_stats(changes_data)
            result += f"**Changes**: {change_stats}\n"

        readiness = analyze_mr_readiness(mr_details, pipeline_data, approvals)
        result += f"**Merge Status**: {readiness}\n"
        result += "\n"

    # Approvals
    result += "## Approvals\n\n"
    result += format_approval_summary(approvals)
    result += "\n"

    # Discussions summary
    result += "## Discussions\n\n"
    result += format_discussion_summary(discussions)
    result += "\n"

    # Detailed discussions
    if discussions:
        result += "## Discussion Details\n\n"
        for discussion in discussions:
            thread_content = format_discussion_thread(discussion)
            if thread_content:
                result += thread_content
                result += "---\n\n"

    # Action items
    result += "## Action Items\n\n"
    action_items = []

    if discussions:
        unresolved = sum(1 for d in discussions if not d.get("resolved"))
        if unresolved > 0:
            action_items.append(f"- Resolve {unresolved} pending discussion(s)")

    if approvals and approvals.get("approvals_left", 0) > 0:
        action_items.append(f"- Get {approvals['approvals_left']} more approval(s)")

    if pipeline_status == 200 and pipeline_data and pipeline_data.get("status") == "failed":
        action_items.append("- Fix failing pipeline")

    if details_status == 200 and mr_details.get("has_conflicts"):
        action_items.append("- Resolve merge conflicts")

    if action_items:
        result += "\n".join(action_items) + "\n"
    else:
        result += "No action items - ready for next steps\n"

    return [TextContent(type="text", text=result)]
