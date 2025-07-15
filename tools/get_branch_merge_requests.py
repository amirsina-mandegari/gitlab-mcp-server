from mcp.types import TextContent
from gitlab_api import (
    get_branch_merge_requests as api_get_branch_merge_requests
)
from utils import (
    format_date,
    get_state_explanation,
    get_pipeline_status_icon,
    analyze_mr_readiness,
    get_mr_priority
)
import logging


async def get_branch_merge_requests(
    gitlab_url, project_id, access_token, args
):
    logging.info(f"get_branch_merge_requests called with args: {args}")
    branch_name = args["branch_name"]
    
    # Prepare parameters for API call
    params = {
        "source_branch": branch_name,
        "state": "all",
        "per_page": 20,
        "order_by": "updated_at",
        "sort": "desc"
    }
    
    # API call
    status, data, error = await api_get_branch_merge_requests(
        gitlab_url, project_id, access_token, params
    )
    
    if status != 200:
        logging.error(
            f"Error fetching branch merge requests: {status} - {error}"
        )
        raise Exception(
            f"Error fetching branch merge requests: {status} - {error}"
        )
    
    # Format the enhanced response
    result = f"# Merge Requests for branch: {branch_name}\n"
    result += f"({len(data)} found)\n\n"
    
    if not data:
        result += "No merge requests found for this branch.\n"
    else:
        for mr in data:
            result += f"## !{mr['iid']}: {mr['title']}\n"
            
            # Enhanced formatting with all the improvements
            author_name = mr['author']['name']
            author_username = mr['author']['username']
            result += f"**Author**: {author_name} (@{author_username})\n"
            result += f"**Status**: {mr['state']} "
            result += f"({get_state_explanation(mr['state'])})\n"
            
            # Priority and readiness
            priority = get_mr_priority(mr)
            readiness = analyze_mr_readiness(mr)
            result += f"**Priority**: {priority}\n"
            result += f"**Merge Status**: {readiness}\n"
            
            # Better date formatting
            result += f"**Created**: {format_date(mr['created_at'])}\n"
            result += f"**Updated**: {format_date(mr['updated_at'])}\n"
            
            # Branch info
            source_branch = mr['source_branch']
            target_branch = mr['target_branch']
            result += f"**Source**: {source_branch} → {target_branch}\n"
            
            # Pipeline status if available
            if mr.get('pipeline'):
                pipeline_status = mr['pipeline'].get('status')
                pipeline_icon = get_pipeline_status_icon(pipeline_status)
                result += f"**Pipeline**: {pipeline_icon} "
                result += f"{pipeline_status or 'unknown'}\n"
            
            # Labels if present
            if mr.get('labels'):
                result += f"**Labels**: {', '.join(mr['labels'])}\n"
            
            # Draft/WIP indicator
            if mr.get('draft') or mr.get('work_in_progress'):
                result += "**Status**: 🚧 Draft/WIP\n"
            
            result += f"**URL**: {mr['web_url']}\n\n"
    
    return [TextContent(type="text", text=result)] 