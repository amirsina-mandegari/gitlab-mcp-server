from datetime import datetime


def format_date(iso_date_string):
    """Convert ISO date to human-readable format"""
    try:
        dt = datetime.fromisoformat(iso_date_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return iso_date_string


def get_state_explanation(state):
    """Get human-readable explanation of MR state"""
    explanations = {
        "opened": "Ready for review",
        "merged": "Successfully merged",
        "closed": "Closed without merging",
        "locked": "Locked (no new discussions)",
        "draft": "Work in progress",
    }
    return explanations.get(state, state)


def get_pipeline_status_icon(status):
    """Get emoji for pipeline status"""
    if not status:
        return "⚪"

    icons = {
        "success": "✅",
        "failed": "❌",
        "running": "🔄",
        "pending": "⏳",
        "canceled": "⏹️",
        "skipped": "⏭️",
        "manual": "👤",
    }
    return icons.get(status, "❓")


def calculate_change_stats(changes):
    """Calculate lines added/removed from changes"""
    if not changes or "changes" not in changes:
        return "No changes"

    additions = 0
    deletions = 0

    for change in changes["changes"]:
        if "diff" in change:
            diff_lines = change["diff"].split("\n")
            for line in diff_lines:
                if line.startswith("+") and not line.startswith("+++"):
                    additions += 1
                elif line.startswith("-") and not line.startswith("---"):
                    deletions += 1

    return f"+{additions}/-{deletions}"


def analyze_mr_readiness(mr_data, pipeline_data=None, approvals=None):
    """Analyze if MR is ready to merge and what's blocking it"""
    blockers = []

    if mr_data.get("draft") or mr_data.get("work_in_progress"):
        blockers.append("🚧 Draft/WIP status")

    if mr_data.get("has_conflicts"):
        blockers.append("⚠️ Merge conflicts")

    if pipeline_data and pipeline_data.get("status") == "failed":
        blockers.append("❌ Pipeline failed")
    elif pipeline_data and pipeline_data.get("status") == "running":
        blockers.append("🔄 Pipeline running")

    if approvals and "approvals_required" in approvals:
        approved_count = len(approvals.get("approved_by", []))
        required_count = approvals.get("approvals_required", 0)
        if approved_count < required_count:
            msg = f"👥 Needs approval ({approved_count}/{required_count})"
            blockers.append(msg)

    if mr_data.get("merge_status") == "cannot_be_merged":
        blockers.append("🚫 Cannot be merged")

    if not blockers:
        return "✅ Ready to merge"
    else:
        return f"🚫 Blocked by: {', '.join(blockers)}"


def get_mr_priority(mr_data):
    """Determine MR priority based on labels and other factors"""
    labels = mr_data.get("labels", [])

    for label in labels:
        if "critical" in label.lower() or "urgent" in label.lower():
            return "🔴 Critical"
        elif "high" in label.lower():
            return "🟡 High"
        elif "low" in label.lower():
            return "🟢 Low"

    return "⚪ Normal"
