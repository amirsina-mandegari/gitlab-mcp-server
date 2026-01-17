import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_merge_request_commits, get_merge_request_discussions_paginated
from gitlab_mr_mcp.utils import format_date


async def get_commit_discussions(gitlab_url, project_id, access_token, args):
    """Get discussions/comments on commits within a merge request"""
    logging.info(f"get_commit_discussions called with args: {args}")
    mr_iid = args["merge_request_iid"]

    try:
        commits_result = await get_merge_request_commits(gitlab_url, project_id, access_token, mr_iid)
        commits_status, commits_data, commits_error = commits_result

        if commits_status != 200:
            logging.error(f"Error fetching commits: {commits_status} - {commits_error}")
            raise Exception(f"Error fetching commits: {commits_error}")

        if not commits_data:
            return [TextContent(type="text", text="No commits found in this merge request.")]

        # Get all MR discussions
        discussions_result = await get_merge_request_discussions_paginated(gitlab_url, project_id, access_token, mr_iid)
        discussions_status, discussions_data, discussions_error = discussions_result

        if discussions_status != 200:
            logging.error(f"Error fetching discussions: {discussions_status} - {discussions_error}")
            discussions_data = []

        commit_map = {commit["id"]: commit for commit in commits_data}

        # Find discussions linked to commits
        commits_with_discussions = {}
        total_discussions = 0

        for discussion in discussions_data:
            notes = discussion.get("notes", [])
            for note in notes:
                position = note.get("position")
                if position and position.get("head_sha"):
                    commit_sha = position["head_sha"]
                    if commit_sha in commit_map:
                        if commit_sha not in commits_with_discussions:
                            commits_with_discussions[commit_sha] = {"commit": commit_map[commit_sha], "discussions": []}
                        commits_with_discussions[commit_sha]["discussions"].append(
                            {"discussion_id": discussion.get("id"), "note": note, "position": position}
                        )
                        total_discussions += 1

        # Format output
        result = f"# Commit Discussions for MR !{mr_iid}\n\n"
        result += "## Summary\n\n"
        result += f"- Total commits: {len(commits_data)}\n"
        result += f"- Commits with discussions: {len(commits_with_discussions)}\n"
        result += f"- Line-level discussions: {total_discussions}\n"
        result += f"- Total MR discussions: {len(discussions_data)}\n\n"

        if not commits_with_discussions:
            result += "No line-level discussions found on any commits.\n"
            return [TextContent(type="text", text=result)]

        # Show discussions by commit
        for _commit_sha, item in commits_with_discussions.items():
            commit = item["commit"]
            discussions = item["discussions"]

            result += f"## Commit: {commit['short_id']}\n\n"
            result += f"**Title**: {commit['title']}\n"
            result += f"**Author**: {commit['author_name']}\n"
            result += f"**Date**: {format_date(commit['committed_date'])}\n"
            result += f"**SHA**: `{commit['id']}`\n\n"

            for disc_item in discussions:
                discussion_id = disc_item["discussion_id"]
                note = disc_item["note"]
                position = disc_item["position"]

                author = note["author"]
                result += f"### Comment by {author['name']} (@{author['username']})\n\n"
                result += f"{note['body']}\n\n"

                if position.get("new_path"):
                    result += f"**File**: `{position['new_path']}`"
                    if position.get("new_line"):
                        result += f" line {position['new_line']}"
                    result += "\n"

                result += f"**Posted**: {format_date(note['created_at'])}\n"
                result += f"**Discussion ID**: `{discussion_id}`\n\n"

            result += "---\n\n"

        return [TextContent(type="text", text=result)]

    except Exception as e:
        logging.error(f"Error in get_commit_discussions: {str(e)}")
        return [TextContent(type="text", text=f"Error retrieving commit discussions: {str(e)}")]
