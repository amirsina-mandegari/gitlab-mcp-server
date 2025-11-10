#!/bin/bash
# Get the script directory (where the MCP server is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the current working directory (where the script is being run from)
CURRENT_DIR="$(pwd)"

# Check if gitlab-mcp.env exists in the current working directory and load it
if [ -f "$CURRENT_DIR/gitlab-mcp.env" ]; then
    echo "Loading environment variables from $CURRENT_DIR/gitlab-mcp.env"
    set -a
    source "$CURRENT_DIR/gitlab-mcp.env"
    set +a
else
    echo "No gitlab-mcp.env found in $CURRENT_DIR, using existing environment variables"
fi

# Activate the virtual environment and run the MCP server
source "$SCRIPT_DIR/.venv/bin/activate"
python "$SCRIPT_DIR/main.py" 2>&1 | tee /tmp/gitlab-mcp-server.log
