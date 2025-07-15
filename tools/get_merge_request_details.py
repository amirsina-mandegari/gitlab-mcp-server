from mcp.types import TextContent
from gitlab_api import (
    get_merge_request_details as api_get_merge_request_details,
    get_merge_request_pipeline,
    get_merge_request_changes
)
from utils import (
    format_date,
    get_state_explanation,
    get_pipeline_status_icon,
    calculate_change_stats,
    analyze_mr_readiness,
    get_mr_priority
)
import logging


async def get_merge_request_details(
    gitlab_url, project_id, access_token, args
):
    logging.info(f"get_merge_request_details called with args: {args}")
    mr_iid = args["merge_request_iid"]
    
    # API calls - run in parallel for better performance
    mr_status, mr_data, mr_error = await api_get_merge_request_details(
        gitlab_url, project_id, access_token, mr_iid
    )
    
    if mr_status != 200:
        logging.error(
            f"Error fetching merge request details: {mr_status} - {mr_error}"
        )
        raise Exception(
            f"Error fetching merge request details: {mr_status} - {mr_error}"
        )
    
    # Get additional data
    pipeline_status, pipeline_data, _ = await get_merge_request_pipeline(
        gitlab_url, project_id, access_token, mr_iid
    )
    
    changes_status, changes_data, _ = await get_merge_request_changes(
        gitlab_url, project_id, access_token, mr_iid
    )
    
    # Format the enhanced response
    result = f"# Merge Request !{mr_data['iid']}: {mr_data['title']}\n\n"
    
    # Basic info with enhanced formatting
    result += f"**Author**: {mr_data['author']['name']} "
    result += f"(@{mr_data['author']['username']})\n"
    result += f"**Status**: {mr_data['state']} "
    result += f"({get_state_explanation(mr_data['state'])})\n"
    result += f"**Priority**: {get_mr_priority(mr_data)}\n"
    result += f"**Created**: {format_date(mr_data['created_at'])}\n"
    result += f"**Updated**: {format_date(mr_data['updated_at'])}\n"
    result += f"**Source**: {mr_data['source_branch']} → "
    result += f"{mr_data['target_branch']}\n"
    
    # Pipeline status
    if pipeline_data:
        pipeline_icon = get_pipeline_status_icon(pipeline_data.get('status'))
        result += f"**Pipeline**: {pipeline_icon} "
        result += f"{pipeline_data.get('status', 'unknown')}\n"
        if pipeline_data.get('web_url'):
            result += f"**Pipeline URL**: {pipeline_data['web_url']}\n"
    
    # Change statistics
    if changes_status == 200:
        change_stats = calculate_change_stats(changes_data)
        result += f"**Changes**: {change_stats}\n"
    
    # Readiness analysis
    readiness = analyze_mr_readiness(mr_data, pipeline_data)
    result += f"**Merge Status**: {readiness}\n"
    
    result += f"**URL**: {mr_data['web_url']}\n\n"
    
    # Labels if present
    if mr_data.get('labels'):
        result += f"**Labels**: {', '.join(mr_data['labels'])}\n\n"
    
    # Description
    if mr_data.get('description'):
        result += f"## Description\n{mr_data['description']}\n\n"
    
    # Additional merge request info
    if mr_data.get('merge_commit_sha'):
        result += f"**Merge Commit**: `{mr_data['merge_commit_sha'][:8]}`\n"
    
    if mr_data.get('squash_commit_sha'):
        result += f"**Squash Commit**: `{mr_data['squash_commit_sha'][:8]}`\n"
    
    return [TextContent(type="text", text=result)] 