#!/bin/bash
# Activate the virtual environment and run the MCP server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
python "$SCRIPT_DIR/main.py" 2>&1 | tee /tmp/gitlab-mcp-server.log 