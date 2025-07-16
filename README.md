# GitLab MCP Server

Connect your AI assistant to GitLab. Ask questions like *"List open merge requests"*, *"Show me reviews for MR #123"*, or *"Find merge requests for the feature branch"* directly in your chat.

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

- *"List open merge requests"*
- *"Show me details for merge request 456"*
- *"Get reviews and discussions for MR #123"*
- *"Find merge requests for the feature/auth-improvements branch"*
- *"Show me closed merge requests targeting main"*

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

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_merge_requests` | List merge requests | `state`, `target_branch`, `limit` |
| `get_merge_request_details` | Get MR details | `merge_request_iid` |
| `get_merge_request_reviews` | Get reviews/discussions | `merge_request_iid` |
| `get_branch_merge_requests` | Find MRs for branch | `branch_name` |

## Development

### Project Structure
```
gitlab-mcp-server/
├── main.py              # MCP server entry point
├── config.py            # Configuration management
├── gitlab_api.py        # GitLab API client
├── run-mcp.sh          # Launch script
└── tools/              # Tool implementations
```

### Adding Tools
1. Create new file in `tools/`
2. Add to `list_tools()` in `main.py`
3. Add handler to `call_tool()` in `main.py`

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
