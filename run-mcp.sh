#!/bin/bash
# Activate the virtual environment and run the MCP server
source /Users/asm/personal_code/gitlab-mcp-server/.venv/bin/activate
python /Users/asm/personal_code/gitlab-mcp-server/main.py 2>&1 | tee /tmp/gitlab-mcp-server.log 