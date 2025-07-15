from gitlab_api import get_merge_requests
from mcp.types import CallToolResult, TextContent
import logging


async def list_merge_requests(gitlab_url, project_id, access_token, args):
    logging.info(f"list_merge_requests called with args: {args}")
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
    status, mrs, error_text = await get_merge_requests(
        gitlab_url, project_id, access_token, params
    )
    if status == 200:
        result = "# Merge Requests\n\n"
        for mr in mrs:
            result += f"**MR !{mr['iid']}**: {mr['title']}\n"
            result += f"- **Author**: {mr['author']['name']}\n"
            result += (
                f"- **Source**: {mr['source_branch']} "
                f"→ {mr['target_branch']}\n"
            )
            result += f"- **State**: {mr['state']}\n"
            result += f"- **Updated**: {mr['updated_at']}\n"
            result += f"- **URL**: {mr['web_url']}\n\n"
        return CallToolResult(content=[TextContent(type="text", text=result)])
    else:
        logging.error(f"GitLab API error {status}: {error_text}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"GitLab API error: {status} - {error_text}")],
            isError=True
        ) 