import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_project_labels as api_get_project_labels


async def list_project_labels(gitlab_url, project_id, access_token, args):
    """List all project labels"""
    logging.info(f"list_project_labels called with args: {args}")

    status, data, error = await api_get_project_labels(gitlab_url, project_id, access_token)

    if status != 200:
        logging.error(f"Error fetching project labels: {status} - {error}")
        raise Exception(f"Error fetching project labels: {status} - {error}")

    result = "# Project Labels\n\n"
    result += f"Found {len(data)} label(s)\n\n"

    if not data:
        result += "No labels found.\n"
        return [TextContent(type="text", text=result)]

    # Separate scoped vs regular labels
    scoped_labels = []
    regular_labels = []

    for label in data:
        name = label.get("name", "")
        if "::" in name:
            scoped_labels.append(label)
        else:
            regular_labels.append(label)

    if regular_labels:
        result += "## Regular Labels\n\n"
        for label in sorted(regular_labels, key=lambda x: x.get("name", "").lower()):
            name = label.get("name", "unknown")
            description = label.get("description", "")
            is_project = label.get("is_project_label", True)
            source = "project" if is_project else "group"

            result += f"- `{name}`"
            if description:
                result += f" - {description}"
            result += f" ({source})\n"
        result += "\n"

    if scoped_labels:
        result += "## Scoped Labels\n\n"

        # Group by scope
        scopes = {}
        for label in scoped_labels:
            name = label.get("name", "")
            scope = name.split("::")[0]
            if scope not in scopes:
                scopes[scope] = []
            scopes[scope].append(label)

        for scope in sorted(scopes.keys()):
            result += f"### {scope}\n\n"
            for label in sorted(scopes[scope], key=lambda x: x.get("name", "")):
                name = label.get("name", "unknown")
                description = label.get("description", "")

                result += f"- `{name}`"
                if description:
                    result += f" - {description}"
                result += "\n"
            result += "\n"

    result += "---\n\n"
    result += "Use exact label names when creating merge requests.\n"

    return [TextContent(type="text", text=result)]
