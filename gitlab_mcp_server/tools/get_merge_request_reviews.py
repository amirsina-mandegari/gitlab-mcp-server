import asyncio
import logging

from mcp.types import TextContent

from gitlab_mcp_server.gitlab_api import (
    get_merge_request_changes,
    get_merge_request_details,
    get_merge_request_pipeline,
)
from gitlab_mcp_server.gitlab_api import get_merge_request_reviews as api_get_merge_request_reviews
from gitlab_mcp_server.utils import (
    analyze_mr_readiness,
    calculate_change_stats,
    format_date,
    get_mr_priority,
    get_pipeline_status_icon,
    get_state_explanation,
)


def get_review_type_icon(note):
    """Get appropriate icon for review type"""
    if note.get("resolvable"):
        return "💬"
    elif note.get("position"):
        return "📝"
    elif "approved" in note.get("body", "").lower():
        return "✅"
    elif any(word in note.get("body", "").lower() for word in ["reject", "needs work", "changes requested"]):
        return "❌"
    else:
        return "💭"


def get_approval_summary(approvals):
    """Generate enhanced approval summary"""
    if not approvals:
        return "## 👥 Approvals\n❓ No approval information available\n\n"

    result = "## 👥 Approvals\n"

    approved_by = approvals.get("approved_by", [])
    approvals_required = approvals.get("approvals_required", 0)
    approvals_left = approvals.get("approvals_left", 0)

    if approved_by:
        result += f"**✅ Approved by ({len(approved_by)} reviewer"
        result += f"{'s' if len(approved_by) > 1 else ''}):**\n"
        for approval in approved_by:
            user = approval["user"]
            result += f"  • **{user['name']}** (@{user['username']})\n"
        result += "\n"

    if approvals_required > 0:
        if approvals_left == 0:
            status = "✅ Approval requirements met"
        else:
            plural = "s" if approvals_left > 1 else ""
            status = f"⏳ {approvals_left} approval{plural} needed"
        result += f"**Status**: {status}\n"
        received_count = len(approved_by)
        result += f"**Required**: {approvals_required} | **Received**: {received_count}\n\n"
    elif not approved_by:
        result += "📝 No approvals yet\n\n"

    return result


def get_discussion_summary(discussions):
    """Generate enhanced discussion summary with counts and status"""
    if not discussions:
        return "## 💬 Discussions\n❓ No discussion information available\n\n"

    total_discussions = len(discussions)
    resolved_count = sum(1 for d in discussions if d.get("resolved"))
    unresolved_count = total_discussions - resolved_count

    result = "## 💬 Discussions & Reviews\n"
    result += (
        f"**Total**: {total_discussions} | **Resolved**: {resolved_count} | " f"**Unresolved**: {unresolved_count}\n\n"
    )

    if unresolved_count > 0:
        plural = "s" if unresolved_count > 1 else ""
        result += f"⚠️ **{unresolved_count} unresolved discussion{plural}** " "- action needed\n\n"
    elif total_discussions > 0:
        result += "✅ All discussions resolved\n\n"

    return result


def format_discussion_thread(discussion):
    """Format a single discussion thread with enhanced formatting"""
    if not discussion.get("notes"):
        return ""

    result = ""
    thread_resolved = discussion.get("resolved", False)
    thread_icon = "✅" if thread_resolved else "🟡"
    discussion_id = discussion.get("id", "unknown")

    result += f"### {thread_icon} Discussion Thread\n"
    result += f"**Discussion ID**: `{discussion_id}`\n"
    if thread_resolved:
        result += "*Resolved*\n"
    else:
        result += "*Unresolved*\n"

    for note in discussion["notes"]:
        if note.get("system"):
            continue

        author_name = note["author"]["name"]
        author_username = note["author"]["username"]
        note_icon = get_review_type_icon(note)
        note_id = note.get("id", "unknown")

        result += f"\n{note_icon} **{author_name}** (@{author_username})\n"
        timestamp = format_date(note["created_at"])
        result += f"*{timestamp}* | Note ID: `{note_id}`\n"

        if note.get("position"):
            pos = note["position"]
            if pos.get("new_path"):
                result += f"📁 **File**: `{pos['new_path']}`\n"
                if pos.get("new_line"):
                    result += f"📍 **Line**: {pos['new_line']}\n"

        body = note.get("body", "").strip()
        if body:
            result += f"\n{body}\n"

        result += "\n---\n"

    return result + "\n"


