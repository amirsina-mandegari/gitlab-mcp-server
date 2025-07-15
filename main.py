#!/usr/bin/env python3
import asyncio
from decouple import config
import logging
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult
from logging_config import configure_logging
from tools.list_merge_requests import list_merge_requests
from tools.get_merge_request_reviews import get_merge_request_reviews
from tools.get_merge_request_details import get_merge_request_details
from tools.get_branch_merge_requests import get_branch_merge_requests


class GitLabMCPServer:
    def __init__(self):
        configure_logging()
        logging.info("Initializing GitLabMCPServer")
        self.server = Server("gitlab-mcp-server")
        # Get environment variables
        self.gitlab_url = config("GITLAB_URL", default="https://gitlab.com")
        self.project_id = config("GITLAB_PROJECT_ID", default=None)
        self.access_token = config("GITLAB_ACCESS_TOKEN", default=None)
        if not self.project_id or not self.access_token:
            logging.error(
                "Missing required environment variables: "
                "GITLAB_PROJECT_ID or GITLAB_ACCESS_TOKEN"
            )
            raise ValueError(
                "GITLAB_PROJECT_ID and GITLAB_ACCESS_TOKEN environment variables are required"
            )
        self.headers = {
            "Private-Token": self.access_token,
            "Content-Type": "application/json"
        }
        self.setup_handlers()

    def setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            logging.info("list_tools called")
            return [
                Tool(
                    name="list_merge_requests",
                    description="List merge requests for the GitLab project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string",
                                "enum": ["opened", "closed", "merged", "all"],
                                "default": "opened",
                                "description": "Filter by merge request state"
                            },
                            "target_branch": {
                                "type": "string",
                                "description": (
                                    "Filter by target branch (optional)"
                                )
                            },
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "description": "Maximum number of results"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_merge_request_reviews",
                    description=(
                        "Get reviews and discussions for a specific merge request"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "description": (
                                    "Internal ID of the merge request"
                                )
                            }
                        },
                        "required": ["merge_request_iid"]
                    }
                ),
                Tool(
                    name="get_merge_request_details",
                    description=(
                        "Get detailed information about a specific merge request"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "description": (
                                    "Internal ID of the merge request"
                                )
                            }
                        },
                        "required": ["merge_request_iid"]
                    }
                ),
                Tool(
                    name="get_branch_merge_requests",
                    description="Find merge requests for a specific branch",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "branch_name": {
                                "type": "string",
                                "description": "Name of the branch"
                            }
                        },
                        "required": ["branch_name"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> CallToolResult:
            logging.info(
                f"call_tool called: {name} with arguments: {arguments}"
            )
            try:
                if name == "list_merge_requests":
                    return await list_merge_requests(
                        self.gitlab_url, self.project_id, self.access_token, arguments
                    )
                elif name == "get_merge_request_reviews":
                    return await get_merge_request_reviews(
                        self.gitlab_url, self.project_id, self.access_token, arguments
                    )
                elif name == "get_merge_request_details":
                    return await get_merge_request_details(
                        self.gitlab_url, self.project_id, self.access_token, arguments
                    )
                elif name == "get_branch_merge_requests":
                    return await get_branch_merge_requests(
                        self.gitlab_url, self.project_id, self.access_token, arguments
                    )
                else:
                    logging.warning(f"Unknown tool called: {name}")
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Unknown tool: {name}"
                            )
                        ],
                        isError=True
                    )
            except Exception as e:
                logging.error(
                    f"Exception in call_tool for {name}: {e}", exc_info=True
                )
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: {str(e)}"
                        )
                    ],
                    isError=True
                )

    async def run(self):
        logging.info("Starting MCP stdio server")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="gitlab-mcp-server",
                    server_version="1.0.0",
                    capabilities={}
                )
            )


async def main():
    try:
        server = GitLabMCPServer()
        await server.run()
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1


if __name__ == "__main__":
    asyncio.run(main())