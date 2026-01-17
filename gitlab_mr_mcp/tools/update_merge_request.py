import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_merge_request_details, get_project_labels, get_project_members
from gitlab_mr_mcp.gitlab_api import update_merge_request as api_update_merge_request


def apply_draft_to_title(title, draft):
    """Apply or remove Draft: prefix based on draft flag."""
    clean_title = title
    for prefix in ["Draft: ", "Draft:", "WIP: ", "WIP:", "draft: ", "draft:", "wip: ", "wip:"]:
        if clean_title.startswith(prefix):
            clean_title = clean_title[len(prefix) :].lstrip()
            break

    if draft:
        return f"Draft: {clean_title}"
    return clean_title


async def resolve_labels(gitlab_url, project_id, access_token, requested_labels):
    """Resolve label names case-insensitively against existing project labels."""
    if not requested_labels:
        return []

    status, labels, error = await get_project_labels(gitlab_url, project_id, access_token)

    if status != 200:
        raise Exception(f"Failed to fetch project labels: {error}")

    label_lookup = {label["name"].lower(): label["name"] for label in labels}

    resolved = []
    not_found = []

    for req_label in requested_labels:
        key = req_label.lower()
        if key in label_lookup:
            resolved.append(label_lookup[key])
        else:
            not_found.append(req_label)

    if not_found:
        available = ", ".join(sorted(label_lookup.values())[:20])
        raise ValueError(f"Labels not found: {', '.join(not_found)}. Available (first 20): {available}")

    return resolved


async def resolve_usernames_to_ids(gitlab_url, project_id, access_token, usernames):
    """Resolve usernames to user IDs"""
    if not usernames:
        return []

    status, members, error = await get_project_members(gitlab_url, project_id, access_token)

    if status != 200:
        raise Exception(f"Failed to fetch project members: {error}")

    username_to_id = {m["username"].lower(): m["id"] for m in members}

    resolved_ids = []
    not_found = []

    for username in usernames:
        clean_username = username.lstrip("@").lower()
        if clean_username in username_to_id:
            resolved_ids.append(username_to_id[clean_username])
        else:
            not_found.append(username)

    if not_found:
        raise ValueError(f"Users not found in project: {', '.join(not_found)}")

    return resolved_ids


async def update_merge_request(gitlab_url, project_id, access_token, args):
    """Update an existing merge request"""
    logging.info(f"update_merge_request called with args: {args}")

    mr_iid = args.get("merge_request_iid")
    if not mr_iid:
        raise ValueError("merge_request_iid is required")

    mr_data = {}

    # Handle draft status via title prefix
    if args.get("draft") is not None:
        if args.get("title"):
            mr_data["title"] = apply_draft_to_title(args["title"], args["draft"])
        else:
            status, mr_details, error = await get_merge_request_details(gitlab_url, project_id, access_token, mr_iid)
            if status != 200:
                raise Exception(f"Failed to fetch MR details: {error}")
            current_title = mr_details.get("title", "")
            mr_data["title"] = apply_draft_to_title(current_title, args["draft"])
    elif args.get("title"):
        mr_data["title"] = args["title"]

    if args.get("description") is not None:
        mr_data["description"] = args["description"]

    if args.get("target_branch"):
        mr_data["target_branch"] = args["target_branch"]

    if args.get("squash") is not None:
        mr_data["squash"] = args["squash"]

    if args.get("remove_source_branch") is not None:
        mr_data["remove_source_branch"] = args["remove_source_branch"]

    # Resolve labels
    if args.get("labels") is not None:
        if args["labels"]:
            resolved_labels = await resolve_labels(gitlab_url, project_id, access_token, args["labels"])
            mr_data["labels"] = ",".join(resolved_labels)
        else:
            mr_data["labels"] = ""

    # Resolve assignees
    if args.get("assignees") is not None:
        if args["assignees"]:
            assignee_ids = await resolve_usernames_to_ids(gitlab_url, project_id, access_token, args["assignees"])
            mr_data["assignee_ids"] = assignee_ids
        else:
            mr_data["assignee_ids"] = []

    # Resolve reviewers
    if args.get("reviewers") is not None:
        if args["reviewers"]:
            reviewer_ids = await resolve_usernames_to_ids(gitlab_url, project_id, access_token, args["reviewers"])
            mr_data["reviewer_ids"] = reviewer_ids
        else:
            mr_data["reviewer_ids"] = []

    if not mr_data:
        raise ValueError("No fields to update. Provide at least one field to change.")

    status, data, error = await api_update_merge_request(gitlab_url, project_id, access_token, mr_iid, mr_data)

    if status == 200:
        mr_title = data.get("title")
        mr_url = data.get("web_url")

        result = f"# MR !{mr_iid} Updated\n\n"
        result += f"**Title**: {mr_title}\n"

        if data.get("draft"):
            result += "**Status**: Draft\n"
        else:
            result += "**Status**: Ready\n"

        if data.get("assignees"):
            assignees = ", ".join(f"@{a['username']}" for a in data["assignees"])
            result += f"**Assignees**: {assignees}\n"

        if data.get("reviewers"):
            reviewers = ", ".join(f"@{r['username']}" for r in data["reviewers"])
            result += f"**Reviewers**: {reviewers}\n"

        if data.get("labels"):
            labels = ", ".join(f"`{label}`" for label in data["labels"])
            result += f"**Labels**: {labels}\n"

        result += f"\n**URL**: {mr_url}\n"

        return [TextContent(type="text", text=result)]

    else:
        error_msg = data.get("message", error) if isinstance(data, dict) else error
        logging.error(f"Error updating merge request: {status} - {error_msg}")
        raise Exception(f"Error updating merge request: {status} - {error_msg}")
