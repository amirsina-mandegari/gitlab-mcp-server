#!/usr/bin/env python3
import asyncio
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    ErrorData,
    GetPromptResult,
    Prompt,
    PromptMessage,
    TextContent,
    Tool,
)

from gitlab_mr_mcp.config import get_gitlab_config
from gitlab_mr_mcp.logging_config import configure_logging
from gitlab_mr_mcp.prompts import PROMPTS
from gitlab_mr_mcp.tools import (
    approve_merge_request,
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
    list_my_projects,
    list_project_labels,
    list_project_members,
    merge_merge_request,
    reply_to_review_comment,
    resolve_review_discussion,
    search_projects,
    unapprove_merge_request,
    update_merge_request,
)

PROJECT_ID_SCHEMA = {
    "type": "string",
    "description": (
        "GitLab project ID or path (e.g., '12345' or 'group/project'). "
        "IMPORTANT: If unknown, first call search_projects or list_my_projects to find it."
    ),
}


def resolve_project_id(arguments, default_project_id):
    """Resolve project_id from arguments or fall back to default."""
    project_id = arguments.get("project_id") or default_project_id
    if not project_id:
        raise ValueError(
            "project_id is required but not provided. "
            "Please call search_projects(search='project name') or list_my_projects() first to find the project ID, "
            "then pass it as project_id parameter."
        )
    return project_id


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
            read_only = {"readOnlyHint": True}
            write_op = {"readOnlyHint": False}
            destructive = {"readOnlyHint": False, "destructiveHint": True}

            tools = [
                Tool(
                    name="search_projects",
                    title="Search Projects",
                    description=(
                        "PRIMARY tool to find projects. Use when user mentions ANY project name. "
                        "ALWAYS prefer this over list_my_projects."
                    ),
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search": {
                                "type": "string",
                                "description": "Project name or partial name (e.g., 'backend', 'api', 'frontend')",
                            },
                            "membership": {
                                "type": "boolean",
                                "default": True,
                                "description": "Only show projects user is a member of",
                            },
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
                    name="list_my_projects",
                    title="List All Projects",
                    description=(
                        "List ALL projects (slow). Only use when user asks 'what projects do I have' "
                        "or needs to browse without knowing any name."
                    ),
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "owned": {
                                "type": "boolean",
                                "default": False,
                                "description": "Only show projects owned by the user",
                            },
                            "limit": {
                                "type": "integer",
                                "default": 20,
                                "minimum": 1,
                                "maximum": 100,
                                "description": "Maximum number of results",
                            },
                        },
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="list_merge_requests",
                    title="List Merge Requests",
                    description="List merge requests for a GitLab project with optional filters.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "state": {
                                "type": "string",
                                "enum": ["opened", "closed", "merged", "all"],
                                "default": "opened",
                                "description": "Filter by merge request state",
                            },
                            "target_branch": {
                                "type": "string",
                                "description": "Filter by target branch (optional)",
                            },
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
                    title="Get MR Reviews",
                    description="Get reviews and discussions for a merge request. Returns discussion IDs for replying.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request",
                            },
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_merge_request_details",
                    title="Get MR Details",
                    description="Get MR details including status, approvals, and merge readiness.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request",
                            },
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_merge_request_pipeline",
                    title="Get MR Pipeline",
                    description="Get pipeline data with all jobs and statuses. Returns job IDs for get_job_log.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request",
                            },
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_merge_request_test_report",
                    title="Get MR Test Report",
                    description="Get test report with failures, error messages, and stack traces.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request",
                            },
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_pipeline_test_summary",
                    title="Get Test Summary",
                    description="Get test summary with pass/fail counts. Faster than full test report.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request",
                            },
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_job_log",
                    title="Get Job Log",
                    description="Get trace/log output for a pipeline job. Use for debugging CI/CD failures.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "job_id": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "ID of the pipeline job (from get_merge_request_pipeline)",
                            },
                        },
                        "required": ["job_id"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_branch_merge_requests",
                    title="Get Branch MRs",
                    description="Get all merge requests for a specific branch.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "branch_name": {
                                "type": "string",
                                "description": "Name of the branch",
                            },
                        },
                        "required": ["branch_name"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="reply_to_review_comment",
                    title="Reply to Discussion",
                    description="Reply to a discussion thread in a merge request review.",
                    annotations=write_op,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request",
                            },
                            "discussion_id": {
                                "type": "string",
                                "description": "ID of the discussion thread to reply to",
                            },
                            "body": {
                                "type": "string",
                                "description": "Content of the reply comment",
                            },
                        },
                        "required": ["merge_request_iid", "discussion_id", "body"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="create_review_comment",
                    title="Create Discussion",
                    description="Create a new discussion thread in a merge request.",
                    annotations=write_op,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request",
                            },
                            "body": {
                                "type": "string",
                                "description": "Content of the new discussion comment",
                            },
                        },
                        "required": ["merge_request_iid", "body"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="resolve_review_discussion",
                    title="Resolve Discussion",
                    description="Resolve or unresolve a discussion thread in a merge request.",
                    annotations=write_op,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request",
                            },
                            "discussion_id": {
                                "type": "string",
                                "description": "ID of the discussion thread to resolve/unresolve",
                            },
                            "resolved": {
                                "type": "boolean",
                                "default": True,
                                "description": "Whether to resolve (true) or unresolve (false)",
                            },
                        },
                        "required": ["merge_request_iid", "discussion_id"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_commit_discussions",
                    title="Get Commit Discussions",
                    description="Get discussions and comments on commits within a merge request.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request",
                            },
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="list_project_members",
                    title="List Project Members",
                    description="List project members with usernames and access levels.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                        },
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="list_project_labels",
                    title="List Project Labels",
                    description="List all available labels in the project including inherited group labels.",
                    annotations=read_only,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                        },
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="create_merge_request",
                    title="Create Merge Request",
                    description="Create a new merge request. Accepts usernames for assignees and reviewers.",
                    annotations=write_op,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
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
                    title="Update Merge Request",
                    description="Update a merge request. Pass empty arrays to clear assignees/reviewers/labels.",
                    annotations=write_op,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
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
                                "description": "Labels to set (replaces existing). Empty array clears.",
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
                Tool(
                    name="merge_merge_request",
                    title="Merge MR",
                    description="Merge a merge request. Check merge status with get_merge_request_details first.",
                    annotations=destructive,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request to merge",
                            },
                            "squash": {
                                "type": "boolean",
                                "default": False,
                                "description": "Squash commits into a single commit",
                            },
                            "should_remove_source_branch": {
                                "type": "boolean",
                                "default": False,
                                "description": "Remove source branch after merge",
                            },
                            "merge_when_pipeline_succeeds": {
                                "type": "boolean",
                                "default": False,
                                "description": "Merge when pipeline succeeds (auto-merge)",
                            },
                            "sha": {
                                "type": "string",
                                "description": "HEAD SHA to ensure no new commits (safety check)",
                            },
                            "merge_commit_message": {
                                "type": "string",
                                "description": "Custom merge commit message (optional)",
                            },
                            "squash_commit_message": {
                                "type": "string",
                                "description": "Custom squash commit message (optional)",
                            },
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="approve_merge_request",
                    title="Approve MR",
                    description="Approve a merge request. Note: You cannot approve your own MRs.",
                    annotations=write_op,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request to approve",
                            },
                            "sha": {
                                "type": "string",
                                "description": "HEAD SHA to ensure approving the right version (optional)",
                            },
                        },
                        "required": ["merge_request_iid"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="unapprove_merge_request",
                    title="Unapprove MR",
                    description="Revoke your approval from a merge request.",
                    annotations=write_op,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": PROJECT_ID_SCHEMA,
                            "merge_request_iid": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Internal ID of the merge request to unapprove",
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
                valid_tools = [
                    "search_projects",
                    "list_my_projects",
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
                    "merge_merge_request",
                    "approve_merge_request",
                    "unapprove_merge_request",
                ]

                if name not in valid_tools:
                    logging.warning(f"Unknown tool called: {name}")
                    raise McpError(error=ErrorData(code=METHOD_NOT_FOUND, message=f"Unknown tool: {name}"))

                gitlab_url = self.config["gitlab_url"]
                access_token = self.config["access_token"]
                default_project_id = self.config["project_id"]

                if name == "search_projects":
                    return await search_projects(gitlab_url, access_token, arguments)
                elif name == "list_my_projects":
                    return await list_my_projects(gitlab_url, access_token, arguments)

                project_id = resolve_project_id(arguments, default_project_id)

                if name == "list_merge_requests":
                    return await list_merge_requests(gitlab_url, project_id, access_token, arguments)
                elif name == "get_merge_request_reviews":
                    return await get_merge_request_reviews(gitlab_url, project_id, access_token, arguments)
                elif name == "get_merge_request_details":
                    return await get_merge_request_details(gitlab_url, project_id, access_token, arguments)
                elif name == "get_merge_request_pipeline":
                    return await get_merge_request_pipeline(gitlab_url, project_id, access_token, arguments)
                elif name == "get_merge_request_test_report":
                    return await get_merge_request_test_report(gitlab_url, project_id, access_token, arguments)
                elif name == "get_pipeline_test_summary":
                    return await get_pipeline_test_summary(gitlab_url, project_id, access_token, arguments)
                elif name == "get_job_log":
                    return await get_job_log(gitlab_url, project_id, access_token, arguments)
                elif name == "get_branch_merge_requests":
                    return await get_branch_merge_requests(gitlab_url, project_id, access_token, arguments)
                elif name == "reply_to_review_comment":
                    return await reply_to_review_comment(gitlab_url, project_id, access_token, arguments)
                elif name == "create_review_comment":
                    return await create_review_comment(gitlab_url, project_id, access_token, arguments)
                elif name == "resolve_review_discussion":
                    return await resolve_review_discussion(gitlab_url, project_id, access_token, arguments)
                elif name == "get_commit_discussions":
                    return await get_commit_discussions(gitlab_url, project_id, access_token, arguments)
                elif name == "list_project_members":
                    return await list_project_members(gitlab_url, project_id, access_token, arguments)
                elif name == "list_project_labels":
                    return await list_project_labels(gitlab_url, project_id, access_token, arguments)
                elif name == "create_merge_request":
                    return await create_merge_request(gitlab_url, project_id, access_token, arguments)
                elif name == "update_merge_request":
                    return await update_merge_request(gitlab_url, project_id, access_token, arguments)
                elif name == "merge_merge_request":
                    return await merge_merge_request(gitlab_url, project_id, access_token, arguments)
                elif name == "approve_merge_request":
                    return await approve_merge_request(gitlab_url, project_id, access_token, arguments)
                elif name == "unapprove_merge_request":
                    return await unapprove_merge_request(gitlab_url, project_id, access_token, arguments)

            except ValueError as e:
                logging.error(f"Validation error in {name}: {e}")
                raise McpError(error=ErrorData(code=INVALID_PARAMS, message=f"Invalid parameters: {str(e)}"))
            except Exception as e:
                logging.error(f"Unexpected error in call_tool for {name}: {e}", exc_info=True)
                raise McpError(error=ErrorData(code=INTERNAL_ERROR, message=f"Internal server error: {str(e)}"))

        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            return [Prompt(name=name, description=data["description"]) for name, data in PROMPTS.items()]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
            if name not in PROMPTS:
                raise McpError(error=ErrorData(code=METHOD_NOT_FOUND, message=f"Unknown prompt: {name}"))
            prompt_data = PROMPTS[name]
            return GetPromptResult(
                description=prompt_data["description"],
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=prompt_data["content"]),
                    )
                ],
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
                        server_name=self.config["server_name"],
                        server_version=self.config["server_version"],
                        capabilities={"tools": {}, "prompts": {}, "logging": {}},
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
