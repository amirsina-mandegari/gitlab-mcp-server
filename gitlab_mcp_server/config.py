#!/usr/bin/env python3
"""Configuration management for GitLab MCP Server."""

from decouple import config


def get_gitlab_config():
    """Get GitLab configuration from environment variables."""
    gitlab_url = config("GITLAB_URL", default="https://gitlab.com")
    project_id = config("GITLAB_PROJECT_ID")
    access_token = config("GITLAB_ACCESS_TOKEN")

    if not project_id:
        raise ValueError("GITLAB_PROJECT_ID environment variable is required")
    if not access_token:
        raise ValueError("GITLAB_ACCESS_TOKEN environment variable is required")

    return {
        "gitlab_url": gitlab_url,
        "project_id": project_id,
        "access_token": access_token,
        "server_name": config("SERVER_NAME", default="gitlab-mcp-server"),
        "server_version": config("SERVER_VERSION", default="1.0.0"),
    }


def get_headers(access_token):
    """Get HTTP headers for GitLab API requests."""
    return {"Private-Token": access_token, "Content-Type": "application/json"}
