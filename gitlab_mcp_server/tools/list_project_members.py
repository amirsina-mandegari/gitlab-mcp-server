import logging

from mcp.types import TextContent

from gitlab_mcp_server.gitlab_api import get_project_members as api_get_project_members

ACCESS_LEVEL_MAP = {
    10: "Guest",
    20: "Reporter",
    30: "Developer",
    40: "Maintainer",
    50: "Owner",
}


async def list_project_members(gitlab_url, project_id, access_token, args):
    """List all project members with their access levels"""
    logging.info(f"list_project_members called with args: {args}")

    status, data, error = await api_get_project_members(gitlab_url, project_id, access_token)

    if status != 200:
        logging.error(f"Error fetching project members: {status} - {error}")
        raise Exception(f"Error fetching project members: {status} - {error}")

    result = "# 👥 Project Members\n"
    result += f"*Found {len(data)} member{'s' if len(data) != 1 else ''}*\n\n"

    if not data:
        result += "📭 No members found.\n"
        return [TextContent(type="text", text=result)]

    # Group by access level
    by_access = {}
    for member in data:
        level = member.get("access_level", 0)
        level_name = ACCESS_LEVEL_MAP.get(level, f"Unknown ({level})")
        if level_name not in by_access:
            by_access[level_name] = []
        by_access[level_name].append(member)

    # Sort by access level (highest first)
    level_order = ["Owner", "Maintainer", "Developer", "Reporter", "Guest"]

    for level_name in level_order:
        if level_name not in by_access:
            continue

        members = by_access[level_name]
        result += f"## {level_name}s ({len(members)})\n\n"

        for member in sorted(members, key=lambda m: m.get("username", "")):
            username = member.get("username", "unknown")
            name = member.get("name", "Unknown")
            user_id = member.get("id", "?")
            state = member.get("state", "active")

            state_icon = "✅" if state == "active" else "⏸️"
            result += f"- {state_icon} **@{username}** ({name}) — ID: `{user_id}`\n"

        result += "\n"

    # Add any unknown access levels
    for level_name, members in by_access.items():
        if level_name in level_order:
            continue
        result += f"## {level_name} ({len(members)})\n\n"
        for member in members:
            username = member.get("username", "unknown")
            name = member.get("name", "Unknown")
            user_id = member.get("id", "?")
            result += f"- **@{username}** ({name}) — ID: `{user_id}`\n"
        result += "\n"

    result += "---\n"
    result += "💡 **Tip**: Use usernames (e.g., `@john.doe`) when creating merge requests.\n"

    return [TextContent(type="text", text=result)]
