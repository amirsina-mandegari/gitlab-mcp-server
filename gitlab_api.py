import aiohttp


def _headers(access_token):
    return {"Private-Token": access_token, "Content-Type": "application/json"}


async def get_merge_requests(gitlab_url, project_id, access_token, params):
    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            return (response.status, await response.json(), await response.text())


async def get_merge_request_pipeline(gitlab_url, project_id, access_token, mr_iid):
    """Get the latest pipeline for a merge request"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/" f"merge_requests/{mr_iid}/pipelines"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        params = {"per_page": 1}
        async with session.get(url, headers=headers, params=params) as response:
            data = await response.json()
            return (response.status, data[0] if data else None, await response.text())


async def get_pipeline_jobs(gitlab_url, project_id, access_token, pipeline_id):
    """Get all jobs for a specific pipeline"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/" f"pipelines/{pipeline_id}/jobs"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        params = {"per_page": 100}
        async with session.get(url, headers=headers, params=params) as response:
            return (response.status, await response.json(), await response.text())


async def get_job_trace(gitlab_url, project_id, access_token, job_id):
    """Get the trace/log output for a specific job"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/" f"jobs/{job_id}/trace"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return (response.status, await response.text(), response.status)


async def get_pipeline_test_report(gitlab_url, project_id, access_token, pipeline_id):
    """Get test report for a specific pipeline"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/" f"pipelines/{pipeline_id}/test_report"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return (response.status, await response.json(), await response.text())


async def get_pipeline_test_report_summary(gitlab_url, project_id, access_token, pipeline_id):
    """Get test report summary for a specific pipeline"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/" f"pipelines/{pipeline_id}/test_report_summary"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return (response.status, await response.json(), await response.text())


async def get_merge_request_changes(gitlab_url, project_id, access_token, mr_iid):
    """Get changes/diff stats for a merge request"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/" f"merge_requests/{mr_iid}/changes"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return (response.status, await response.json(), await response.text())


async def get_project_info(gitlab_url, project_id, access_token):
    """Get project information to check for merge conflicts"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return (response.status, await response.json(), await response.text())


async def get_merge_request_reviews(gitlab_url, project_id, access_token, mr_iid):
    discussions_result = await get_merge_request_discussions_paginated(gitlab_url, project_id, access_token, mr_iid)
    discussions_status, discussions, discussions_text = discussions_result

    approvals_url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/approvals"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(approvals_url, headers=headers) as approvals_response:
            if approvals_response.status == 200:
                approvals = await approvals_response.json()
            else:
                approvals = None
            approvals_status = approvals_response.status
            approvals_text = await approvals_response.text()

    return {
        "discussions": (discussions_status, discussions, discussions_text),
        "approvals": (approvals_status, approvals, approvals_text),
    }


async def get_merge_request_details(gitlab_url, project_id, access_token, mr_iid):
    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return (response.status, await response.json(), await response.text())


async def create_merge_request_discussion(gitlab_url, project_id, access_token, mr_iid, body):
    """Create a new discussion/comment on a merge request"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/" f"{mr_iid}/discussions"
    headers = _headers(access_token)
    data = {"body": body}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            json_data = await response.json() if response.content_type == "application/json" else {}
            return (response.status, json_data, await response.text())


async def reply_to_merge_request_discussion(gitlab_url, project_id, access_token, mr_iid, discussion_id, body):
    """Reply to an existing discussion on a merge request"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/" f"{mr_iid}/discussions/{discussion_id}/notes"
    headers = _headers(access_token)
    data = {"body": body}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            json_data = await response.json() if response.content_type == "application/json" else {}
            return (response.status, json_data, await response.text())


async def resolve_merge_request_discussion(gitlab_url, project_id, access_token, mr_iid, discussion_id, resolved):
    """Resolve or unresolve a discussion on a merge request"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/" f"{mr_iid}/discussions/{discussion_id}"
    headers = _headers(access_token)
    data = {"resolved": resolved}

    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, json=data) as response:
            json_data = await response.json() if response.content_type == "application/json" else {}
            return (response.status, json_data, await response.text())


async def get_branch_merge_requests(gitlab_url, project_id, access_token, branch_name):
    """Get merge requests for a specific branch"""
    params = {"source_branch": branch_name, "state": "all", "per_page": 100}

    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests"
    headers = _headers(access_token)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            return (response.status, await response.json(), await response.text())


async def get_merge_request_commits(gitlab_url, project_id, access_token, mr_iid):
    """Get all commits in a merge request (handles pagination)"""
    base_url = f"{gitlab_url}/api/v4/projects/{project_id}/" f"merge_requests/{mr_iid}/commits"
    headers = _headers(access_token)
    all_commits = []
    page = 1
    per_page = 100  # Maximum allowed per page

    async with aiohttp.ClientSession() as session:
        while True:
            params = {"page": page, "per_page": per_page}
            async with session.get(base_url, headers=headers, params=params) as response:
                if response.status != 200:
                    return (response.status, await response.json(), await response.text())

                page_data = await response.json()
                if not page_data:  # No more results
                    break

                all_commits.extend(page_data)

                # If we got fewer results than per_page, we're done
                if len(page_data) < per_page:
                    break

                page += 1

        return (200, all_commits, "Success")


