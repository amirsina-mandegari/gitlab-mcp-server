import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import search_projects as api_search_projects


async def search_projects(gitlab_url, access_token, args):
    logging.info(f"search_projects called with args: {args}")

    search = args.get("search")
    membership = args.get("membership", True)
    limit = args.get("limit", 20)

    status, data, error = await api_search_projects(gitlab_url, access_token, search, membership, limit)

    if status != 200:
        logging.error(f"Error searching projects: {status} - {error}")
        raise Exception(f"Error searching projects: {status} - {error}")

    search_info = f' matching "{search}"' if search else ""
    result = f"# GitLab Projects{search_info}\n\n"
    result += f"Found {len(data)} project(s)\n\n"

    if not data:
        result += "No projects found.\n"
        return [TextContent(type="text", text=result)]

    for project in data:
        result += f"## {project['name']}\n\n"
        result += f"**ID**: `{project['id']}`\n"
        result += f"**Path**: `{project['path_with_namespace']}`\n"

        if project.get("description"):
            desc = project["description"][:100]
            if len(project["description"]) > 100:
                desc += "..."
            result += f"**Description**: {desc}\n"

        result += f"**Visibility**: {project.get('visibility', 'unknown')}\n"
        result += f"**Default Branch**: `{project.get('default_branch', 'main')}`\n"
        result += f"**URL**: {project['web_url']}\n\n"

    result += "---\n\n"
    result += "**Tip**: Use the project `ID` or `path` in other tools.\n"
    result += "Example: `list_merge_requests` with `project_id: 12345`\n"

    return [TextContent(type="text", text=result)]
