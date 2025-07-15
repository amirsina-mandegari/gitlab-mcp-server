from mcp.types import TextContent
from gitlab_api import (
    get_branch_merge_requests as api_get_branch_merge_requests
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
    
    # Format the response
    result = f"# Merge Requests for branch: {branch_name}\n\n"
    
    if not data:
        result += "No merge requests found for this branch.\n"
    else:
        for mr in data:
            result += f"## !{mr['iid']}: {mr['title']}\n"
            author_name = mr['author']['name']
            author_username = mr['author']['username']
            result += f"**Author**: {author_name} (@{author_username})\n"
            result += f"**Status**: {mr['state']}\n"
            result += f"**Created**: {mr['created_at']}\n"
            result += f"**Updated**: {mr['updated_at']}\n"
            source_branch = mr['source_branch']
            target_branch = mr['target_branch']
            result += f"**Source**: {source_branch} → {target_branch}\n"
            result += f"**URL**: {mr['web_url']}\n\n"
    
    return [TextContent(type="text", text=result)] 