import logging

from mcp.types import TextContent

from gitlab_mcp_server.gitlab_api import get_merge_request_pipeline, get_pipeline_test_report


async def get_merge_request_test_report(gitlab_url, project_id, access_token, args):
    """Get the test report for a merge request's latest pipeline"""
    logging.info(f"get_merge_request_test_report called with args: {args}")
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
        result = f"# 📊 Test Report for Merge Request !{mr_iid}\n\n"
        result += "ℹ️ No pipeline found for this merge request.\n\n"
        result += "Cannot fetch test report without a pipeline.\n"
        return [TextContent(type="text", text=result)]

    pipeline_id = pipeline_data.get("id")
    logging.info(f"Fetching test report for pipeline {pipeline_id}")

    # Now get the test report for this pipeline
    try:
        status, report_data, error = await get_pipeline_test_report(gitlab_url, project_id, access_token, pipeline_id)
    except Exception as e:
        logging.error(f"Error fetching test report: {e}")
        raise Exception(f"Error fetching test report: {e}")

    if status != 200:
        logging.error(f"Error fetching test report: {status} - {error}")
        if status == 404:
            result = f"# 📊 Test Report for Merge Request !{mr_iid}\n\n"
            result += "ℹ️ No test report available for this merge request.\n\n"
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
        raise Exception(f"Error fetching test report: {status} - {error}")

    # Format the test report
    result = f"# 📊 Test Report for Merge Request !{mr_iid}\n\n"
    result += f"**Pipeline**: #{pipeline_id}"
    if pipeline_data.get("web_url"):
        result += f" - [View Pipeline]({pipeline_data['web_url']})\n\n"
    else:
        result += "\n\n"

    total_time = report_data.get("total_time", 0)
    total_count = report_data.get("total_count", 0)
    success_count = report_data.get("success_count", 0)
    failed_count = report_data.get("failed_count", 0)
    skipped_count = report_data.get("skipped_count", 0)
    error_count = report_data.get("error_count", 0)

    # Summary
    result += "## 📋 Summary\n\n"
    result += f"**Total Tests**: {total_count}\n"
    result += f"**✅ Passed**: {success_count}\n"
    result += f"**❌ Failed**: {failed_count}\n"
    result += f"**⚠️ Errors**: {error_count}\n"
    result += f"**⏭️ Skipped**: {skipped_count}\n"
    result += f"**⏱️ Total Time**: {total_time:.2f}s\n\n"

    if total_count == 0:
        result += "ℹ️ No tests were found in the test report.\n"
        return [TextContent(type="text", text=result)]

    # Pass rate
    if total_count > 0:
        pass_rate = (success_count / total_count) * 100
        if pass_rate == 100:
            result += f"**🎉 Pass Rate**: {pass_rate:.1f}% - "
            result += "All tests passed!\n\n"
        else:
            result += f"**📊 Pass Rate**: {pass_rate:.1f}%\n\n"

    # Show failed tests first
    test_suites = report_data.get("test_suites", [])

    if failed_count > 0 or error_count > 0:
        result += "## ❌ Failed Tests\n\n"

        for suite in test_suites:
            suite_name = suite.get("name", "Unknown Suite")
            test_cases = suite.get("test_cases", [])

            failed_cases = [tc for tc in test_cases if tc.get("status") in ["failed", "error"]]

            if failed_cases:
                result += f"### 📦 {suite_name}\n\n"

                for test_case in failed_cases:
                    test_name = test_case.get("name", "Unknown Test")
                    status = test_case.get("status", "unknown")
                    execution_time = test_case.get("execution_time", 0)

                    status_icon = "❌" if status == "failed" else "⚠️"
                    result += f"#### {status_icon} {test_name}\n\n"
                    result += f"**Status**: {status}\n"
                    result += f"**Duration**: {execution_time:.3f}s\n"

                    if test_case.get("classname"):
                        result += f"**Class**: `{test_case['classname']}`\n"

                    if test_case.get("file"):
                        result += f"**File**: `{test_case['file']}`\n"

                    # System output (error message)
                    if test_case.get("system_output"):
                        result += "\n**Error Output:**\n\n"
                        result += "```\n"
                        # Limit error output to reasonable size
                        error_output = test_case["system_output"]
                        if len(error_output) > 2000:
                            result += error_output[:2000]
                            result += "\n... (truncated)\n"
                        else:
                            result += error_output
                        result += "\n```\n"

                    result += "\n"

    # Show skipped tests if any
    if skipped_count > 0:
        result += "## ⏭️ Skipped Tests\n\n"

        for suite in test_suites:
            suite_name = suite.get("name", "Unknown Suite")
            test_cases = suite.get("test_cases", [])

            skipped_cases = [tc for tc in test_cases if tc.get("status") == "skipped"]

            if skipped_cases:
                result += f"### 📦 {suite_name}\n\n"
                for test_case in skipped_cases:
                    test_name = test_case.get("name", "Unknown Test")
                    result += f"- ⏭️ {test_name}"
                    if test_case.get("classname"):
                        result += f" (`{test_case['classname']}`)"
                    result += "\n"
                result += "\n"

    # Show test suites summary
    if len(test_suites) > 0:
        result += "## 📦 Test Suites Overview\n\n"
        for suite in test_suites:
            suite_name = suite.get("name", "Unknown Suite")
            total = suite.get("total_count", 0)
            success = suite.get("success_count", 0)
            failed = suite.get("failed_count", 0)
            skipped = suite.get("skipped_count", 0)
            errors = suite.get("error_count", 0)
            suite_time = suite.get("total_time", 0)

            status_icon = "✅" if failed == 0 and errors == 0 else "❌"
            result += f"- {status_icon} **{suite_name}**: "
            result += f"{success}/{total} passed"
            if failed > 0:
                result += f", {failed} failed"
            if errors > 0:
                result += f", {errors} errors"
            if skipped > 0:
                result += f", {skipped} skipped"
            result += f" ({suite_time:.2f}s)\n"

    # Add helpful tips if there are failures
    if failed_count > 0 or error_count > 0:
        result += "\n## 💡 Next Steps\n\n"
        result += "1. Review the error messages above\n"
        result += "2. Check the specific test files mentioned\n"
        result += "3. Use `get_job_log` to see full CI output if needed\n"
        result += "4. Run tests locally to reproduce the failures\n"

    return [TextContent(type="text", text=result)]
