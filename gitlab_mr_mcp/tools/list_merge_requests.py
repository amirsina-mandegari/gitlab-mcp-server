import asyncio
import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_merge_request_changes, get_merge_request_pipeline, get_merge_requests
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


async def list_merge_requests(gitlab_url, project_id, access_token, args):
    logging.info(f"list_merge_requests called with args: {args}")

    state = args.get("state", "opened")
    target_branch = args.get("target_branch")
    limit = args.get("limit", 10)

    params = {"state": state, "per_page": limit, "order_by": "updated_at", "sort": "desc"}

    if target_branch:
        params["target_branch"] = target_branch

    status, data, error = await get_merge_requests(gitlab_url, project_id, access_token, params)

    if status != 200:
        logging.error(f"Error listing merge requests: {status} - {error}")
        raise Exception(f"Error listing merge requests: {status} - {error}")

    state_filter = f" ({state})" if state != "all" else ""
    result = f"# Merge Requests{state_filter}\n\n"
    result += f"Found {len(data)} merge request(s)\n\n"

    if not data:
        result += "No merge requests found.\n"
        return [TextContent(type="text", text=result)]

    # Fetch enhanced data for first 5 MRs
    enhanced_data_tasks = []
    for mr in data[:5]:
        task = get_enhanced_mr_data(gitlab_url, project_id, access_token, mr["iid"])
        enhanced_data_tasks.append(task)

    try:
        enhanced_results = await asyncio.gather(*enhanced_data_tasks)
    except Exception as e:
        logging.warning(f"Error in parallel enhanced data fetch: {e}")
        enhanced_results = [(None, None)] * len(data[:5])

    for i, mr in enumerate(data):
        if i < len(enhanced_results):
            pipeline_data, changes_data = enhanced_results[i]
        else:
            pipeline_data, changes_data = None, None

        state_icon = get_state_icon(mr["state"])
        result += f"## {state_icon} !{mr['iid']}: {mr['title']}\n\n"

        result += f"**Author**: {mr['author']['name']} (@{mr['author']['username']})\n"
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

    # Action items for opened MRs
    opened_mrs = [mr for mr in data if mr["state"] == "opened"]
    if opened_mrs:
        has_conflicts = sum(1 for mr in opened_mrs if mr.get("has_conflicts"))
        drafts = sum(1 for mr in opened_mrs if mr.get("draft") or mr.get("work_in_progress"))

        if has_conflicts or drafts:
            result += "\n**Attention needed**:\n"
            if has_conflicts:
                result += f"- {has_conflicts} MR(s) with merge conflicts\n"
            if drafts:
                result += f"- {drafts} draft MR(s)\n"

    return [TextContent(type="text", text=result)]
