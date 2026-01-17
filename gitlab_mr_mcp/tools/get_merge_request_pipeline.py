import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_merge_request_pipeline as api_get_merge_request_pipeline
from gitlab_mr_mcp.gitlab_api import get_pipeline_jobs
from gitlab_mr_mcp.utils import format_date, get_pipeline_status_icon


def format_duration(seconds):
    """Format duration in human readable form"""
    if not seconds:
        return "N/A"
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


async def get_merge_request_pipeline(gitlab_url, project_id, access_token, args):
    """Get the last pipeline data for a merge request with all jobs"""
    logging.info(f"get_merge_request_pipeline called with args: {args}")
    mr_iid = args["merge_request_iid"]

    try:
        status, pipeline_data, error = await api_get_merge_request_pipeline(
            gitlab_url, project_id, access_token, mr_iid
        )
    except Exception as e:
        logging.error(f"Error fetching pipeline: {e}")
        raise Exception(f"Error fetching merge request pipeline: {e}")

    if status != 200:
        logging.error(f"Error fetching pipeline: {status} - {error}")
        raise Exception(f"Error fetching merge request pipeline: {status} - {error}")

    if not pipeline_data:
        result = f"# Pipeline for MR !{mr_iid}\n\n"
        result += "No pipeline found for this merge request.\n\n"
        result += "Possible reasons:\n"
        result += "- No CI/CD configured for this project\n"
        result += "- Pipeline hasn't been triggered yet\n"
        result += "- Branch has no commits\n"
        return [TextContent(type="text", text=result)]

    # Get jobs for the pipeline
    pipeline_id = pipeline_data.get("id")
    jobs_data = []
    if pipeline_id:
        try:
            jobs_status, jobs_data, jobs_error = await get_pipeline_jobs(
                gitlab_url, project_id, access_token, pipeline_id
            )
            if jobs_status != 200:
                logging.warning(f"Could not fetch jobs: {jobs_status} - {jobs_error}")
                jobs_data = []
        except Exception as e:
            logging.warning(f"Error fetching jobs: {e}")
            jobs_data = []

    # Format output
    pipeline_status = pipeline_data.get("status", "unknown")
    pipeline_icon = get_pipeline_status_icon(pipeline_status)

    result = f"# {pipeline_icon} Pipeline for MR !{mr_iid}\n\n"

    # Overview
    result += "## Overview\n\n"
    result += f"**Pipeline ID**: {pipeline_data.get('id', 'N/A')}\n"
    result += f"**Status**: {pipeline_icon} {pipeline_status}\n"
    result += f"**SHA**: `{pipeline_data.get('sha', 'N/A')[:8]}`\n"
    result += f"**Ref**: `{pipeline_data.get('ref', 'N/A')}`\n"

    if pipeline_data.get("source"):
        result += f"**Source**: {pipeline_data['source']}\n"

    if pipeline_data.get("created_at"):
        result += f"**Created**: {format_date(pipeline_data['created_at'])}\n"

    if pipeline_data.get("duration"):
        result += f"**Duration**: {format_duration(pipeline_data['duration'])}\n"

    if pipeline_data.get("coverage"):
        result += f"**Coverage**: {pipeline_data['coverage']}%\n"

    if pipeline_data.get("web_url"):
        result += f"**URL**: {pipeline_data['web_url']}\n"

    result += "\n"

    # Jobs
    if jobs_data:
        result += "## Jobs\n\n"

        # Group by status
        failed_jobs = [j for j in jobs_data if j.get("status") == "failed"]
        running_jobs = [j for j in jobs_data if j.get("status") == "running"]
        success_jobs = [j for j in jobs_data if j.get("status") == "success"]
        other_jobs = [j for j in jobs_data if j.get("status") not in ["failed", "success", "running"]]

        result += f"**Total**: {len(jobs_data)} | "
        result += f"**Passed**: {len(success_jobs)} | "
        result += f"**Failed**: {len(failed_jobs)} | "
        result += f"**Running**: {len(running_jobs)} | "
        result += f"**Other**: {len(other_jobs)}\n\n"

        # Failed jobs first (most important)
        if failed_jobs:
            result += "### Failed Jobs\n\n"
            for job in failed_jobs:
                job_icon = get_pipeline_status_icon(job.get("status"))
                duration = format_duration(job.get("duration"))
                result += f"- {job_icon} **{job.get('name', 'Unknown')}** "
                result += f"(ID: `{job.get('id')}`, Stage: {job.get('stage', 'N/A')}, {duration})\n"

            result += "\nUse `get_job_log` with Job ID to see error details.\n\n"

        # Running jobs
        if running_jobs:
            result += "### Running Jobs\n\n"
            for job in running_jobs:
                job_icon = get_pipeline_status_icon(job.get("status"))
                result += f"- {job_icon} **{job.get('name', 'Unknown')}** "
                result += f"(ID: `{job.get('id')}`, Stage: {job.get('stage', 'N/A')})\n"
            result += "\n"

        # Successful jobs (compact)
        if success_jobs:
            result += "### Passed Jobs\n\n"
            for job in success_jobs:
                duration = format_duration(job.get("duration"))
                result += f"- [pass] **{job.get('name', 'Unknown')}** "
                result += f"(ID: `{job.get('id')}`, {duration})\n"
            result += "\n"

        # Other jobs
        if other_jobs:
            result += "### Other Jobs\n\n"
            for job in other_jobs:
                job_icon = get_pipeline_status_icon(job.get("status"))
                result += f"- {job_icon} **{job.get('name', 'Unknown')}** "
                result += f"(ID: `{job.get('id')}`, Status: {job.get('status', 'N/A')})\n"
            result += "\n"

    # Status explanation
    status_explanations = {
        "success": "All jobs passed successfully",
        "failed": "One or more jobs failed",
        "running": "Pipeline is currently running",
        "pending": "Pipeline is waiting to start",
        "canceled": "Pipeline was canceled",
        "skipped": "Pipeline was skipped",
        "manual": "Waiting for manual action",
    }

    explanation = status_explanations.get(pipeline_status, f"Status: {pipeline_status}")
    result += f"**Status explanation**: {explanation}\n"

    return [TextContent(type="text", text=result)]
