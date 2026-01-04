import logging

from mcp.types import TextContent

from gitlab_mcp_server.gitlab_api import get_merge_request_pipeline as api_get_merge_request_pipeline
from gitlab_mcp_server.gitlab_api import get_pipeline_jobs
from gitlab_mcp_server.utils import format_date, get_pipeline_status_icon


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
        result = f"# 🔧 Pipeline for Merge Request !{mr_iid}\n\n"
        result += "ℹ️ No pipeline found for this merge request.\n\n"
        result += "This could mean:\n"
        result += "• No CI/CD is configured for this project\n"
        result += "• The pipeline hasn't been triggered yet\n"
        result += "• The merge request branch has no commits\n"
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

    # Format the pipeline data
    pipeline_status = pipeline_data.get("status", "unknown")
    pipeline_icon = get_pipeline_status_icon(pipeline_status)

    result = f"# {pipeline_icon} Pipeline for Merge Request !{mr_iid}\n\n"

    result += "## 📊 Pipeline Overview\n"
    result += f"**🆔 Pipeline ID**: #{pipeline_data.get('id', 'N/A')}\n"
    result += f"**📊 Status**: {pipeline_icon} {pipeline_status}\n"
    result += f"**🔗 SHA**: `{pipeline_data.get('sha', 'N/A')[:8]}`\n"
    result += f"**🌿 Ref**: `{pipeline_data.get('ref', 'N/A')}`\n"

    if pipeline_data.get("source"):
        result += f"**📍 Source**: {pipeline_data['source']}\n"

    if pipeline_data.get("created_at"):
        result += f"**📅 Created**: {format_date(pipeline_data['created_at'])}\n"

    if pipeline_data.get("updated_at"):
        result += f"**🔄 Updated**: {format_date(pipeline_data['updated_at'])}\n"

    if pipeline_data.get("started_at"):
        result += f"**▶️ Started**: {format_date(pipeline_data['started_at'])}\n"

    if pipeline_data.get("finished_at"):
        result += f"**⏹️ Finished**: {format_date(pipeline_data['finished_at'])}\n"

    # Duration
    if pipeline_data.get("duration"):
        duration_mins = pipeline_data["duration"] // 60
        duration_secs = pipeline_data["duration"] % 60
        result += f"**⏱️ Duration**: {duration_mins}m {duration_secs}s\n"

    if pipeline_data.get("queued_duration"):
        queued_mins = pipeline_data["queued_duration"] // 60
        queued_secs = pipeline_data["queued_duration"] % 60
        result += f"**⏳ Queued**: {queued_mins}m {queued_secs}s\n"

    result += "\n"

    # User info
    if pipeline_data.get("user"):
        user = pipeline_data["user"]
        result += "## 👤 Triggered By\n"
        result += f"**Name**: {user.get('name', 'N/A')}\n"
        result += f"**Username**: @{user.get('username', 'N/A')}\n"
        result += "\n"

    # Coverage
    if pipeline_data.get("coverage"):
        result += "## 📈 Code Coverage\n"
        result += f"**Coverage**: {pipeline_data['coverage']}%\n"
        result += "\n"

    # Web URL
    if pipeline_data.get("web_url"):
        result += "## 🔗 Actions\n"
        result += f"• [View Pipeline Details]({pipeline_data['web_url']})\n"
        result += "\n"

    # Jobs information
    if jobs_data:
        result += "## 🔨 Pipeline Jobs\n\n"

        # Group jobs by status
        failed_jobs = [j for j in jobs_data if j.get("status") == "failed"]
        success_jobs = [j for j in jobs_data if j.get("status") == "success"]
        running_jobs = [j for j in jobs_data if j.get("status") == "running"]
        other_jobs = [j for j in jobs_data if j.get("status") not in ["failed", "success", "running"]]

        result += f"**Total Jobs**: {len(jobs_data)}\n"
        result += f"**✅ Success**: {len(success_jobs)} | "
        result += f"**❌ Failed**: {len(failed_jobs)} | "
        result += f"**🔄 Running**: {len(running_jobs)} | "
        result += f"**⏳ Other**: {len(other_jobs)}\n\n"

        # Show failed jobs first
        if failed_jobs:
            result += "### ❌ Failed Jobs\n\n"
            for job in failed_jobs:
                job_icon = get_pipeline_status_icon(job.get("status"))
                result += f"- {job_icon} **{job.get('name', 'Unknown Job')}** "
                result += f"(Job ID: `{job.get('id')}`, Stage: {job.get('stage', 'N/A')})"

                if job.get("duration"):
                    duration_mins = int(job["duration"]) // 60
                    duration_secs = int(job["duration"]) % 60
                    result += f" - {duration_mins}m {duration_secs}s"

                if job.get("web_url"):
                    result += f" - [View]({job['web_url']})"

                result += "\n"

            result += "\n*💡 Tip: Use `get_job_log` with a Job ID to see the full output*\n"
            result += "\n"

        # Show running jobs
        if running_jobs:
            result += "### 🔄 Running Jobs\n\n"
            for job in running_jobs:
                job_icon = get_pipeline_status_icon(job.get("status"))
                result += f"- {job_icon} **{job.get('name', 'Unknown Job')}** "
                result += f"(Job ID: `{job.get('id')}`, Stage: {job.get('stage', 'N/A')})"
                if job.get("web_url"):
                    result += f" - [View]({job['web_url']})"
                result += "\n"
            result += "\n"

        # Show successful jobs (summary)
        if success_jobs:
            result += "### ✅ Successful Jobs\n\n"
            for job in success_jobs:
                result += f"- ✅ **{job.get('name', 'Unknown Job')}** "
                result += f"(Job ID: `{job.get('id')}`, Stage: {job.get('stage', 'N/A')})"
                if job.get("duration"):
                    duration_mins = int(job["duration"]) // 60
                    duration_secs = int(job["duration"]) % 60
                    result += f" - {duration_mins}m {duration_secs}s"
                result += "\n"
            result += "\n"

        # Show other jobs
        if other_jobs:
            result += "### ⏳ Other Jobs\n\n"
            for job in other_jobs:
                job_icon = get_pipeline_status_icon(job.get("status"))
                result += f"- {job_icon} **{job.get('name', 'Unknown Job')}** "
                result += f"(Job ID: `{job.get('id')}`, Stage: {job.get('stage', 'N/A')}, "
                result += f"Status: {job.get('status', 'N/A')})\n"
            result += "\n"

    # Status explanation
    result += "## ℹ️ Status Information\n"
    status_explanations = {
        "success": "✅ All jobs passed successfully",
        "failed": "❌ One or more jobs failed",
        "running": "🔄 Pipeline is currently running",
        "pending": "⏳ Pipeline is waiting to start",
        "canceled": "⏹️ Pipeline was canceled",
        "skipped": "⏭️ Pipeline was skipped",
        "manual": "👤 Waiting for manual action",
        "created": "📝 Pipeline was created but not started",
        "preparing": "🔧 Pipeline is preparing to run",
        "waiting_for_resource": "⏸️ Waiting for available resources",
        "scheduled": "📅 Pipeline is scheduled to run",
    }

    explanation = status_explanations.get(pipeline_status, f"Unknown status: {pipeline_status}")
    result += f"{explanation}\n"

    return [TextContent(type="text", text=result)]
