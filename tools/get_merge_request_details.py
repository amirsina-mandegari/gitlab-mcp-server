from gitlab_api import get_merge_request_details as api_get_merge_request_details
from mcp.types import CallToolResult, TextContent
import logging


async def get_merge_request_details(
    gitlab_url, project_id, access_token, args
):
    logging.info(f"get_merge_request_details called with args: {args}")
    mr_iid = args["merge_request_iid"]
    status, mr, error_text = await api_get_merge_request_details(
        gitlab_url, project_id, access_token, mr_iid
    )
    if status == 200:
        result = f"# MR !{mr['iid']}: {mr['title']}\n\n"
        result += (
            f"**Author**: {mr['author']['name']} (@{mr['author']['username']})\n"
        )
        result += (
            f"**Source**: `{mr['source_branch']}` "
            f"→ `{mr['target_branch']}`\n"
        )
        result += f"**State**: {mr['state']}\n"
        result += f"**Created**: {mr['created_at']}\n"
        result += f"**Updated**: {mr['updated_at']}\n"
        result += f"**URL**: {mr['web_url']}\n\n"
        if mr.get('description'):
            result += f"## Description\n{mr['description']}\n\n"
        if mr.get('pipeline'):
            pipeline = mr['pipeline']
            result += (
                f"**Pipeline**: {pipeline['status']} "
                f"({pipeline['web_url']})\n"
            )
        result += f"**Changes**: +{mr['changes_count']} files\n"
        return CallToolResult(
            content=[TextContent(type="text", text=result)],
            isError=False
        )
    else:
        logging.error(f"GitLab API error {status}: {error_text}")
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"GitLab API error: {status} - {error_text}"
            )],
            isError=True
        ) 