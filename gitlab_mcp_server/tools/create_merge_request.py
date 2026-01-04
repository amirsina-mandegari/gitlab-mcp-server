import logging

from mcp.types import TextContent

from gitlab_mcp_server.gitlab_api import create_merge_request as api_create_merge_request
from gitlab_mcp_server.gitlab_api import create_project_label, get_project_labels, get_project_members


async def resolve_labels(gitlab_url, project_id, access_token, requested_labels, create_missing=False):
    """Resolve label names case-insensitively against existing project labels.

    If create_missing=True, creates labels that don't exist.
    If create_missing=False, raises ValueError for missing labels.
    """
    if not requested_labels:
        return [], []

    status, labels, error = await get_project_labels(gitlab_url, project_id, access_token)

    if status != 200:
        raise Exception(f"Failed to fetch project labels: {error}")

    # Build case-insensitive lookup: lowercase -> actual name
    label_lookup = {label["name"].lower(): label["name"] for label in labels}

    resolved = []
    not_found = []
    created = []

    for req_label in requested_labels:
        key = req_label.lower()
        if key in label_lookup:
            resolved.append(label_lookup[key])
        else:
            not_found.append(req_label)

    if not_found:
        if create_missing:
            # Create the missing labels
            for label_name in not_found:
                status, data, error = await create_project_label(gitlab_url, project_id, access_token, label_name)
                if status == 201:
                    created.append(data.get("name", label_name))
                    resolved.append(data.get("name", label_name))
                elif status == 409:
                    # Label already exists (race condition), use as-is
                    resolved.append(label_name)
                else:
                    raise Exception(f"Failed to create label '{label_name}': {error}")
        else:
            available = ", ".join(sorted(label_lookup.values())[:20])
            raise ValueError(
                f"Labels not found: {', '.join(not_found)}. "
                f"Available labels (first 20): {available}. "
                f"Set create_missing_labels=true to create them."
            )

    return resolved, created


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
        # Strip @ prefix if present
        clean_username = username.lstrip("@").lower()
        if clean_username in username_to_id:
            resolved_ids.append(username_to_id[clean_username])
        else:
            not_found.append(username)

    if not_found:
        raise ValueError(f"Users not found in project: {', '.join(not_found)}")

    return resolved_ids


def apply_draft_to_title(title, draft):
    """Apply or remove Draft: prefix based on draft flag.

    GitLab's draft API param is unreliable across versions.
    The title prefix is the guaranteed method.
    """
    # Remove existing draft/wip prefixes first (case-insensitive)
    clean_title = title
    for prefix in ["Draft: ", "Draft:", "WIP: ", "WIP:", "draft: ", "draft:", "wip: ", "wip:"]:
        if clean_title.startswith(prefix):
            clean_title = clean_title[len(prefix) :].lstrip()
            break

    if draft:
        return f"Draft: {clean_title}"
    return clean_title


async def create_merge_request(gitlab_url, project_id, access_token, args):
    """Create a new merge request"""
    logging.info(f"create_merge_request called with args: {args}")

    source_branch = args.get("source_branch")
    target_branch = args.get("target_branch")
    title = args.get("title")

    if not source_branch:
        raise ValueError("source_branch is required")
    if not target_branch:
        raise ValueError("target_branch is required")
    if not title:
        raise ValueError("title is required")

    # Handle draft status via title prefix (more reliable than API param)
    if args.get("draft", False):
        title = apply_draft_to_title(title, draft=True)

    # Build the MR data
    mr_data = {
        "source_branch": source_branch,
        "target_branch": target_branch,
        "title": title,
    }

    # Optional fields
    if args.get("description"):
        mr_data["description"] = args["description"]

    if args.get("squash") is not None:
        mr_data["squash"] = args["squash"]

    if args.get("remove_source_branch") is not None:
        mr_data["remove_source_branch"] = args["remove_source_branch"]

    # Resolve labels (case-insensitive validation)
    created_labels = []
    if args.get("labels"):
        resolved_labels, created_labels = await resolve_labels(
            gitlab_url,
            project_id,
            access_token,
            args["labels"],
            create_missing=args.get("create_missing_labels", False),
        )
        if resolved_labels:
            mr_data["labels"] = ",".join(resolved_labels)

    # Resolve assignees (usernames → IDs)
    if args.get("assignees"):
        assignee_ids = await resolve_usernames_to_ids(gitlab_url, project_id, access_token, args["assignees"])
        if assignee_ids:
            mr_data["assignee_ids"] = assignee_ids

    # Resolve reviewers (usernames → IDs)
    if args.get("reviewers"):
        reviewer_ids = await resolve_usernames_to_ids(gitlab_url, project_id, access_token, args["reviewers"])
        if reviewer_ids:
            mr_data["reviewer_ids"] = reviewer_ids

    status, data, error = await api_create_merge_request(gitlab_url, project_id, access_token, mr_data)

    if status == 201:
        mr_iid = data.get("iid")
        mr_url = data.get("web_url")
        mr_title = data.get("title")

        result = "# ✅ Merge Request Created\n\n"
        result += f"**!{mr_iid}**: {mr_title}\n\n"
        result += f"**Source**: `{source_branch}` → **Target**: `{target_branch}`\n\n"

        if data.get("draft"):
            result += "📝 **Status**: Draft\n"

        if data.get("assignees"):
            assignees = ", ".join(f"@{a['username']}" for a in data["assignees"])
            result += f"👤 **Assignees**: {assignees}\n"

        if data.get("reviewers"):
            reviewers = ", ".join(f"@{r['username']}" for r in data["reviewers"])
            result += f"👀 **Reviewers**: {reviewers}\n"

        if data.get("labels"):
            labels = ", ".join(f"`{label}`" for label in data["labels"])
            result += f"🏷️ **Labels**: {labels}\n"

        if created_labels:
            created = ", ".join(f"`{label}`" for label in created_labels)
            result += f"✨ **Created Labels**: {created}\n"

        result += f"\n🔗 [Open in GitLab]({mr_url})\n"

        return [TextContent(type="text", text=result)]
    elif status == 409:
        # MR already exists
        error_msg = data.get("message", error)
        result = "# ⚠️ Merge Request Already Exists\n\n"
        result += f"A merge request for `{source_branch}` → `{target_branch}` already exists.\n"
        result += f"\n**Error**: {error_msg}\n"
        return [TextContent(type="text", text=result)]

    else:
        error_msg = data.get("message", error) if isinstance(data, dict) else error
        logging.error(f"Error creating merge request: {status} - {error_msg}")
        raise Exception(f"Error creating merge request: {status} - {error_msg}")