async def get_commit_comments(gitlab_url, project_id, access_token, commit_sha):
    """Get simple comments for a specific commit"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/" f"repository/commits/{commit_sha}/comments"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return (response.status, await response.json(), await response.text())


async def get_commit_discussions(gitlab_url, project_id, access_token, commit_sha):
    """Get discussions/comments for a specific commit"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/" f"repository/commits/{commit_sha}/discussions"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return (response.status, await response.json(), await response.text())


async def get_commit_all_comments_and_discussions(gitlab_url, project_id, access_token, commit_sha):
    """Get both comments and discussions for a commit, combining them"""
    discussions_result = await get_commit_discussions(gitlab_url, project_id, access_token, commit_sha)
    discussions_status, discussions_data, discussions_error = discussions_result

    comments_result = await get_commit_comments(gitlab_url, project_id, access_token, commit_sha)
    comments_status, comments_data, comments_error = comments_result

    combined_data = []

    if discussions_status == 200 and discussions_data:
        combined_data.extend(discussions_data)

    if comments_status == 200 and comments_data:
        for comment in comments_data:
            discussion_format = {
                "id": f"comment_{comment.get('id', 'unknown')}",
                "individual_note": True,
                "notes": [
                    {
                        "id": comment.get("id"),
                        "body": comment.get("note", ""),
                        "author": comment.get("author", {}),
                        "created_at": comment.get("created_at"),
                        "updated_at": comment.get("created_at"),
                        "system": False,
                        "noteable_type": "Commit",
                        "noteable_id": commit_sha,
                        "resolvable": False,
                        "position": (
                            {
                                "new_path": comment.get("path"),
                                "new_line": comment.get("line"),
                                "line_type": comment.get("line_type"),
                            }
                            if comment.get("path")
                            else None
                        ),
                    }
                ],
            }
        combined_data.append(discussion_format)

    if combined_data:
        return (200, combined_data, "Success")
    elif discussions_status == 200 or comments_status == 200:
        return (200, [], "No comments or discussions found")
    else:
        return discussions_result


async def get_merge_request_discussions_paginated(gitlab_url, project_id, access_token, mr_iid):
    """Get all discussions from a merge request with pagination"""
    all_discussions = []
    page = 1
    per_page = 100  # Maximum allowed per page

    async with aiohttp.ClientSession() as session:
        headers = _headers(access_token)

        while True:
            url = f"{gitlab_url}/api/v4/projects/{project_id}/" f"merge_requests/{mr_iid}/discussions"
            params = {"page": page, "per_page": per_page}

            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    return (response.status, await response.json(), await response.text())

                discussions = await response.json()
                if not discussions:  # No more results
                    break

                all_discussions.extend(discussions)

                link_header = response.headers.get("Link", "")
                if 'rel="next"' not in link_header:
                    break

                page += 1

        return (200, all_discussions, "Success")


async def get_project_members(gitlab_url, project_id, access_token):
    """Get all project members including inherited from groups"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/members/all"
    headers = _headers(access_token)
    all_members = []
    page = 1
    per_page = 100

    async with aiohttp.ClientSession() as session:
        while True:
            params = {"page": page, "per_page": per_page}
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    return (response.status, await response.json(), await response.text())

                members = await response.json()
                if not members:
                    break

                all_members.extend(members)

                if len(members) < per_page:
                    break

                page += 1

        return (200, all_members, "Success")


async def get_project_labels(gitlab_url, project_id, access_token):
    """Get all project labels including inherited from groups"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/labels"
    headers = _headers(access_token)
    all_labels = []
    page = 1
    per_page = 100

    async with aiohttp.ClientSession() as session:
        while True:
            params = {"page": page, "per_page": per_page, "include_ancestor_groups": "true"}
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    return (response.status, await response.json(), await response.text())

                labels = await response.json()
                if not labels:
                    break

                all_labels.extend(labels)

                if len(labels) < per_page:
                    break

                page += 1

        return (200, all_labels, "Success")


async def create_merge_request(gitlab_url, project_id, access_token, data):
    """Create a new merge request"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests"
    headers = _headers(access_token)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            json_data = await response.json() if response.content_type == "application/json" else {}
            return (response.status, json_data, await response.text())


async def update_merge_request(gitlab_url, project_id, access_token, mr_iid, data):
    """Update an existing merge request"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
    headers = _headers(access_token)

    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, json=data) as response:
            json_data = await response.json() if response.content_type == "application/json" else {}
            return (response.status, json_data, await response.text())


async def create_project_label(gitlab_url, project_id, access_token, name, color=None, description=None):
    """Create a new project label"""
    url = f"{gitlab_url}/api/v4/projects/{project_id}/labels"
    headers = _headers(access_token)

    data = {"name": name}
    if color:
        data["color"] = color
    else:
        # Default to a random nice color
        data["color"] = "#428BCA"  # Nice blue
    if description:
        data["description"] = description

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            json_data = await response.json() if response.content_type == "application/json" else {}
            return (response.status, json_data, await response.text())