async def get_merge_request_reviews(gitlab_url, project_id, access_token, args):
    logging.info(f"get_merge_request_reviews called with args: {args}")
    mr_iid = args["merge_request_iid"]

    tasks = [
        api_get_merge_request_reviews(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_details(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_pipeline(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_changes(gitlab_url, project_id, access_token, mr_iid),
    ]

    try:
        reviews_result, details_result, pipeline_result, changes_result = await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"Error in parallel API calls: {e}")
        raise Exception(f"Error fetching merge request data: {e}")

    discussions_status, discussions, discussions_text = reviews_result["discussions"]
    approvals_status, approvals, approvals_text = reviews_result["approvals"]

    details_status, mr_details, details_text = details_result
    pipeline_status, pipeline_data, pipeline_text = pipeline_result
    changes_status, changes_data, changes_text = changes_result

    if discussions_status != 200:
        logging.error(f"Error fetching discussions {discussions_status}: {discussions_text}")
        raise Exception(f"Error fetching discussions: {discussions_status} - {discussions_text}")

    result = f"# 🔍 Reviews & Discussions for MR !{mr_iid}\n\n"

    if details_status == 200:
        result += "## 📋 Merge Request Overview\n"
        result += f"**Title**: {mr_details.get('title', 'N/A')}\n"
        state = mr_details.get("state", "N/A")
        result += f"**Status**: {state} ({get_state_explanation(state)})\n"
        author = mr_details.get("author", {})
        author_name = author.get("name", "N/A")
        author_username = author.get("username", "N/A")
        result += f"**Author**: {author_name} (@{author_username})\n"
        result += f"**Priority**: {get_mr_priority(mr_details)}\n"

        if pipeline_status == 200 and pipeline_data:
            pipeline_icon = get_pipeline_status_icon(pipeline_data.get("status"))
            result += f"**Pipeline**: {pipeline_icon} {pipeline_data.get('status', 'unknown')}\n"

        if changes_status == 200:
            change_stats = calculate_change_stats(changes_data)
            result += f"**Changes**: {change_stats}\n"

        readiness = analyze_mr_readiness(mr_details, pipeline_data, approvals)
        result += f"**Merge Status**: {readiness}\n"

        result += f"**Updated**: {format_date(mr_details.get('updated_at', 'N/A'))}\n\n"

    result += get_approval_summary(approvals)

    result += get_discussion_summary(discussions)

    if discussions:
        result += "## 📝 Detailed Discussions\n\n"
        for discussion in discussions:
            thread_content = format_discussion_thread(discussion)
            if thread_content:
                result += thread_content
    else:
        result += "💬 No discussions found\n\n"

    result += "## 📊 Action Items\n"
    action_items = []

    if discussions:
        unresolved_count = sum(1 for d in discussions if not d.get("resolved"))
        if unresolved_count > 0:
            action_items.append(
                f"🟡 Resolve {unresolved_count} pending discussion{'s' if unresolved_count > 1 else ''}"
            )

    if approvals and approvals.get("approvals_left", 0) > 0:
        action_items.append(
            f"👥 Obtain {approvals['approvals_left']} more approval{'s' if approvals['approvals_left'] > 1 else ''}"
        )

    if pipeline_status == 200 and pipeline_data and pipeline_data.get("status") == "failed":
        action_items.append("❌ Fix failing pipeline")

    if details_status == 200 and mr_details.get("has_conflicts"):
        action_items.append("⚠️ Resolve merge conflicts")

    if action_items:
        for item in action_items:
            result += f"• {item}\n"
    else:
        result += "✅ No action items - ready for next steps\n"

    return [TextContent(type="text", text=result)]
