import asyncio
import logging

from mcp.types import TextContent

from gitlab_mcp_server.gitlab_api import get_branch_merge_requests as api_get_branch_merge_requests
from gitlab_mcp_server.gitlab_api import get_merge_request_changes, get_merge_request_pipeline
from gitlab_mcp_server.utils import (
    analyze_mr_readiness,
    calculate_change_stats,
    format_date,
    get_mr_priority,
    get_pipeline_status_icon,
    get_state_explanation,
)


async def get_enhanced_mr_data(gitlab_url, project_id, access_token, mr_iid):
    """Get enhanced data for a single MR using parallel API calls"""
    try:
        pipeline_task = get_merge_request_pipeline(gitlab_url, project_id, access_token, mr_iid)
        changes_task = get_merge_request_changes(gitlab_url, project_id, access_token, mr_iid)

        pipeline_result, changes_result = await asyncio.gather(pipeline_task, changes_task, return_exceptions=True)

        if isinstance(pipeline_result, Exception):
            pipeline_data = None
            logging.warning(f"Pipeline fetch failed for MR {mr_iid}: {pipeline_result}")
        else:
            pipeline_status, pipeline_data, _ = pipeline_result
            if pipeline_status != 200:
                pipeline_data = None

        if isinstance(changes_result, Exception):
            changes_data = None
            logging.warning(f"Changes fetch failed for MR {mr_iid}: {changes_result}")
        else:
            changes_status, changes_data, _ = changes_result
            if changes_status != 200:
                changes_data = None

        return pipeline_data, changes_data

    except Exception as e:
        logging.warning(f"Error fetching enhanced data for MR {mr_iid}: {e}")
        return None, None


async def get_branch_merge_requests(gitlab_url, project_id, access_token, args):
    logging.info(f"get_branch_merge_requests called with args: {args}")
    branch_name = args["branch_name"]

    status, data, error = await api_get_branch_merge_requests(gitlab_url, project_id, access_token, branch_name)

    if status != 200:
        logging.error(f"Error fetching branch merge requests: {status} - {error}")
        raise Exception(f"Error fetching branch merge requests: {status} - {error}")

    result = f"# 🌿 Merge Requests for branch: **{branch_name}**\n"
    result += f"*Found {len(data)} merge request" f"{'s' if len(data) != 1 else ''}*\n\n"

    if not data:
        result += "📭 No merge requests found for this branch.\n"
        result += "💡 **Tip**: Create a merge request to start the " "review process.\n"
        return [TextContent(type="text", text=result)]

    enhanced_data_tasks = []
    for mr in data:
        task = get_enhanced_mr_data(gitlab_url, project_id, access_token, mr["iid"])
        enhanced_data_tasks.append(task)

    try:
        enhanced_results = await asyncio.gather(*enhanced_data_tasks)
    except Exception as e:
        logging.warning(f"Error in parallel enhanced data fetch: {e}")
        enhanced_results = [(None, None)] * len(data)

    for i, mr in enumerate(data):
        pipeline_data, changes_data = enhanced_results[i]

        if mr["state"] == "merged":
            state_icon = "✅"
        elif mr["state"] == "opened":
            state_icon = "🔄"
        else:
            state_icon = "❌"
        result += f"## {state_icon} !{mr['iid']}: {mr['title']}\n"

        author_name = mr["author"]["name"]
        author_username = mr["author"]["username"]
        result += f"**👤 Author**: {author_name} (@{author_username})\n"

        result += f"**📊 Status**: {mr['state']} "
        result += f"({get_state_explanation(mr['state'])})\n"

        priority = get_mr_priority(mr)
        readiness = analyze_mr_readiness(mr, pipeline_data)
        result += f"**🏷️ Priority**: {priority}\n"
        result += f"**🚦 Merge Status**: {readiness}\n"

        result += f"**📅 Created**: {format_date(mr['created_at'])}\n"
        result += f"**🔄 Updated**: {format_date(mr['updated_at'])}\n"

        source_branch = mr["source_branch"]
        target_branch = mr["target_branch"]
        result += f"**🌿 Branches**: `{source_branch}` → `{target_branch}`\n"

        if pipeline_data:
            pipeline_status = pipeline_data.get("status")
            pipeline_icon = get_pipeline_status_icon(pipeline_status)
            result += f"**🔧 Pipeline**: {pipeline_icon} {pipeline_status}\n"

            if pipeline_data.get("web_url"):
                result += f"  *[View Pipeline]({pipeline_data['web_url']})*\n"
        elif mr.get("pipeline"):
            pipeline_status = mr["pipeline"].get("status")
            pipeline_icon = get_pipeline_status_icon(pipeline_status)
            result += f"**🔧 Pipeline**: {pipeline_icon} {pipeline_status or 'unknown'}\n"

        if changes_data:
            change_stats = calculate_change_stats(changes_data)
            result += f"**📈 Changes**: {change_stats}\n"

        if mr.get("labels"):
            labels_str = ", ".join(f"`{label}`" for label in mr["labels"])
            result += f"**🏷️ Labels**: {labels_str}\n"

        if mr.get("draft") or mr.get("work_in_progress"):
            result += "**⚠️ Status**: 🚧 Draft/Work in Progress\n"

        if mr.get("has_conflicts"):
            result += "**⚠️ Warning**: 🔥 Has merge conflicts\n"

        result += f"**🔗 Actions**: [View MR]({mr['web_url']})"
        if mr["state"] == "opened":
            result += f" | [Review & Approve]({mr['web_url']})"
        result += "\n"

        result += "\n---\n\n"

    result += "## 📊 Summary\n"

    state_counts = {}
    for mr in data:
        state = mr["state"]
        state_counts[state] = state_counts.get(state, 0) + 1

    result += "**State Breakdown**:\n"
    for state, count in state_counts.items():
        icon = "✅" if state == "merged" else "🔄" if state == "opened" else "❌"
        result += f"  • {icon} {state.title()}: {count}\n"

    result += "\n**🎯 Action Items**:\n"
    opened_mrs = [mr for mr in data if mr["state"] == "opened"]

    if opened_mrs:
        has_conflicts = sum(1 for mr in opened_mrs if mr.get("has_conflicts"))
        drafts = sum(1 for mr in opened_mrs if mr.get("draft") or mr.get("work_in_progress"))

        if has_conflicts:
            result += f"  • 🔥 {has_conflicts} MR{'s' if has_conflicts > 1 else ''} with merge conflicts\n"
        if drafts:
            result += f"  • 🚧 {drafts} draft MR{'s' if drafts > 1 else ''} in progress\n"

        ready_count = len(opened_mrs) - has_conflicts - drafts
        if ready_count > 0:
            result += f"  • ✅ {ready_count} MR{'s' if ready_count > 1 else ''} ready for review\n"
    else:
        result += "  • 🎉 No open merge requests - branch is clean!\n"

    return [TextContent(type="text", text=result)]
