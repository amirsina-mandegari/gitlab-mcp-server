import aiohttp


def _headers(access_token):
    return {"Private-Token": access_token, "Content-Type": "application/json"}


async def get_merge_requests(gitlab_url, project_id, access_token, params):
    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            return (
                response.status,
                await response.json(),
                await response.text()
            )


async def get_merge_request_reviews(
    gitlab_url, project_id, access_token, mr_iid
):
    discussions_url = (
        f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/discussions"
    )
    approvals_url = (
        f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/approvals"
    )
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(discussions_url, headers=headers) as discussions_response:
            if discussions_response.status == 200:
                discussions = await discussions_response.json()
            else:
                discussions = None
            discussions_status = discussions_response.status
            discussions_text = await discussions_response.text()
        async with session.get(approvals_url, headers=headers) as approvals_response:
            if approvals_response.status == 200:
                approvals = await approvals_response.json()
            else:
                approvals = None
            approvals_status = approvals_response.status
            approvals_text = await approvals_response.text()
    return {
        "discussions": (
            discussions_status, discussions, discussions_text
        ),
        "approvals": (
            approvals_status, approvals, approvals_text
        ),
    }


async def get_merge_request_details(
    gitlab_url, project_id, access_token, mr_iid
):
    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return (
                response.status,
                await response.json(),
                await response.text()
            )


async def get_branch_merge_requests(
    gitlab_url, project_id, access_token, params
):
    url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests"
    headers = _headers(access_token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            return (
                response.status,
                await response.json(),
                await response.text()
            ) 