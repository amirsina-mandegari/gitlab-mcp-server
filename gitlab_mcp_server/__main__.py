#!/usr/bin/env python3
"""Entry point for running as `python -m gitlab_mcp_server`."""

import asyncio

from gitlab_mcp_server.server import main

if __name__ == "__main__":
    asyncio.run(main())
