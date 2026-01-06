#!/usr/bin/env python3
"""Entry point for running as `python -m gitlab_mr_mcp`."""

import asyncio

from gitlab_mr_mcp.server import main

if __name__ == "__main__":
    asyncio.run(main())
