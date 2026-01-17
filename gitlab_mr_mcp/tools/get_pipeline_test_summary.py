import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_merge_request_pipeline, get_pipeline_test_report_summary


async def get_pipeline_test_summary(gitlab_url, project_id, access_token, args):
    """Get the test summary for a merge request's latest pipeline"""
    logging.info(f"get_pipeline_test_summary called with args: {args}")
    mr_iid = args["merge_request_iid"]

    # Get the latest pipeline
    try:
        pipeline_status, pipeline_data, pipeline_error = await get_merge_request_pipeline(
            gitlab_url, project_id, access_token, mr_iid
        )
    except Exception as e:
        logging.error(f"Error fetching pipeline: {e}")
        raise Exception(f"Error fetching pipeline for MR: {e}")

    if pipeline_status != 200 or not pipeline_data:
        result = f"# Test Summary for MR !{mr_iid}\n\n"
        result += "No pipeline found for this merge request.\n"
        return [TextContent(type="text", text=result)]

    pipeline_id = pipeline_data.get("id")
    logging.info(f"Fetching test summary for pipeline {pipeline_id}")

    # Get test summary
    try:
        status, summary_data, error = await get_pipeline_test_report_summary(
            gitlab_url, project_id, access_token, pipeline_id
        )
    except Exception as e:
        logging.error(f"Error fetching test summary: {e}")
        raise Exception(f"Error fetching test summary: {e}")

    if status != 200:
        logging.error(f"Error fetching test summary: {status} - {error}")
        if status == 404:
            result = f"# Test Summary for MR !{mr_iid}\n\n"
            result += "No test summary available.\n\n"
            result += "To generate test reports:\n"
            result += "1. Run tests that output JUnit XML format\n"
            result += "2. Use `artifacts:reports:junit` in .gitlab-ci.yml\n"
            return [TextContent(type="text", text=result)]
        raise Exception(f"Error fetching test summary: {status} - {error}")

    # Format output
    result = f"# Test Summary for MR !{mr_iid}\n\n"
    result += f"**Pipeline**: #{pipeline_id}"
    if pipeline_data.get("web_url"):
        result += f" - {pipeline_data['web_url']}"
    result += "\n\n"

    # Summary stats
    total = summary_data.get("total", {})
    total_count = total.get("count", 0)
    success_count = total.get("success", 0)
    failed_count = total.get("failed", 0)
    skipped_count = total.get("skipped", 0)
    error_count = total.get("error", 0)
    total_time = total.get("time", 0)

    result += "## Summary\n\n"
    result += f"**Total**: {total_count} | "
    result += f"**Passed**: {success_count} | "
    result += f"**Failed**: {failed_count} | "
    result += f"**Errors**: {error_count} | "
    result += f"**Skipped**: {skipped_count}\n"
    result += f"**Duration**: {total_time:.2f}s\n\n"

    if total_count == 0:
        result += "No tests found in the summary.\n"
        return [TextContent(type="text", text=result)]

    # Pass rate
    pass_rate = (success_count / total_count) * 100
    if pass_rate == 100:
        result += f"**Pass Rate**: {pass_rate:.1f}% - All tests passed\n\n"
    else:
        result += f"**Pass Rate**: {pass_rate:.1f}%\n\n"

    # Test suites
    test_suites = summary_data.get("test_suites", [])
    if test_suites:
        result += "## Test Suites\n\n"
        for suite in test_suites:
            name = suite.get("name", "Unknown")
            suite_total = suite.get("total_count", 0)
            suite_success = suite.get("success_count", 0)
            suite_failed = suite.get("failed_count", 0)
            suite_error = suite.get("error_count", 0)
            suite_time = suite.get("total_time", 0)

            status_marker = "[FAIL]" if (suite_failed > 0 or suite_error > 0) else "[pass]"
            result += f"### {status_marker} {name}\n\n"
            result += f"- Total: {suite_total}\n"
            result += f"- Passed: {suite_success}\n"
            if suite_failed > 0:
                result += f"- Failed: {suite_failed}\n"
            if suite_error > 0:
                result += f"- Errors: {suite_error}\n"
            result += f"- Duration: {suite_time:.2f}s\n\n"

    # Next steps for failures
    if failed_count > 0 or error_count > 0:
        result += "## Next Steps\n\n"
        result += "1. Use `get_merge_request_test_report` for detailed error messages\n"
        result += "2. Use `get_job_log` to see full CI output\n"

    return [TextContent(type="text", text=result)]
