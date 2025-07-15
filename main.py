#!/usr/bin/env python3
import asyncio
import logging
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, 
    TextContent,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    JSONRPCError
)
from logging_config import configure_logging
from config import get_gitlab_config
from tools.list_merge_requests import list_merge_requests
from tools.get_merge_request_reviews import get_merge_request_reviews
from tools.get_merge_request_details import get_merge_request_details
from tools.get_branch_merge_requests import get_branch_merge_requests


class GitLabMCPServer:
    def __init__(self):
        configure_logging()
        logging.info("Initializing GitLabMCPServer")
        
        # Load and validate configuration
        self.config = get_gitlab_config()
        
        self.server = Server(self.config['server_name'])
        self.setup_handlers()

    def setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            logging.info("list_tools called")
            tools = [
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
                                "minimum": 1,
                                "maximum": 100,
                                "description": "Maximum number of results"
                            }
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_merge_request_reviews",
                    description=(
                        "Get reviews and discussions for a specific "
                        "merge request"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": (
                                    "Internal ID of the merge request"
                                )
                            }
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_merge_request_details",
                    description=(
                        "Get detailed information about a specific "
                        "merge request"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": (
                                    "Internal ID of the merge request"
                                )
                            }
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False
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
                                "minLength": 1,
                                "description": "Name of the branch"
                            }
                        },
                        "required": ["branch_name"],
                        "additionalProperties": False
                    }
                )
            ]
            tool_names = [t.name for t in tools]
            logging.info(f"Returning {len(tools)} tools: {tool_names}")
            return tools

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[TextContent]:
            logging.info(
                f"call_tool called: {name} with arguments: {arguments}"
            )
            
            try:
                # Validate tool name
                if name not in [
                    "list_merge_requests", 
                    "get_merge_request_reviews",
                    "get_merge_request_details", 
                    "get_branch_merge_requests"
                ]:
                    logging.warning(f"Unknown tool called: {name}")
                    raise JSONRPCError(
                        METHOD_NOT_FOUND,
                        f"Unknown tool: {name}"
                    )
                
                # Route to appropriate tool handler
                if name == "list_merge_requests":
                    return await list_merge_requests(
                        self.config['gitlab_url'], 
                        self.config['project_id'], 
                        self.config['access_token'], 
                        arguments
                    )
                elif name == "get_merge_request_reviews":
                    return await get_merge_request_reviews(
                        self.config['gitlab_url'], 
                        self.config['project_id'], 
                        self.config['access_token'], 
                        arguments
                    )
                elif name == "get_merge_request_details":
                    return await get_merge_request_details(
                        self.config['gitlab_url'], 
                        self.config['project_id'], 
                        self.config['access_token'], 
                        arguments
                    )
                elif name == "get_branch_merge_requests":
                    return await get_branch_merge_requests(
                        self.config['gitlab_url'], 
                        self.config['project_id'], 
                        self.config['access_token'], 
                        arguments
                    )
                    
            except JSONRPCError:
                # Re-raise JSONRPC errors as-is
                raise
            except ValueError as e:
                logging.error(f"Validation error in {name}: {e}")
                raise JSONRPCError(
                    INVALID_PARAMS,
                    f"Invalid parameters: {str(e)}"
                )
            except Exception as e:
                logging.error(
                    f"Unexpected error in call_tool for {name}: {e}", 
                    exc_info=True
                )
                raise JSONRPCError(
                    INTERNAL_ERROR,
                    f"Internal server error: {str(e)}"
                )

    async def run(self):
        logging.info("Starting MCP stdio server")
        try:
            async with stdio_server() as (read_stream, write_stream):
                logging.info("stdio_server context entered successfully")
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=self.config['server_name'],
                        server_version=self.config['server_version'],
                        capabilities={
                            "tools": {},
                            "logging": {}
                        }
                    )
                )
        except Exception as e:
            logging.error(f"Error in stdio_server: {e}", exc_info=True)
            raise


async def main():
    try:
        logging.info("Starting main function")
        server = GitLabMCPServer()
        logging.info("GitLabMCPServer created successfully")
        await server.run()
    except Exception as e:
        logging.error(f"Error starting server: {e}", exc_info=True)
        print(f"Error starting server: {e}")
        return 1


if __name__ == "__main__":
    asyncio.run(main())