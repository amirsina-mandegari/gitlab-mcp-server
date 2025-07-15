from mcp.types import TextContent
from gitlab_api import (
    get_merge_request_details as api_get_merge_request_details
)
import logging


async def get_merge_request_details(
    gitlab_url, project_id, access_token, args
):
    logging.info(f"get_merge_request_details called with args: {args}")
    mr_iid = args["merge_request_iid"]
    
    # API call
    status, data, error = await api_get_merge_request_details(
        gitlab_url, project_id, access_token, mr_iid
    )
    
    if status != 200:
        logging.error(
            f"Error fetching merge request details: {status} - {error}"
        )
        raise Exception(
            f"Error fetching merge request details: {status} - {error}"
        )
    
    # Format the response
    result = f"# Merge Request !{data['iid']}: {data['title']}\n\n"
    result += f"**Author**: {data['author']['name']} "
    result += f"(@{data['author']['username']})\n"
    result += f"**Status**: {data['state']}\n"
    result += f"**Created**: {data['created_at']}\n"
    result += f"**Updated**: {data['updated_at']}\n"
    result += f"**Source**: {data['source_branch']} → "
    result += f"{data['target_branch']}\n"
    result += f"**URL**: {data['web_url']}\n\n"
    
    if data.get('description'):
        result += f"## Description\n{data['description']}\n\n"
    
    return [TextContent(type="text", text=result)] 