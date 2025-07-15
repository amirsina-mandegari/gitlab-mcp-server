# GitLab MCP Server

A Model Context Protocol (MCP) server that provides GitLab integration for AI assistants. This server allows AI models to interact with GitLab projects, retrieve merge request information, reviews, and branch details.

## Features

- **List Merge Requests**: Get merge requests filtered by state, target branch, and limit
- **Get Merge Request Details**: Retrieve detailed information about specific merge requests
- **Get Merge Request Reviews**: Access reviews and discussions for merge requests
- **Get Branch Merge Requests**: Find merge requests associated with specific branches

## Prerequisites

- Python 3.8+
- GitLab account with API access
- GitLab Personal Access Token with appropriate permissions

## Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd gitlab-mcp-server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure it with your GitLab details:

```bash
cp .env.example .env
```

Then edit the `.env` file with your configuration:

```env
# Required Environment Variables
GITLAB_PROJECT_ID=your-project-id
GITLAB_ACCESS_TOKEN=your-access-token

# Optional Environment Variables
GITLAB_URL=https://gitlab.com
SERVER_NAME=gitlab-mcp-server
SERVER_VERSION=1.0.0
```

**Important:** Replace `your-project-id` and `your-access-token` with your actual GitLab values.

**Environment Variables Explained:**

- `GITLAB_PROJECT_ID`: Your GitLab project ID (required)
- `GITLAB_ACCESS_TOKEN`: Your GitLab Personal Access Token (required)
- `GITLAB_URL`: GitLab instance URL (optional, defaults to https://gitlab.com)
- `SERVER_NAME`: MCP server name (optional, defaults to gitlab-mcp-server)
- `SERVER_VERSION`: MCP server version (optional, defaults to 1.0.0)

### 3. GitLab Access Token Setup

1. Go to your GitLab instance → Settings → Access Tokens
2. Create a new token with the following scopes:
   - `api` - Access the authenticated user's API
   - `read_api` - Read access to the API
   - `read_repository` - Read access to repository
3. Copy the token and add it to your `.env` file

### 4. Find Your Project ID

You can find your GitLab project ID in:

- Project Settings → General → Project ID
- Or in the URL: `https://gitlab.com/username/project` (it's the numeric ID)

## Usage

### Local Development

Run the server locally:

```bash
chmod +x run-mcp.sh
./run-mcp.sh
```

Or run directly with Python:

```bash
source .venv/bin/activate
python main.py
```

### Integration with Cursor

To use this MCP server with Cursor, you need to configure it in your MCP settings.

#### MCP Configuration JSON

**Recommended: Using the Shell Script**

Add the following configuration to your MCP client settings (usually in `~/.cursor/mcp_settings.json` or similar):

```json
{
  "mcpServers": {
    "gitlab-mcp": {
      "command": "/path/to/gitlab-mcp-server/run-mcp.sh",
      "cwd": "/path/to/gitlab-mcp-server"
    }
  }
}
```

**Important Notes:**

- Replace `/path/to/gitlab-mcp-server` with the actual path to your project
- Make sure the shell script is executable: `chmod +x run-mcp.sh`
- The shell script handles virtual environment activation automatically

#### Alternative: Direct Python Execution

If you need to run Python directly (not recommended due to venv requirements):

```json
{
  "mcpServers": {
    "gitlab-mcp": {
      "command": "python",
      "args": ["/path/to/gitlab-mcp-server/main.py"],
      "cwd": "/path/to/gitlab-mcp-server",
      "env": {
        "GITLAB_PROJECT_ID": "your-project-id",
        "GITLAB_ACCESS_TOKEN": "your-access-token",
        "GITLAB_URL": "https://gitlab.com"
      }
    }
  }
}
```

**Note:** This approach requires that you manually ensure the correct Python environment is available in your PATH.

### Cursor Setup Steps

1. **Install Cursor**: Download and install Cursor from the official website
2. **Configure MCP**: Add the configuration above to your MCP settings
3. **Restart Cursor**: Restart Cursor to load the new MCP server
4. **Verify Connection**: Check that the GitLab MCP server is listed in your available tools

## Available Tools

### 1. `list_merge_requests`

List merge requests for the GitLab project.

**Parameters:**

- `state` (optional): Filter by state (`opened`, `closed`, `merged`, `all`) - default: `opened`
- `target_branch` (optional): Filter by target branch
- `limit` (optional): Maximum number of results (1-100) - default: 10

### 2. `get_merge_request_details`

Get detailed information about a specific merge request.

**Parameters:**

- `merge_request_iid` (required): Internal ID of the merge request

### 3. `get_merge_request_reviews`

Get reviews and discussions for a specific merge request.

**Parameters:**

- `merge_request_iid` (required): Internal ID of the merge request

### 4. `get_branch_merge_requests`

Find merge requests for a specific branch.

**Parameters:**

- `branch_name` (required): Name of the branch

## Example Usage in Cursor

Once configured, you can use commands like:

```
"List open merge requests"
"Get details for merge request 123"
"Show reviews for MR 456"
"Find merge requests for feature/new-login branch"
```

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify your GitLab access token has the correct permissions
2. **Project Not Found**: Check your project ID is correct
3. **Connection Issues**: Ensure your GitLab URL is accessible
4. **Python Path Issues**: Make sure the Python path in MCP config points to your virtual environment

### Logging

Logs are written to `/tmp/gitlab-mcp-server.log` when using the shell script, or to stdout when running directly.

To enable debug logging, modify `logging_config.py` to set the log level to `DEBUG`.

### Testing

Run the test suite:

```bash
python test_tools.py
```

## Development

### Project Structure

```
gitlab-mcp-server/
├── main.py              # Main MCP server entry point
├── config.py            # Configuration management
├── gitlab_api.py        # GitLab API client
├── logging_config.py    # Logging configuration
├── requirements.txt     # Python dependencies
├── run-mcp.sh          # Shell script to run the server
├── test_tools.py       # Test suite
├── .env.example        # Example environment configuration
└── tools/              # Individual tool implementations
    ├── list_merge_requests.py
    ├── get_merge_request_details.py
    ├── get_merge_request_reviews.py
    └── get_branch_merge_requests.py
```

### Adding New Tools

1. Create a new file in the `tools/` directory
2. Implement the tool function following the existing pattern
3. Add the tool to the `list_tools()` function in `main.py`
4. Add the tool handler to the `call_tool()` function in `main.py`

## Security Considerations

- Never commit your `.env` file or expose your access token
- Use environment variables for sensitive configuration
- Regularly rotate your GitLab access tokens
- Consider using project-specific access tokens with minimal required permissions

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the GitLab API documentation
3. Open an issue in the project repository
