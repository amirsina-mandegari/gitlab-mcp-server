# GitLab MR MCP

[![CI](https://github.com/amirsina-mandegari/gitlab-mr-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/amirsina-mandegari/gitlab-mr-mcp/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/gitlab-mr-mcp.svg)](https://pypi.org/project/gitlab-mr-mcp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/gitlab-mr-mcp.svg)](https://pypi.org/project/gitlab-mr-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Connect your AI assistant to GitLab. Ask questions like _"List open merge requests"_, _"Show me reviews for MR #123"_, _"Get commit discussions for MR #456"_, or _"Find merge requests for the feature branch"_ directly in your chat.

## Table of Contents

- [Quick Setup](#quick-setup)
- [What You Can Do](#what-you-can-do)
- [Configuration Options](#configuration-options)
- [Troubleshooting](#troubleshooting)
- [Tool Reference](#tool-reference)
- [Development](#development)
- [Security Notes](#security-notes)
- [Support](#support)

## Quick Setup

### Installation

```bash
# Using pipx (recommended)
pipx install gitlab-mr-mcp

# Or using uv
uv tool install gitlab-mr-mcp

# Or using pip
pip install gitlab-mr-mcp
```

> **Note:** Using `pipx` or `uv tool` is recommended as they automatically add the `gitlab-mcp` command to your PATH. If using `pip install`, ensure your Python scripts directory is in PATH, or use the full path to the command.

### Get your GitLab token

1. Go to GitLab → Settings → Access Tokens
2. Create token with **`read_api`** scope (add `api` scope if you want write access)
3. Copy the token

### Configure your MCP client

Add to your MCP config (e.g., `.cursor/mcp.json` for Cursor):

```json
{
  "mcpServers": {
    "gitlab-mcp": {
      "command": "gitlab-mcp",
      "env": {
        "GITLAB_URL": "https://gitlab.com",
        "GITLAB_ACCESS_TOKEN": "glpat-xxxxxxxxxxxxxxxxxxxx",
        "GITLAB_PROJECT_ID": "12345"
      }
    }
  }
}
```

Restart your MCP client and start asking GitLab questions!

## What You Can Do

Once connected, try these commands in your chat:

- _"List open merge requests"_
- _"Show me details for merge request 456"_
- _"Get reviews and discussions for MR #123"_
- _"Show me the test summary for MR #456"_
- _"What tests failed in merge request #789?"_
- _"Show me the pipeline for MR #456"_
- _"Get the failed job logs for merge request #789"_
- _"Show me commit discussions for MR #456"_
- _"Get all comments on commits in merge request #789"_
- _"Find merge requests for the feature/auth-improvements branch"_
- _"Show me closed merge requests targeting main"_
- _"Reply to discussion abc123 in MR #456 with 'Thanks for the feedback!'"_
- _"Create a new review comment in MR #789 asking about the error handling"_
- _"Resolve discussion def456 in MR #123"_

## Working with Review Comments

The enhanced review tools allow you to interact with merge request discussions:

1. **First, get the reviews** to see discussion IDs:

   ```
   "Show me reviews for MR #123"
   ```

2. **Reply to specific discussions** using the discussion ID:

   ```
   "Reply to discussion abc123 in MR #456 with 'I'll fix this in the next commit'"
   ```

3. **Create new discussion threads** to start conversations:

   ```
   "Create a review comment in MR #789 asking 'Could you add error handling here?'"
   ```

4. **Resolve discussions** when issues are addressed:
   ```
   "Resolve discussion def456 in MR #123"
   ```

**Note**: The `get_merge_request_reviews` tool now displays discussion IDs and note IDs in the output, making it easy to reference specific discussions when replying or resolving.

## Working with Test Reports (Recommended for Test Failures)

GitLab provides two tools for checking test results - use the summary for quick checks, and the full report for detailed debugging:

### Option 1: Test Summary (Fast & Lightweight) ⚡

Use `get_pipeline_test_summary` for a quick overview:

```
"Show me the test summary for MR #123"
"How many tests passed in MR #456?"
```

**What You Get:**

- 📊 Pass/fail counts per test suite
- ⏱️ Total execution time
- 🎯 Pass rate percentage
- ⚡ **Fast** - doesn't include detailed error messages

### Option 2: Full Test Report (Detailed) 🔍

Use `get_merge_request_test_report` for detailed debugging:

```
"Show me the test report for MR #123"
"What tests failed in merge request #456?"
```

**What You Get:**

- ✅ **Specific test names** that passed/failed
- ❌ **Error messages** and stack traces
- 📦 **Test suites** organized by class/file
- ⏱️ **Execution time** for each test
- 📊 **Pass rate** and summary statistics
- 📄 **File paths** and line numbers

**How Both Work:**

- Automatically fetch the latest pipeline for the merge request
- Retrieve test data from that pipeline (uses GitLab's `/pipelines/:pipeline_id/test_report` or `/test_report_summary` API)

**Example Output:**

```
Test Report Summary:
Total: 45 tests | ✅ 42 passed | ❌ 3 failed | Pass Rate: 93.3%

❌ Failed Tests:
  test_login_with_invalid_password (0.3s)
    Error: AssertionError: Expected 401, got 200
    File: tests/auth_test.py
```

**Why Use This Instead of Job Logs?**

- 🎯 **No noise**: Only test results, no build/setup output
- 📊 **Structured data**: Easy for AI to understand and suggest fixes
- 🚀 **Fast**: Much smaller than full job logs
- 🔍 **Precise**: Shows exact test names and error locations

**Requirements:**

Your CI must upload test results using `artifacts:reports:junit` in `.gitlab-ci.yml`:

```yaml
test:
  script:
    - pytest --junitxml=report.xml
  artifacts:
    reports:
      junit: report.xml
```

## Working with Pipeline Jobs and Logs

The pipeline tools provide a two-step workflow for debugging test failures:

### Step 1: Get Pipeline Overview

Use `get_merge_request_pipeline` to see all jobs and their statuses:

```
"Show me the pipeline for MR #456"
```

**What You Get:**

- Pipeline overview (status, duration, coverage)
- All jobs grouped by status (failed, running, success)
- **Job IDs** for each job (use these to fetch logs)
- Direct links to view jobs in GitLab
- Job-level timing and stage information

### Step 2: Get Specific Job Logs

Use `get_job_log` with a job ID to fetch the actual output:

```
"Get the log for job 12345"
"Show me the output of job 67890"
```

**What You Get:**

- Complete job output/trace
- Log size and line count
- Automatically truncated to last 15,000 characters for very long logs

### Typical Workflow:

```
You: "Show me the pipeline for MR #123"
AI: "Pipeline failed. 2 jobs failed:
     - test-unit (Job ID: 12345)
     - test-integration (Job ID: 67890)"

You: "Get the log for job 12345"
AI: [Shows full test output with error details]

You: "Fix the failing test"
AI: [Analyzes the log and suggests fixes]
```

**Why Two Tools?**

- **Performance**: Only fetch logs when needed (not all at once)
- **Flexibility**: Check any job's log (failed, successful, or running)
- **Context Efficient**: Avoid dumping huge logs unnecessarily

## Working with Commit Discussions

The `get_commit_discussions` tool provides comprehensive insights into discussions and comments on individual commits within a merge request:

1. **View all commit discussions** for a merge request:

   ```
   "Show me commit discussions for MR #123"
   ```

2. **Get detailed commit conversation history**:

   ```
   "Get all comments on commits in merge request #456"
   ```

This tool is particularly useful for:

- **Code Review Tracking**: See all feedback on specific commits
- **Discussion History**: Understand the evolution of code discussions
- **Commit-Level Context**: View comments tied to specific code changes
- **Review Progress**: Monitor which commits have been discussed

**Technical Implementation:**

- Uses `/projects/:project_id/merge_requests/:merge_request_iid/commits` to get all commits with proper pagination
- Fetches ALL merge request discussions using `/projects/:project_id/merge_requests/:merge_request_iid/discussions` with pagination support
- Filters discussions by commit SHA using position data to show commit-specific conversations
- Handles both individual comments and discussion threads correctly

The output includes:

- Summary of total commits and discussion counts
- Individual commit details (SHA, title, author, date)
- All discussions and comments for each commit with file positions
- Complete conversation threads with replies
- File positions for diff-related comments
- Thread conversations with replies

## Configuration Options

### MCP Config (Recommended)

Configure environment variables directly in your MCP client config as shown in [Quick Setup](#quick-setup). This keeps project-specific settings with the project.

### Environment Variables

Alternatively, set environment variables in your shell:

```bash
export GITLAB_PROJECT_ID=12345
export GITLAB_ACCESS_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
export GITLAB_URL=https://gitlab.com
```

### Find Your Project ID

- Go to your GitLab project → Settings → General → Project ID
- Or check the URL: `https://gitlab.com/username/project` (use the numeric ID)

## Troubleshooting

**Authentication Error**: Verify your token has `read_api` permissions and is not expired.

**Project Not Found**: Double-check your project ID is correct (it's a number, not the project name).

**Connection Issues**: Make sure your GitLab URL is accessible and correct.

**Script Not Found**: Ensure the path in your MCP config points to the actual server location and the script is executable.

## Tool Reference

| Tool                            | Description                       | Parameters                                       |
| ------------------------------- | --------------------------------- | ------------------------------------------------ |
| `list_merge_requests`           | List merge requests               | `state`, `target_branch`, `limit`                |
| `get_merge_request_details`     | Get MR details                    | `merge_request_iid`                              |
| `create_merge_request`          | Create a new merge request        | `source_branch`, `target_branch`, `title`, etc.  |
| `update_merge_request`          | Update an existing merge request  | `merge_request_iid`, `title`, `assignees`, etc.  |
| `get_pipeline_test_summary`     | Get test summary (fast overview)  | `merge_request_iid`                              |
| `get_merge_request_test_report` | Get detailed test failure reports | `merge_request_iid`                              |
| `get_merge_request_pipeline`    | Get pipeline with all jobs        | `merge_request_iid`                              |
| `get_job_log`                   | Get trace/output for specific job | `job_id`                                         |
| `get_merge_request_reviews`     | Get reviews/discussions           | `merge_request_iid`                              |
| `get_commit_discussions`        | Get discussions on commits        | `merge_request_iid`                              |
| `get_branch_merge_requests`     | Find MRs for branch               | `branch_name`                                    |
| `reply_to_review_comment`       | Reply to existing discussion      | `merge_request_iid`, `discussion_id`, `body`     |
| `create_review_comment`         | Create new discussion thread      | `merge_request_iid`, `body`                      |
| `resolve_review_discussion`     | Resolve/unresolve discussion      | `merge_request_iid`, `discussion_id`, `resolved` |
| `list_project_members`          | List project members              | (none)                                           |
| `list_project_labels`           | List project labels               | (none)                                           |

## Development

### Project Structure

```
gitlab_mr_mcp/
├── __init__.py          # Package version
├── __main__.py          # Entry point for python -m
├── server.py            # MCP server implementation
├── config.py            # Configuration management
├── gitlab_api.py        # GitLab API client
├── utils.py             # Utility functions
├── logging_config.py    # Logging configuration
└── tools/               # Tool implementations
    ├── __init__.py
    ├── list_merge_requests.py
    ├── get_merge_request_details.py
    ├── create_merge_request.py
    ├── update_merge_request.py
    └── ... (more tools)
```

### Adding Tools

1. Create new file in `gitlab_mr_mcp/tools/` directory
2. Add import and export to `gitlab_mr_mcp/tools/__init__.py`
3. Add to `list_tools()` in `gitlab_mr_mcp/server.py`
4. Add handler to `call_tool()` in `gitlab_mr_mcp/server.py`

### Development Setup

1. **Install development dependencies:**

```bash
uv pip install -e ".[dev]"
```

2. **Set up pre-commit hooks:**

```bash
pre-commit install
```

This will automatically check and format your code for:

- ✨ **Trailing whitespace** - auto-removed
- 📄 **End-of-file issues** - auto-fixed
- 🎨 **Code formatting (black)** - auto-formatted
- 📦 **Import sorting (isort)** - auto-organized
- 🐍 **Python style (flake8)** - linted with bugbear & print detection
- 🔒 **Security issues (bandit)** - security checks
- 📋 **YAML/JSON formatting** - validated

3. **Format all existing code (first time only):**

```bash
# Install dependencies first if not already done
uv pip install -e ".[dev]"

# Format everything
black --line-length=120 .
isort --profile black --line-length=120 .
```

4. **Run pre-commit manually on all files:**

```bash
pre-commit run --all-files
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v
```

## Security Notes

- Never commit access tokens to version control
- Use project-specific tokens with minimal permissions (`read_api` scope)
- Rotate tokens regularly
- Store tokens in your MCP config (which should not be committed)

## Support

- Check [GitLab API documentation](https://docs.gitlab.com/ee/api/)
- Open issues at [github.com/amirsina-mandegari/gitlab-mr-mcp](https://github.com/amirsina-mandegari/gitlab-mr-mcp)

## License

MIT License - see LICENSE file for details.
