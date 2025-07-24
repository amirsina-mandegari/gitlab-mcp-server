#!/usr/bin/env python3
"""Test script to verify GitLab MCP tools return proper CallToolResult objects."""

import asyncio
import sys
from tools.list_merge_requests import list_merge_requests
from tools.get_merge_request_details import get_merge_request_details
from tools.get_merge_request_reviews import get_merge_request_reviews
from mcp.types import CallToolResult

from decouple import config

GITLAB_URL = config('GITLAB_URL', default='https://git.partnerz.io')
PROJECT_ID = config('GITLAB_PROJECT_ID', default='237')
ACCESS_TOKEN = config('GITLAB_ACCESS_TOKEN', default='')


async def test_list_merge_requests():
    """Test list_merge_requests tool."""
    print("Testing list_merge_requests...")
    args = {"state": "opened", "limit": 2}
    result = await list_merge_requests(GITLAB_URL, PROJECT_ID, ACCESS_TOKEN, args)
    print(f"Result type: {type(result)}")
    print(f"Is CallToolResult: {isinstance(result, CallToolResult)}")
    if isinstance(result, CallToolResult):
        print(f"isError: {result.isError}")
        print(f"Content type: {type(result.content)}")
        if result.content:
            print(f"First content item: {result.content[0].text[:100]}...")
    print("=" * 50)


async def test_get_merge_request_details():
    """Test get_merge_request_details tool."""
    print("Testing get_merge_request_details...")
    args = {"merge_request_iid": 1047}
    result = await get_merge_request_details(
        GITLAB_URL, PROJECT_ID, ACCESS_TOKEN, args
    )
    print(f"Result type: {type(result)}")
    print(f"Is CallToolResult: {isinstance(result, CallToolResult)}")
    if isinstance(result, CallToolResult):
        print(f"isError: {result.isError}")
        print(f"Content type: {type(result.content)}")
        if result.content:
            print(f"First content item: {result.content[0].text[:100]}...")
    print("=" * 50)


async def test_get_merge_request_reviews():
    """Test get_merge_request_reviews tool."""
    print("Testing get_merge_request_reviews...")
    args = {"merge_request_iid": 1047}
    result = await get_merge_request_reviews(
        GITLAB_URL, PROJECT_ID, ACCESS_TOKEN, args
    )
    print(f"Result type: {type(result)}")
    print(f"Is CallToolResult: {isinstance(result, CallToolResult)}")
    if isinstance(result, CallToolResult):
        print(f"isError: {result.isError}")
        print(f"Content type: {type(result.content)}")
        if result.content:
            print(f"Full content: {result.content[0].text}")
    print("=" * 50)


async def main():
    """Run all tests."""
    if not ACCESS_TOKEN:
        print("Error: GITLAB_ACCESS_TOKEN not set")
        sys.exit(1)
    
    await test_list_merge_requests()
    await test_get_merge_request_details()
    await test_get_merge_request_reviews()


if __name__ == "__main__":
    asyncio.run(main()) 