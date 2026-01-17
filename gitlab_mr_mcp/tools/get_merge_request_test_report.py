import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_merge_request_pipeline, get_pipeline_test_report


async def get_merge_request_test_report(gitlab_url, project_id, access_token, args):
    """Get the test report for a merge request's latest pipeline"""
    logging.info(f"get_merge_request_test_report called with args: {args}")
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
        result = f"# Test Report for MR !{mr_iid}\n\n"
        result += "No pipeline found for this merge request.\n"
        return [TextContent(type="text", text=result)]

    pipeline_id = pipeline_data.get("id")
    logging.info(f"Fetching test report for pipeline {pipeline_id}")

    # Get test report
    try:
        status, report_data, error = await get_pipeline_test_report(gitlab_url, project_id, access_token, pipeline_id)
    except Exception as e:
        logging.error(f"Error fetching test report: {e}")
        raise Exception(f"Error fetching test report: {e}")

    if status != 200:
        logging.error(f"Error fetching test report: {status} - {error}")
        if status == 404:
            result = f"# Test Report for MR !{mr_iid}\n\n"
            result += "No test report available.\n\n"
            result += "To generate test reports:\n"
            result += "1. Run tests that output JUnit XML format\n"
            result += "2. Use `artifacts:reports:junit` in .gitlab-ci.yml\n"
            return [TextContent(type="text", text=result)]
        raise Exception(f"Error fetching test report: {status} - {error}")

    # Format output
    result = f"# Test Report for MR !{mr_iid}\n\n"
    result += f"**Pipeline**: #{pipeline_id}"
    if pipeline_data.get("web_url"):
        result += f" - {pipeline_data['web_url']}"
    result += "\n\n"

    # Summary
    total_count = report_data.get("total_count", 0)
    success_count = report_data.get("success_count", 0)
    failed_count = report_data.get("failed_count", 0)
    skipped_count = report_data.get("skipped_count", 0)
    error_count = report_data.get("error_count", 0)
    total_time = report_data.get("total_time", 0)

    result += "## Summary\n\n"
    result += f"**Total**: {total_count} | "
    result += f"**Passed**: {success_count} | "
    result += f"**Failed**: {failed_count} | "
    result += f"**Errors**: {error_count} | "
    result += f"**Skipped**: {skipped_count}\n"
    result += f"**Duration**: {total_time:.2f}s\n\n"

    if total_count == 0:
        result += "No tests found in the report.\n"
        return [TextContent(type="text", text=result)]

    # Pass rate
    pass_rate = (success_count / total_count) * 100
    result += f"**Pass Rate**: {pass_rate:.1f}%\n\n"

    # Failed tests (most important)
    test_suites = report_data.get("test_suites", [])

    if failed_count > 0 or error_count > 0:
        result += "## Failed Tests\n\n"

        for suite in test_suites:
            suite_name = suite.get("name", "Unknown")
            test_cases = suite.get("test_cases", [])
            failed_cases = [tc for tc in test_cases if tc.get("status") in ["failed", "error"]]

            if failed_cases:
                result += f"### {suite_name}\n\n"

                for tc in failed_cases:
                    test_name = tc.get("name", "Unknown")
                    status = tc.get("status", "unknown")
                    exec_time = tc.get("execution_time", 0)

                    status_marker = "[FAIL]" if status == "failed" else "[ERROR]"
                    result += f"#### {status_marker} {test_name}\n\n"
                    result += f"**Duration**: {exec_time:.3f}s\n"

                    if tc.get("classname"):
                        result += f"**Class**: `{tc['classname']}`\n"

                    if tc.get("file"):
                        result += f"**File**: `{tc['file']}`\n"

                    # Error output
                    if tc.get("system_output"):
                        result += "\n**Error Output**:\n\n```\n"
                        error_output = tc["system_output"]
                        if len(error_output) > 2000:
                            result += error_output[:2000] + "\n... (truncated)\n"
                        else:
                            result += error_output
                        result += "\n```\n\n"

    # Skipped tests
    if skipped_count > 0:
        result += "## Skipped Tests\n\n"
        for suite in test_suites:
            suite_name = suite.get("name", "Unknown")
            test_cases = suite.get("test_cases", [])
            skipped_cases = [tc for tc in test_cases if tc.get("status") == "skipped"]

            if skipped_cases:
                result += f"### {suite_name}\n\n"
                for tc in skipped_cases:
                    result += f"- {tc.get('name', 'Unknown')}\n"
                result += "\n"

    # Suite overview
    if len(test_suites) > 0:
        result += "## Suites Overview\n\n"
        for suite in test_suites:
            name = suite.get("name", "Unknown")
            total = suite.get("total_count", 0)
            success = suite.get("success_count", 0)
            failed = suite.get("failed_count", 0)
            errors = suite.get("error_count", 0)

            status_marker = "[pass]" if (failed == 0 and errors == 0) else "[FAIL]"
            result += f"- {status_marker} **{name}**: {success}/{total} passed"
            if failed > 0:
                result += f", {failed} failed"
            if errors > 0:
                result += f", {errors} errors"
            result += "\n"

    # Next steps
    if failed_count > 0 or error_count > 0:
        result += "\n## Next Steps\n\n"
        result += "1. Review error messages above\n"
        result += "2. Check the specific test files\n"
        result += "3. Use `get_job_log` for full CI output\n"
        result += "4. Run tests locally to reproduce\n"

    return [TextContent(type="text", text=result)]
