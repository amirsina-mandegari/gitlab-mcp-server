import logging

from mcp.types import TextContent

from gitlab_mr_mcp.gitlab_api import get_merge_request_pipeline, get_pipeline_test_report_summary


async def get_pipeline_test_summary(gitlab_url, project_id, access_token, args):
    """Get the test summary for a merge request's latest pipeline"""
    logging.info(f"get_pipeline_test_summary called with args: {args}")
    mr_iid = args["merge_request_iid"]

    # First, get the latest pipeline for this MR
    try:
        pipeline_status, pipeline_data, pipeline_error = await get_merge_request_pipeline(
            gitlab_url, project_id, access_token, mr_iid
        )
    except Exception as e:
        logging.error(f"Error fetching pipeline: {e}")
        raise Exception(f"Error fetching pipeline for MR: {e}")

    if pipeline_status != 200 or not pipeline_data:
        result = f"# 📊 Test Summary for Merge Request !{mr_iid}\n\n"
        result += "ℹ️ No pipeline found for this merge request.\n\n"
        result += "Cannot fetch test summary without a pipeline.\n"
        return [TextContent(type="text", text=result)]

    pipeline_id = pipeline_data.get("id")
    logging.info(f"Fetching test summary for pipeline {pipeline_id}")

    # Now get the test summary for this pipeline
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
            result = f"# 📊 Test Summary for Merge Request !{mr_iid}\n\n"
            result += "ℹ️ No test summary available for this pipeline.\n\n"
            result += "This could mean:\n"
            result += "• No CI/CD pipeline has run tests\n"
            result += "• Tests don't upload JUnit XML or similar reports\n"
            result += "• The pipeline is configured but no test "
            result += "artifacts were generated\n\n"
            result += "**💡 Tip:** To generate test reports, your CI jobs "
            result += "need to:\n"
            result += "1. Run tests that output JUnit XML format\n"
            result += "2. Use `artifacts:reports:junit` in .gitlab-ci.yml\n"
            return [TextContent(type="text", text=result)]
        raise Exception(f"Error fetching test summary: {status} - {error}")

    # Format the test summary
    result = f"# 📊 Test Summary for Merge Request !{mr_iid}\n\n"
    result += f"**Pipeline**: #{pipeline_id}"
    if pipeline_data.get("web_url"):
        result += f" - [View Pipeline]({pipeline_data['web_url']})\n\n"
    else:
        result += "\n\n"

    # Get summary data
    total_time = summary_data.get("total", {}).get("time", 0)
    total_count = summary_data.get("total", {}).get("count", 0)
    success_count = summary_data.get("total", {}).get("success", 0)
    failed_count = summary_data.get("total", {}).get("failed", 0)
    skipped_count = summary_data.get("total", {}).get("skipped", 0)
    error_count = summary_data.get("total", {}).get("error", 0)

    # Summary
    result += "## 📋 Summary\n\n"
    result += f"**Total Tests**: {total_count}\n"
    result += f"**✅ Passed**: {success_count}\n"
    result += f"**❌ Failed**: {failed_count}\n"
    result += f"**⚠️ Errors**: {error_count}\n"
    result += f"**⏭️ Skipped**: {skipped_count}\n"
    result += f"**⏱️ Total Time**: {total_time:.2f}s\n\n"

    if total_count == 0:
        result += "ℹ️ No tests were found in the test summary.\n"
        return [TextContent(type="text", text=result)]

    # Pass rate
    if total_count > 0:
        pass_rate = (success_count / total_count) * 100
        if pass_rate == 100:
            result += f"**🎉 Pass Rate**: {pass_rate:.1f}% - "
            result += "All tests passed!\n\n"
        elif pass_rate >= 80:
            result += f"**✅ Pass Rate**: {pass_rate:.1f}%\n\n"
        elif pass_rate >= 50:
            result += f"**⚠️ Pass Rate**: {pass_rate:.1f}%\n\n"
        else:
            result += f"**❌ Pass Rate**: {pass_rate:.1f}%\n\n"

    # Test suites breakdown
    test_suites = summary_data.get("test_suites", [])
    if test_suites:
        result += "## 📦 Test Suites\n\n"
        for suite in test_suites:
            suite_name = suite.get("name", "Unknown Suite")
            suite_total = suite.get("total_count", 0)
            suite_success = suite.get("success_count", 0)
            suite_failed = suite.get("failed_count", 0)
            suite_skipped = suite.get("skipped_count", 0)
            suite_error = suite.get("error_count", 0)
            suite_time = suite.get("total_time", 0)

            # Determine status icon
            if suite_failed == 0 and suite_error == 0:
                status_icon = "✅"
            elif suite_failed > 0 or suite_error > 0:
                status_icon = "❌"
            else:
                status_icon = "⚪"

            result += f"### {status_icon} {suite_name}\n\n"
            result += f"- **Total**: {suite_total} tests\n"
            result += f"- **✅ Passed**: {suite_success}\n"

            if suite_failed > 0:
                result += f"- **❌ Failed**: {suite_failed}\n"

            if suite_error > 0:
                result += f"- **⚠️ Errors**: {suite_error}\n"

            if suite_skipped > 0:
                result += f"- **⏭️ Skipped**: {suite_skipped}\n"

            result += f"- **⏱️ Duration**: {suite_time:.2f}s\n\n"

    # Add helpful tips if there are failures
    if failed_count > 0 or error_count > 0:
        result += "## 💡 Next Steps\n\n"
        result += "1. Use `get_merge_request_test_report` to see "
        result += "detailed error messages\n"
        result += "2. Check specific failed test names and stack traces\n"
        result += "3. Use `get_job_log` to see full CI output if needed\n"

    return [TextContent(type="text", text=result)]
