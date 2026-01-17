import asyncio
import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_branch_merge_requests as api_get_branch_merge_requests
from gitlab_mr_mcp.gitlab_api import get_merge_request_changes, get_merge_request_pipeline
from gitlab_mr_mcp.utils import (
    analyze_mr_readiness,
    calculate_change_stats,
    format_date,
    format_labels,
    get_pipeline_status_icon,
    get_state_icon,
)


async def get_enhanced_mr_data(gitlab_url, project_id, access_token, mr_iid):
    """Get enhanced data for a single MR using parallel API calls"""
    try:
        pipeline_task = get_merge_request_pipeline(gitlab_url, project_id, access_token, mr_iid)
        changes_task = get_merge_request_changes(gitlab_url, project_id, access_token, mr_iid)

        pipeline_result, changes_result = await asyncio.gather(pipeline_task, changes_task, return_exceptions=True)

        if isinstance(pipeline_result, Exception):
            pipeline_data = None
        else:
            pipeline_status, pipeline_data, _ = pipeline_result
            if pipeline_status != 200:
                pipeline_data = None

        if isinstance(changes_result, Exception):
            changes_data = None
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

    result = f"# Merge Requests for branch: `{branch_name}`\n\n"
    result += f"Found {len(data)} merge request(s)\n\n"

    if not data:
        result += "No merge requests found for this branch.\n"
        return [TextContent(type="text", text=result)]

    # Fetch enhanced data
    enhanced_data_tasks = [get_enhanced_mr_data(gitlab_url, project_id, access_token, mr["iid"]) for mr in data]

    try:
        enhanced_results = await asyncio.gather(*enhanced_data_tasks)
    except Exception as e:
        logging.warning(f"Error in parallel enhanced data fetch: {e}")
        enhanced_results = [(None, None)] * len(data)

    for i, mr in enumerate(data):
        pipeline_data, changes_data = enhanced_results[i]

        state_icon = get_state_icon(mr["state"])
        result += f"## {state_icon} !{mr['iid']}: {mr['title']}\n\n"

        result += f"**Author**: {mr['author']['name']} (@{mr['author']['username']})\n"
        result += f"**State**: {mr['state']}\n"
        result += f"**Branches**: `{mr['source_branch']}` -> `{mr['target_branch']}`\n"
        result += f"**Updated**: {format_date(mr['updated_at'])}\n"

        # Pipeline
        if pipeline_data:
            pipeline_stat = pipeline_data.get("status")
            pipeline_icon = get_pipeline_status_icon(pipeline_stat)
            result += f"**Pipeline**: {pipeline_icon} {pipeline_stat}\n"
        elif mr.get("pipeline"):
            pipeline_stat = mr["pipeline"].get("status")
            pipeline_icon = get_pipeline_status_icon(pipeline_stat)
            result += f"**Pipeline**: {pipeline_icon} {pipeline_stat or 'unknown'}\n"

        # Changes
        if changes_data:
            change_stats = calculate_change_stats(changes_data)
            result += f"**Changes**: {change_stats}\n"

        # Readiness
        readiness = analyze_mr_readiness(mr, pipeline_data)
        result += f"**Status**: {readiness}\n"

        # Labels
        labels_str = format_labels(mr.get("labels"))
        if labels_str:
            result += f"**Labels**: {labels_str}\n"

        # Flags
        flags = []
        if mr.get("draft") or mr.get("work_in_progress"):
            flags.append("Draft")
        if mr.get("has_conflicts"):
            flags.append("Conflicts")
        if flags:
            result += f"**Flags**: {', '.join(flags)}\n"

        result += f"**URL**: {mr['web_url']}\n\n"

    # Summary
    result += "---\n\n## Summary\n\n"

    state_counts = {}
    for mr in data:
        s = mr["state"]
        state_counts[s] = state_counts.get(s, 0) + 1

    for s, count in state_counts.items():
        result += f"- {s.title()}: {count}\n"

    return [TextContent(type="text", text=result)]
