# GitLab MCP Server

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
pipx install gitlab-mcp-server

# Or using pip
pip install gitlab-mcp-server
```

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

### Project-Level (Recommended)

Each project gets its own `gitlab-mcp.env` file with its own GitLab configuration. Keep tokens out of version control.

### Global Configuration

Set environment variables system-wide instead of per-project:

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

## Migrating from pip to uv

If you have an existing installation using pip, here's how to migrate to uv:

1. **Install uv** (see Prerequisites section above)

2. **Remove the old virtual environment:**

   ```bash
   deactivate  # If you have a venv activated
   rm -rf .venv
   ```

3. **Create a new virtual environment with uv:**

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

4. **For development, install dev dependencies:**

   ```bash
   uv pip install -e ".[dev]"
   ```

That's it! Your project is now using uv for faster and more reliable dependency management.

**Note:** The `requirements.txt` and `dev-requirements.txt` files are kept for backward compatibility. However, `pyproject.toml` is now the source of truth for dependencies. If you add new dependencies, update `pyproject.toml` and regenerate the requirements files if needed:

```bash
uv pip compile pyproject.toml -o requirements.txt
uv pip compile --extra dev pyproject.toml -o dev-requirements.txt
```

## Development

### Project Structure

```
gitlab-mcp-server/
├── main.py              # MCP server entry point
├── config.py            # Configuration management
├── gitlab_api.py        # GitLab API client
├── utils.py             # Utility functions
├── logging_config.py    # Logging configuration
├── run-mcp.sh          # Launch script
└── tools/              # Tool implementations package
    ├── __init__.py         # Package initialization
    ├── list_merge_requests.py
    ├── get_merge_request_details.py
    ├── get_merge_request_test_report.py
    ├── get_pipeline_test_summary.py
    ├── get_merge_request_pipeline.py
    ├── get_job_log.py
    ├── get_merge_request_reviews.py
    ├── get_commit_discussions.py
    ├── get_branch_merge_requests.py
    └── reply_to_review_comment.py
```

### Adding Tools

1. Create new file in `tools/` directory
2. Add import and export to `tools/__init__.py`
3. Add to `list_tools()` in `main.py`
4. Add handler to `call_tool()` in `main.py`

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

### Testing

```bash
python test_tools.py
```

## Security Notes

- Add `gitlab-mcp.env` to your `.gitignore`
- Never commit access tokens
- Use project-specific tokens with minimal permissions
- Rotate tokens regularly

## Support

- Check [GitLab API documentation](https://docs.gitlab.com/ee/api/)
- Open issues at [github.com/amirsina-mandegari/gitlab-mcp-server](https://github.com/amirsina-mandegari/gitlab-mcp-server)

## License

MIT License - see LICENSE file for details.
