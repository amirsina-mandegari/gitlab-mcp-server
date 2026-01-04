import logging

from mcp.types import TextContent

from gitlab_mcp_server.gitlab_api import get_job_trace


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
        result = f"# 📋 Job Log (Job ID: {job_id})\n\n"
        result += "ℹ️ No log output available for this job.\n\n"
        result += "This could mean:\n"
        result += "• The job hasn't started yet\n"
        result += "• The job was skipped\n"
        result += "• The log has been archived or deleted\n"
        return [TextContent(type="text", text=result)]

    # Format the output
    result = f"# 📋 Job Log (Job ID: {job_id})\n\n"

    # Add log size info
    log_size_kb = len(log_data) / 1024
    result += f"**📊 Log Size**: {log_size_kb:.2f} KB\n"
    result += f"**📄 Lines**: {log_data.count(chr(10)) + 1}\n\n"

    # Check if we need to truncate
    max_chars = 15000  # Keep logs reasonable for context
    if len(log_data) > max_chars:
        result += "## 📝 Job Output (Last 15,000 characters)\n\n"
        result += "```\n"
        result += log_data[-max_chars:]
        result += "\n```\n\n"
        result += f"*⚠️ Note: Log truncated from {len(log_data):,} to "
        result += f"{max_chars:,} characters (showing last portion)*\n"
    else:
        result += "## 📝 Job Output\n\n"
        result += "```\n"
        result += log_data
        result += "\n```\n"

    return [TextContent(type="text", text=result)]
