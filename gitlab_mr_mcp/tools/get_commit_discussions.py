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
            logging.error(f"Error fetching merge request commits: " f"{commits_status} - {commits_error}")
            raise Exception(f"Error fetching merge request commits: {commits_error}")

        if not commits_data:
            return [TextContent(type="text", text="No commits found in this merge request.")]

        logging.info(f"Getting ALL MR discussions for MR #{mr_iid}...")
        discussions_result = await get_merge_request_discussions_paginated(gitlab_url, project_id, access_token, mr_iid)
        discussions_status, discussions_data, discussions_error = discussions_result

        if discussions_status != 200:
            logging.error(f"Error fetching MR discussions: " f"{discussions_status} - {discussions_error}")
            discussions_data = []

        commit_map = {commit["id"]: commit for commit in commits_data}

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

        if not commits_with_discussions:
            summary_text = (
                f"## Commit Discussions for MR #{mr_iid}\n\n"
                f"**Summary:**\n"
                f"- Total commits: {len(commits_data)}\n"
                f"- Commits with discussions: 0\n"
                f"- Total discussions: 0\n\n"
                f"No line-level discussions found on any commits in this "
                f"merge request. Found {len(discussions_data)} total MR discussions."
            )
            return [TextContent(type="text", text=summary_text)]

        response_text = (
            f"## Commit Discussions for MR #{mr_iid}\n\n"
            f"**Summary:**\n"
            f"- Total commits: {len(commits_data)}\n"
            f"- Commits with discussions: {len(commits_with_discussions)}\n"
            f"- Total line-level discussions: {total_discussions}\n"
            f"- Total MR discussions: {len(discussions_data)}\n\n"
        )

        for _commit_sha, item in commits_with_discussions.items():
            commit = item["commit"]
            discussions = item["discussions"]

            response_text += f"### 📝 Commit: {commit['short_id']}\n"
            response_text += f"**Title:** {commit['title']}\n"
            response_text += f"**Author:** {commit['author_name']}\n"
            response_text += f"**Date:** {format_date(commit['committed_date'])}\n"
            response_text += f"**SHA:** `{commit['id']}`\n\n"

            for discussion_item in discussions:
                discussion_id = discussion_item["discussion_id"]
                note = discussion_item["note"]
                position = discussion_item["position"]

                author_name = note["author"]["name"]
                response_text += f"**💬 Comment by {author_name}:**\n"
                response_text += f"{note['body']}\n"

                if position.get("new_path"):
                    line_info = position.get("new_line", "N/A")
                    response_text += f"*On file: {position['new_path']} " f"(line {line_info})*\n"

                created_at = format_date(note["created_at"])
                response_text += f"*Posted: {created_at}*\n"
                response_text += f"*Discussion ID: {discussion_id}*\n\n"

            response_text += "---\n\n"

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        logging.error(f"Error in get_commit_discussions: {str(e)}")
        return [TextContent(type="text", text=f"Error retrieving commit discussions: {str(e)}")]
