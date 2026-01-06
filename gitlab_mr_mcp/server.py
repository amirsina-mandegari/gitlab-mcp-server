#!/usr/bin/env python3
import asyncio
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, METHOD_NOT_FOUND, ErrorData, TextContent, Tool

from gitlab_mr_mcp.config import get_gitlab_config
from gitlab_mr_mcp.logging_config import configure_logging
from gitlab_mr_mcp.tools import (
    create_merge_request,
    create_review_comment,
    get_branch_merge_requests,
    get_commit_discussions,
    get_job_log,
    get_merge_request_details,
    get_merge_request_pipeline,
    get_merge_request_reviews,
    get_merge_request_test_report,
    get_pipeline_test_summary,
    list_merge_requests,
    list_project_labels,
    list_project_members,
    reply_to_review_comment,
    resolve_review_discussion,
    update_merge_request,
)


class GitLabMCPServer:
    def __init__(self):
        configure_logging()
        logging.info("Initializing GitLabMCPServer")

        self.config = get_gitlab_config()

        self.server = Server(self.config["server_name"])
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
                                "description": "Filter by merge request state",
                            },
                            "target_branch": {"type": "string", "description": ("Filter by target branch (optional)")},
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100,
                                "description": "Maximum number of results",
                            },
                        },
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_merge_request_reviews",
                    description=("Get reviews and discussions for a specific " "merge request"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": ("Internal ID of the merge request"),
                            }
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_merge_request_details",
                    description=("Get detailed information about a specific " "merge request"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": ("Internal ID of the merge request"),
                            }
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_merge_request_pipeline",
                    description=(
                        "Get the last pipeline data for a specific merge "
                        "request, including all jobs and their statuses. "
                        "Returns job IDs that can be used with get_job_log "
                        "to fetch detailed output."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": ("Internal ID of the merge request"),
                            }
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_merge_request_test_report",
                    description=(
                        "Get structured test report for a merge request "
                        "with specific test failures, error messages, and "
                        "stack traces. Shows the same test data visible on "
                        "the GitLab MR page. Best for debugging test failures."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": ("Internal ID of the merge request"),
                            }
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_pipeline_test_summary",
                    description=(
                        "Get test summary for a merge request - a "
                        "lightweight overview showing pass/fail counts "
                        "per test suite. Faster than full test report. "
                        "Great for quick status checks."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": ("Internal ID of the merge request"),
                            }
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_job_log",
                    description=(
                        "Get the trace/log output for a specific pipeline "
                        "job. Perfect for debugging failed tests and "
                        "understanding CI/CD failures."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {
                                "type": "integer",
                                "minimum": 1,
                                "description": ("ID of the pipeline job (obtained from " "get_merge_request_pipeline)"),
                            }
                        },
                        "required": ["job_id"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_branch_merge_requests",
                    description=("Get all merge requests for a specific branch"),
                    inputSchema={
                        "type": "object",
                        "properties": {"branch_name": {"type": "string", "description": "Name of the branch"}},
                        "required": ["branch_name"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="reply_to_review_comment",
                    description=("Reply to a specific discussion thread in a " "merge request review"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": ("Internal ID of the merge request"),
                            },
                            "discussion_id": {
                                "type": "string",
                                "description": ("ID of the discussion thread to reply to"),
                            },
                            "body": {"type": "string", "description": "Content of the reply comment"},
                        },
                        "required": ["merge_request_iid", "discussion_id", "body"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="create_review_comment",
                    description=("Create a new discussion thread in a " "merge request review"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": ("Internal ID of the merge request"),
                            },
                            "body": {"type": "string", "description": ("Content of the new discussion comment")},
                        },
                        "required": ["merge_request_iid", "body"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="resolve_review_discussion",
                    description=("Resolve or unresolve a discussion thread in a " "merge request review"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": ("Internal ID of the merge request"),
                            },
                            "discussion_id": {
                                "type": "string",
                                "description": ("ID of the discussion thread to " "resolve/unresolve"),
                            },
                            "resolved": {
                                "type": "boolean",
                                "default": True,
                                "description": ("Whether to resolve (true) or unresolve " "(false) the discussion"),
                            },
                        },
                        "required": ["merge_request_iid", "discussion_id"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_commit_discussions",
                    description=("Get discussions and comments on commits within a " "specific merge request"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": ("Internal ID of the merge request"),
                            }
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="list_project_members",
                    description=(
                        "List all project members with their usernames, IDs, and access levels. "
                        "Use this to find users for assigning or reviewing merge requests."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="list_project_labels",
                    description=(
                        "List all available labels in the project, including inherited group labels. "
                        "Use this to discover valid labels for merge requests."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="create_merge_request",
                    description=(
                        "Create a new merge request from source branch to target branch. "
                        "Accepts usernames (e.g., 'john.doe' or '@john.doe') for assignees and reviewers."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_branch": {
                                "type": "string",
                                "description": "The source branch name",
                            },
                            "target_branch": {
                                "type": "string",
                                "description": "The target branch name (e.g., 'main', 'develop')",
                            },
                            "title": {
                                "type": "string",
                                "description": "Title of the merge request",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description/body of the merge request (optional)",
                            },
                            "draft": {
                                "type": "boolean",
                                "default": False,
                                "description": "Create as draft/WIP merge request",
                            },
                            "squash": {
                                "type": "boolean",
                                "description": "Squash commits when merging (optional)",
                            },
                            "remove_source_branch": {
                                "type": "boolean",
                                "description": "Remove source branch after merge (optional)",
                            },
                            "labels": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Labels to apply (optional)",
                            },
                            "create_missing_labels": {
                                "type": "boolean",
                                "default": False,
                                "description": "Create labels if they don't exist (default: false)",
                            },
                            "assignees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Usernames to assign (e.g., ['john.doe', 'jane.smith'])",
                            },
                            "reviewers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Usernames to request review from",
                            },
                        },
                        "required": ["source_branch", "target_branch", "title"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="update_merge_request",
                    description=(
                        "Update an existing merge request. Can change assignees, reviewers, "
                        "labels, title, description, draft status, and more. "
                        "Pass empty arrays to clear assignees/reviewers/labels."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request to update",
                            },
                            "title": {
                                "type": "string",
                                "description": "New title (optional)",
                            },
                            "description": {
                                "type": "string",
                                "description": "New description (optional)",
                            },
                            "target_branch": {
                                "type": "string",
                                "description": "New target branch (optional)",
                            },
                            "draft": {
                                "type": "boolean",
                                "description": "Set draft status (true=draft, false=ready)",
                            },
                            "squash": {
                                "type": "boolean",
                                "description": "Squash commits when merging",
                            },
                            "remove_source_branch": {
                                "type": "boolean",
                                "description": "Remove source branch after merge",
                            },
                            "labels": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Labels to set (replaces existing). Empty array clears labels.",
                            },
                            "assignees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Usernames to assign (replaces existing). Empty array clears.",
                            },
                            "reviewers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Usernames for review (replaces existing). Empty array clears.",
                            },
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
            ]
            tool_names = [t.name for t in tools]
            logging.info(f"Returning {len(tools)} tools: {tool_names}")
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            logging.info(f"call_tool called: {name} with arguments: {arguments}")

            try:
                if name not in [
                    "list_merge_requests",
                    "get_merge_request_reviews",
                    "get_merge_request_details",
                    "get_merge_request_pipeline",
                    "get_merge_request_test_report",
                    "get_pipeline_test_summary",
                    "get_job_log",
                    "get_branch_merge_requests",
                    "reply_to_review_comment",
                    "create_review_comment",
                    "resolve_review_discussion",
                    "get_commit_discussions",
                    "list_project_members",
                    "list_project_labels",
                    "create_merge_request",
                    "update_merge_request",
                ]:
                    logging.warning(f"Unknown tool called: {name}")
                    raise McpError(error=ErrorData(code=METHOD_NOT_FOUND, message=f"Unknown tool: {name}"))

                if name == "list_merge_requests":
                    return await list_merge_requests(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "get_merge_request_reviews":
                    return await get_merge_request_reviews(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "get_merge_request_details":
                    return await get_merge_request_details(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "get_merge_request_pipeline":
                    return await get_merge_request_pipeline(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "get_merge_request_test_report":
                    return await get_merge_request_test_report(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "get_pipeline_test_summary":
                    return await get_pipeline_test_summary(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "get_job_log":
                    return await get_job_log(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "get_branch_merge_requests":
                    return await get_branch_merge_requests(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "reply_to_review_comment":
                    return await reply_to_review_comment(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "create_review_comment":
                    return await create_review_comment(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "resolve_review_discussion":
                    return await resolve_review_discussion(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "get_commit_discussions":
                    return await get_commit_discussions(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "list_project_members":
                    return await list_project_members(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "list_project_labels":
                    return await list_project_labels(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "create_merge_request":
                    return await create_merge_request(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )
                elif name == "update_merge_request":
                    return await update_merge_request(
                        self.config["gitlab_url"], self.config["project_id"], self.config["access_token"], arguments
                    )

            except ValueError as e:
                logging.error(f"Validation error in {name}: {e}")
                raise McpError(error=ErrorData(code=INVALID_PARAMS, message=f"Invalid parameters: {str(e)}"))
            except Exception as e:
                logging.error(f"Unexpected error in call_tool for {name}: {e}", exc_info=True)
                raise McpError(error=ErrorData(code=INTERNAL_ERROR, message=f"Internal server error: {str(e)}"))

    async def run(self):
        logging.info("Starting MCP stdio server")
        try:
            async with stdio_server() as (read_stream, write_stream):
                logging.info("stdio_server context entered successfully")
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=self.config["server_name"],
                        server_version=self.config["server_version"],
                        capabilities={"tools": {}, "logging": {}},
                    ),
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
        print(f"Error starting server: {e}")  # noqa: T201
        return 1


def main_sync():
    """Synchronous entry point for console script."""
    return asyncio.run(main())


if __name__ == "__main__":
    main_sync()
