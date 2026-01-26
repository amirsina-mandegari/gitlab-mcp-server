#!/usr/bin/env python3
"""Configuration management for GitLab MCP Server."""

import os


def get_gitlab_config():
    """Get GitLab configuration from environment variables."""
    gitlab_url = os.environ.get("GITLAB_URL", "https://gitlab.com")
    project_id = os.environ.get("GITLAB_PROJECT_ID")
    access_token = os.environ.get("GITLAB_ACCESS_TOKEN")

    if not project_id:
        raise ValueError("GITLAB_PROJECT_ID environment variable is required")
    if not access_token:
        raise ValueError("GITLAB_ACCESS_TOKEN environment variable is required")

    return {
        "gitlab_url": gitlab_url,
        "project_id": project_id,
        "access_token": access_token,
        "server_name": os.environ.get("SERVER_NAME", "gitlab-mcp-server"),
        "server_version": os.environ.get("SERVER_VERSION", "1.0.0"),
    }


def get_headers(access_token):
    """Get HTTP headers for GitLab API requests."""
    return {"Private-Token": access_token, "Content-Type": "application/json"}
