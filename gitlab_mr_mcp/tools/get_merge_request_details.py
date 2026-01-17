import asyncio
import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_merge_request_changes
from gitlab_mr_mcp.gitlab_api import get_merge_request_details as api_get_merge_request_details
from gitlab_mr_mcp.gitlab_api import get_merge_request_pipeline, get_merge_request_reviews
from gitlab_mr_mcp.utils import (
    analyze_mr_readiness,
    calculate_change_stats,
    format_date,
    format_labels,
    format_user,
    get_pipeline_status_icon,
    get_state_icon,
)


async def get_merge_request_details(gitlab_url, project_id, access_token, args):
    logging.info(f"get_merge_request_details called with args: {args}")
    mr_iid = args["merge_request_iid"]

    tasks = [
        api_get_merge_request_details(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_pipeline(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_changes(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_reviews(gitlab_url, project_id, access_token, mr_iid),
    ]

    try:
        details_result, pipeline_result, changes_result, reviews_result = await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"Error in parallel API calls: {e}")
        raise Exception(f"Error fetching merge request data: {e}")

    mr_status, mr_data, mr_error = details_result
    pipeline_status, pipeline_data, _pipeline_error = pipeline_result
    changes_status, changes_data, _changes_error = changes_result

    if mr_status != 200:
        logging.error(f"Error fetching merge request details: {mr_status} - {mr_error}")
        raise Exception(f"Error fetching merge request details: {mr_status} - {mr_error}")

    # Header
    state_icon = get_state_icon(mr_data["state"])
    result = f"# {state_icon} MR !{mr_data['iid']}: {mr_data['title']}\n\n"

    # Core info
    result += f"**Author**: {format_user(mr_data.get('author'))}\n"
    result += f"**State**: {mr_data['state']}\n"
    result += f"**Branches**: `{mr_data['source_branch']}` -> `{mr_data['target_branch']}`\n"
    result += f"**Created**: {format_date(mr_data['created_at'])}\n"
    result += f"**Updated**: {format_date(mr_data['updated_at'])}\n"

    # Pipeline
    if pipeline_status == 200 and pipeline_data:
        pipeline_icon = get_pipeline_status_icon(pipeline_data.get("status"))
        result += f"**Pipeline**: {pipeline_icon} {pipeline_data.get('status', 'unknown')}\n"
    elif mr_data.get("pipeline"):
        pipeline_stat = mr_data["pipeline"].get("status")
        pipeline_icon = get_pipeline_status_icon(pipeline_stat)
        result += f"**Pipeline**: {pipeline_icon} {pipeline_stat or 'unknown'}\n"

    # Changes
    if changes_status == 200:
        change_stats = calculate_change_stats(changes_data)
        result += f"**Changes**: {change_stats}\n"

    # Readiness
    readiness = analyze_mr_readiness(mr_data, pipeline_data)
    result += f"**Merge Status**: {readiness}\n"

    # Labels
    labels_str = format_labels(mr_data.get("labels"))
    if labels_str:
        result += f"**Labels**: {labels_str}\n"

    # Flags
    if mr_data.get("draft") or mr_data.get("work_in_progress"):
        result += "**Draft**: Yes\n"

    if mr_data.get("has_conflicts"):
        result += "**Conflicts**: Yes - needs resolution\n"

    # Assignees/Reviewers
    if mr_data.get("assignees"):
        assignees = ", ".join(f"@{user['username']}" for user in mr_data["assignees"])
        result += f"**Assignees**: {assignees}\n"

    if mr_data.get("reviewers"):
        reviewers = ", ".join(f"@{user['username']}" for user in mr_data["reviewers"])
        result += f"**Reviewers**: {reviewers}\n"

    # URL
    result += f"**URL**: {mr_data['web_url']}\n"

    # Description
    if mr_data.get("description"):
        result += f"\n## Description\n\n{mr_data['description']}\n"

    # Reviews summary
    if reviews_result and "discussions" in reviews_result:
        discussions_status, discussions, _ = reviews_result["discussions"]
        approvals_status, approvals, _ = reviews_result["approvals"]

        result += "\n## Reviews\n\n"

        if approvals_status == 200 and approvals:
            approved_by = approvals.get("approved_by", [])
            approvals_left = approvals.get("approvals_left", 0)

            if approved_by:
                approvers = ", ".join(f"@{a['user']['username']}" for a in approved_by)
                result += f"**Approved by**: {approvers}\n"

            if approvals_left > 0:
                result += f"**Approvals needed**: {approvals_left}\n"

        if discussions_status == 200 and discussions:
            total = len(discussions)
            resolved = sum(1 for d in discussions if d.get("resolved"))
            unresolved = total - resolved

            result += f"**Discussions**: {total} total, {resolved} resolved"
            if unresolved > 0:
                result += f", {unresolved} unresolved"
            result += "\n"

    # Action items
    result += "\n## Action Items\n\n"
    action_items = []

    if mr_data.get("draft") or mr_data.get("work_in_progress"):
        action_items.append("- Remove draft status when ready")

    if mr_data.get("has_conflicts"):
        action_items.append("- Resolve merge conflicts")

    if pipeline_status == 200 and pipeline_data:
        if pipeline_data.get("status") == "failed":
            action_items.append("- Fix failing pipeline")
        elif pipeline_data.get("status") == "running":
            action_items.append("- Wait for pipeline to complete")

    if reviews_result and "discussions" in reviews_result:
        discussions_status, discussions, _ = reviews_result["discussions"]
        approvals_status, approvals, _ = reviews_result["approvals"]

        if discussions_status == 200 and discussions:
            unresolved = sum(1 for d in discussions if not d.get("resolved"))
            if unresolved > 0:
                action_items.append(f"- Resolve {unresolved} pending discussion(s)")

        if approvals_status == 200 and approvals and approvals.get("approvals_left", 0) > 0:
            action_items.append(f"- Get {approvals['approvals_left']} more approval(s)")

    if mr_data["state"] == "opened" and not action_items:
        action_items.append("- Ready to merge")

    if action_items:
        result += "\n".join(action_items) + "\n"
    else:
        result += "None identified\n"

    return [TextContent(type="text", text=result)]
