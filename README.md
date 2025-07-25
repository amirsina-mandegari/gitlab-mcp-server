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

1. **Install the server:**

   ```bash
   git clone https://github.com/amirsina-mandegari/gitlab-mcp-server.git
   cd gitlab-mcp-server
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   chmod +x run-mcp.sh
   ```

2. **Get your GitLab token:**

   - Go to GitLab → Settings → Access Tokens
   - Create token with **`read_api`** scope
   - Copy the token

3. **Configure your project:**
   In your project directory, create `gitlab-mcp.env`:

   ```env
   GITLAB_PROJECT_ID=12345
   GITLAB_ACCESS_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
   GITLAB_URL=https://gitlab.com
   ```

4. **Connect to Cursor:**
   Create `.cursor/mcp.json` in your project:

   ```json
   {
     "mcpServers": {
       "gitlab-mcp": {
         "command": "/path/to/gitlab-mcp-server/run-mcp.sh",
         "cwd": "/path/to/your-project"
       }
     }
   }
   ```

5. **Restart Cursor** and start asking GitLab questions!

## What You Can Do

Once connected, try these commands in your chat:

- _"List open merge requests"_
- _"Show me details for merge request 456"_
- _"Get reviews and discussions for MR #123"_
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

| Tool                        | Description                  | Parameters                                       |
| --------------------------- | ---------------------------- | ------------------------------------------------ |
| `list_merge_requests`       | List merge requests          | `state`, `target_branch`, `limit`                |
| `get_merge_request_details` | Get MR details               | `merge_request_iid`                              |
| `get_merge_request_reviews` | Get reviews/discussions      | `merge_request_iid`                              |
| `get_commit_discussions`    | Get discussions on commits   | `merge_request_iid`                              |
| `get_branch_merge_requests` | Find MRs for branch          | `branch_name`                                    |
| `reply_to_review_comment`   | Reply to existing discussion | `merge_request_iid`, `discussion_id`, `body`     |
| `create_review_comment`     | Create new discussion thread | `merge_request_iid`, `body`                      |
| `resolve_review_discussion` | Resolve/unresolve discussion | `merge_request_iid`, `discussion_id`, `resolved` |

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
