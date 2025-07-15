from gitlab_api import get_branch_merge_requests as api_get_branch_merge_requests
from mcp.types import CallToolResult, TextContent
import logging


async def get_branch_merge_requests(
    gitlab_url, project_id, access_token, args
):
    logging.info(f"get_branch_merge_requests called with args: {args}")
    branch_name = args["branch_name"]
    params = {
        "source_branch": branch_name,
        "state": "all",
        "per_page": 20,
    }
    status, mrs, error_text = await api_get_branch_merge_requests(
        gitlab_url, project_id, access_token, params
    )
    if status == 200:
        if not mrs:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=(
                            f"No merge requests found for branch "
                            f"'{branch_name}'"
                        ),
                    )
                ]
            )
        result = f"# Merge Requests for branch '{branch_name}'\n\n"
        for mr in mrs:
            result += f"**MR !{mr['iid']}**: {mr['title']}\n"
            result += f"- **State**: {mr['state']}\n"
            result += f"- **Target**: {mr['target_branch']}\n"
            result += f"- **Updated**: {mr['updated_at']}\n"
            result += f"- **URL**: {mr['web_url']}\n\n"
        return CallToolResult(content=[TextContent(type="text", text=result)])
    else:
        logging.error(f"GitLab API error {status}: {error_text}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"GitLab API error: {status} - {error_text}")],
            isError=True
        ) 