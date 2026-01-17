import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_job_trace


async def get_job_log(gitlab_url, project_id, access_token, args):
    """Get the trace/log output for a specific pipeline job"""
    logging.info(f"get_job_log called with args: {args}")
    job_id = args["job_id"]

    try:
        status, log_data, error = await get_job_trace(gitlab_url, project_id, access_token, job_id)
    except Exception as e:
        logging.error(f"Error fetching job log: {e}")
        raise Exception(f"Error fetching job log: {e}")

    if status != 200:
        logging.error(f"Error fetching job log: {status} - {error}")
        raise Exception(f"Error fetching job log: {status} - {error}")

    if not log_data or len(log_data.strip()) == 0:
        result = f"# Job Log (ID: {job_id})\n\n"
        result += "No log output available.\n\n"
        result += "Possible reasons:\n"
        result += "- Job hasn't started yet\n"
        result += "- Job was skipped\n"
        result += "- Log has been archived or deleted\n"
        return [TextContent(type="text", text=result)]

    # Format output
    result = f"# Job Log (ID: {job_id})\n\n"

    log_size_kb = len(log_data) / 1024
    line_count = log_data.count(chr(10)) + 1
    result += f"**Size**: {log_size_kb:.1f} KB | **Lines**: {line_count}\n\n"

    # Truncate if needed
    max_chars = 15000
    if len(log_data) > max_chars:
        result += "## Output (last 15,000 characters)\n\n"
        result += "```\n"
        result += log_data[-max_chars:]
        result += "\n```\n\n"
        result += f"*Truncated from {len(log_data):,} characters*\n"
    else:
        result += "## Output\n\n"
        result += "```\n"
        result += log_data
        result += "\n```\n"

    return [TextContent(type="text", text=result)]
