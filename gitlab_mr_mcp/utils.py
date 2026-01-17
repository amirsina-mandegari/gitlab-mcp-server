from datetime import datetime


def format_date(iso_date_string):
    """Convert ISO date to human-readable format"""
    try:
        dt = datetime.fromisoformat(iso_date_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, AttributeError):
        return str(iso_date_string) if iso_date_string else "N/A"


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
    """Get icon for pipeline status - minimal set"""
    if not status:
        return "-"

    icons = {
        "success": "[pass]",
        "failed": "[FAIL]",
        "running": "[running]",
        "pending": "[pending]",
        "canceled": "[canceled]",
        "skipped": "[skipped]",
        "manual": "[manual]",
    }
    return icons.get(status, f"[{status}]")


def get_state_icon(state):
    """Get icon for MR state - minimal set"""
    icons = {
        "merged": "[merged]",
        "opened": "[open]",
        "closed": "[closed]",
    }
    return icons.get(state, f"[{state}]")


def calculate_change_stats(changes):
    """Calculate lines added/removed from changes"""
    if not changes or "changes" not in changes:
        return "No changes"

    additions = 0
    deletions = 0
    file_count = len(changes.get("changes", []))

    for change in changes["changes"]:
        if "diff" in change:
            diff_lines = change["diff"].split("\n")
            for line in diff_lines:
                if line.startswith("+") and not line.startswith("+++"):
                    additions += 1
                elif line.startswith("-") and not line.startswith("---"):
                    deletions += 1

    return f"{file_count} files, +{additions}/-{deletions}"


def analyze_mr_readiness(mr_data, pipeline_data=None, approvals=None):
    """Analyze if MR is ready to merge and what's blocking it"""
    blockers = []

    if mr_data.get("draft") or mr_data.get("work_in_progress"):
        blockers.append("Draft/WIP")

    if mr_data.get("has_conflicts"):
        blockers.append("Merge conflicts")

    if pipeline_data and pipeline_data.get("status") == "failed":
        blockers.append("Pipeline failed")
    elif pipeline_data and pipeline_data.get("status") == "running":
        blockers.append("Pipeline running")

    if approvals and "approvals_required" in approvals:
        approved_count = len(approvals.get("approved_by", []))
        required_count = approvals.get("approvals_required", 0)
        if approved_count < required_count:
            blockers.append(f"Needs approval ({approved_count}/{required_count})")

    if mr_data.get("merge_status") == "cannot_be_merged":
        blockers.append("Cannot be merged")

    if not blockers:
        return "Ready to merge"
    else:
        return f"Blocked: {', '.join(blockers)}"


def get_mr_priority(mr_data):
    """Determine MR priority based on labels"""
    labels = mr_data.get("labels", [])

    for label in labels:
        label_lower = label.lower()
        if "critical" in label_lower or "urgent" in label_lower:
            return "Critical"
        elif "high" in label_lower:
            return "High"
        elif "low" in label_lower:
            return "Low"

    return "Normal"


def format_user(user_data):
    """Format user info consistently"""
    if not user_data:
        return "Unknown"
    name = user_data.get("name", "Unknown")
    username = user_data.get("username", "unknown")
    return f"{name} (@{username})"


def format_labels(labels):
    """Format labels consistently"""
    if not labels:
        return None
    return ", ".join(f"`{label}`" for label in labels)


def truncate_text(text, max_length=100):
    """Truncate text with ellipsis"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
