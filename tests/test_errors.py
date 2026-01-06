"""Test error handling."""

import os
from unittest.mock import patch

import pytest

from gitlab_mr_mcp.config import get_gitlab_config


def test_config_missing_project_id():
    """Test that missing GITLAB_PROJECT_ID raises error."""
    with patch.dict(os.environ, {}, clear=True):
        # Remove the env vars
        with patch.dict(
            os.environ,
            {"GITLAB_ACCESS_TOKEN": "test-token", "GITLAB_URL": "https://gitlab.com"},
            clear=True,
        ):
            with pytest.raises(Exception) as exc_info:
                get_gitlab_config()

            assert "GITLAB_PROJECT_ID" in str(exc_info.value)


def test_config_missing_access_token():
    """Test that missing GITLAB_ACCESS_TOKEN raises error."""
    with patch.dict(
        os.environ,
        {"GITLAB_PROJECT_ID": "123", "GITLAB_URL": "https://gitlab.com"},
        clear=True,
    ):
        with pytest.raises(Exception) as exc_info:
            get_gitlab_config()

        assert "GITLAB_ACCESS_TOKEN" in str(exc_info.value)


def test_config_valid():
    """Test valid configuration."""
    with patch.dict(
        os.environ,
        {
            "GITLAB_PROJECT_ID": "123",
            "GITLAB_ACCESS_TOKEN": "test-token",
            "GITLAB_URL": "https://gitlab.example.com",
            "SERVER_NAME": "test-server",
            "SERVER_VERSION": "2.0.0",
        },
        clear=True,
    ):
        config = get_gitlab_config()

        assert config["project_id"] == "123"
        assert config["access_token"] == "test-token"
        assert config["gitlab_url"] == "https://gitlab.example.com"
        assert config["server_name"] == "test-server"
        assert config["server_version"] == "2.0.0"


def test_config_defaults():
    """Test configuration defaults."""
    with patch.dict(
        os.environ,
        {
            "GITLAB_PROJECT_ID": "123",
            "GITLAB_ACCESS_TOKEN": "test-token",
        },
        clear=True,
    ):
        config = get_gitlab_config()

        assert config["gitlab_url"] == "https://gitlab.com"
        assert config["server_name"] == "gitlab-mcp-server"
        assert config["server_version"] == "1.0.0"
