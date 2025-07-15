from mcp.types import TextContent
from gitlab_api import get_merge_requests
import logging


async def list_merge_requests(gitlab_url, project_id, access_token, args):
    logging.info(f"list_merge_requests called with args: {args}")
    
    # Prepare parameters for API call
    state = args.get("state", "opened")
    target_branch = args.get("target_branch")
    limit = args.get("limit", 10)
    
    params = {
        "state": state,
        "per_page": limit,
        "order_by": "updated_at",
        "sort": "desc"
    }
    
    if target_branch:
        params["target_branch"] = target_branch
    
    # API call
    status, data, error = await get_merge_requests(
        gitlab_url, project_id, access_token, params
    )
    
    if status != 200:
        logging.error(f"Error listing merge requests: {status} - {error}")
        raise Exception(f"Error listing merge requests: {status} - {error}")
    
    # Format the response
    result = "# Merge Requests\n\n"
    
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