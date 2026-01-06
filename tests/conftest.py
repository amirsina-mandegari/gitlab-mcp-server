"""Shared test fixtures for GitLab MCP tests."""

import pytest

# Common test data
GITLAB_URL = "https://gitlab.example.com"
PROJECT_ID = "123"
ACCESS_TOKEN = "test-token"  # nosec B105


@pytest.fixture
def gitlab_credentials():
    """Return standard GitLab credentials for testing."""
    return {
        "gitlab_url": GITLAB_URL,
        "project_id": PROJECT_ID,
        "access_token": ACCESS_TOKEN,
    }


@pytest.fixture
def sample_merge_request():
    """Return a sample merge request object."""
    return {
        "iid": 42,
        "title": "Add new feature",
        "description": "This MR adds a cool new feature",
        "state": "opened",
        "draft": False,
        "author": {"username": "johndoe", "name": "John Doe"},
        "assignees": [{"username": "reviewer1", "name": "Reviewer One"}],
        "reviewers": [{"username": "reviewer2", "name": "Reviewer Two"}],
        "source_branch": "feature-branch",
        "target_branch": "main",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-16T10:00:00Z",
        "merged_at": None,
        "web_url": "https://gitlab.example.com/project/-/merge_requests/42",
        "labels": ["enhancement", "needs-review"],
        "has_conflicts": False,
        "merge_status": "can_be_merged",
    }


@pytest.fixture
def sample_pipeline():
    """Return a sample pipeline object."""
    return {
        "id": 789,
        "status": "success",
        "ref": "feature-branch",
        "sha": "abc123def456",
        "web_url": "https://gitlab.example.com/project/-/pipelines/789",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def sample_job():
    """Return a sample job object."""
    return {
        "id": 999,
        "name": "test",
        "status": "success",
        "stage": "test",
        "web_url": "https://gitlab.example.com/project/-/jobs/999",
        "duration": 120.5,
        "started_at": "2024-01-15T10:00:00Z",
        "finished_at": "2024-01-15T10:02:00Z",
    }


@pytest.fixture
def sample_discussion():
    """Return a sample discussion object."""
    return {
        "id": "abc123",
        "individual_note": False,
        "notes": [
            {
                "id": 1,
                "body": "Please fix this issue",
                "author": {"username": "reviewer", "name": "Reviewer"},
                "created_at": "2024-01-15T10:00:00Z",
                "resolvable": True,
                "resolved": False,
            }
        ],
    }


@pytest.fixture
def sample_project_member():
    """Return a sample project member object."""
    return {
        "id": 1,
        "username": "developer",
        "name": "Developer Name",
        "state": "active",
        "access_level": 30,
        "web_url": "https://gitlab.example.com/developer",
    }


@pytest.fixture
def sample_label():
    """Return a sample label object."""
    return {
        "id": 1,
        "name": "bug",
        "color": "#ff0000",
        "description": "Bug label",
    }


@pytest.fixture
def sample_test_report():
    """Return a sample test report object."""
    return {
        "total_time": 120.5,
        "total_count": 100,
        "success_count": 98,
        "failed_count": 2,
        "skipped_count": 0,
        "error_count": 0,
        "test_suites": [
            {
                "name": "Unit Tests",
                "total_time": 60.0,
                "total_count": 50,
                "success_count": 49,
                "failed_count": 1,
                "skipped_count": 0,
                "error_count": 0,
            }
        ],
    }
