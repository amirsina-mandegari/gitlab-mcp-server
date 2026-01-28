WORKFLOW_PROMPT = """
GitLab MCP requires a project_id for most operations.

TO FIND PROJECT ID:
- ALWAYS use search_projects(search="name") - fast and efficient
- ONLY use list_my_projects() if user asks "what projects do I have"

IMPORTANT: If user mentions a project name like "backend", "api", "frontend",
use search_projects immediately. Do NOT use list_my_projects for this.

TO FIND MERGE REQUEST:
- Know the MR number? → Use it directly as merge_request_iid
- Know the branch? → get_branch_merge_requests(branch_name="...")
- Want to browse? → list_merge_requests(state="opened")

All other tools need project_id + merge_request_iid.
"""

DEBUGGING_PROMPT = """
When debugging CI/CD failures, choose the right tool:

FOR TEST FAILURES:
1. get_pipeline_test_summary → Quick pass/fail counts (fast)
2. get_merge_request_test_report → Detailed errors + stack traces (use this for fixing)

FOR BUILD/OTHER FAILURES:
1. get_merge_request_pipeline → See all jobs, find failed job_id
2. get_job_log(job_id=...) → Get full output for that job

DECISION TREE:
- "Tests failed" → Start with test_report
- "Build failed" → Start with pipeline → job_log
- "Quick status check" → Use test_summary
"""

REVIEW_PROMPT = """
Code review workflow:

READ REVIEWS:
- get_merge_request_reviews → Returns discussions with discussion_id

RESPOND:
- reply_to_review_comment(discussion_id, body) → Reply to thread
- resolve_review_discussion(discussion_id) → Mark resolved
- create_review_comment(body) → Start new thread

COMPLETE REVIEW:
- approve_merge_request → Add approval
- merge_merge_request → Merge (check status first with get_merge_request_details)

Note: You cannot approve your own MRs.
"""

PROMPTS = {
    "gitlab-workflow": {
        "title": "GitLab Workflow",
        "description": "How to find projects and merge requests",
        "content": WORKFLOW_PROMPT,
    },
    "debug-pipeline": {
        "title": "Debug Pipeline",
        "description": "Which tool to use for different CI/CD failures",
        "content": DEBUGGING_PROMPT,
    },
    "review-workflow": {
        "title": "Review Workflow",
        "description": "How to read and respond to code reviews",
        "content": REVIEW_PROMPT,
    },
}
