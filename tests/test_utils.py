"""Test utility functions."""

from gitlab_mr_mcp.utils import (
    analyze_mr_readiness,
    calculate_change_stats,
    format_date,
    get_mr_priority,
    get_pipeline_status_icon,
    get_state_explanation,
)


def test_format_date_valid():
    """Test date formatting with valid ISO date."""
    result = format_date("2024-01-15T10:30:00Z")
    assert "2024" in result
    assert "01" in result or "Jan" in result


def test_format_date_invalid():
    """Test date formatting with invalid date."""
    result = format_date("not-a-date")
    assert result == "not-a-date"


def test_get_pipeline_status_icon():
    """Test pipeline status icons."""
    assert get_pipeline_status_icon("success") == "✅"
    assert get_pipeline_status_icon("failed") == "❌"
    assert get_pipeline_status_icon("running") == "🔄"
    assert get_pipeline_status_icon("pending") == "⏳"
    assert get_pipeline_status_icon(None) == "⚪"


def test_get_state_explanation():
    """Test MR state explanations."""
    assert get_state_explanation("opened") == "Ready for review"
    assert get_state_explanation("merged") == "Successfully merged"
    assert get_state_explanation("closed") == "Closed without merging"
    assert get_state_explanation("unknown") == "unknown"


def test_calculate_change_stats_empty():
    """Test change stats with no changes."""
    result = calculate_change_stats(None)
    assert result == "No changes"

    result = calculate_change_stats({})
    assert result == "No changes"


def test_get_mr_priority():
    """Test MR priority detection."""
    assert "Critical" in get_mr_priority({"labels": ["critical-fix"]})
    assert "High" in get_mr_priority({"labels": ["high-priority"]})
    assert "Low" in get_mr_priority({"labels": ["low-priority"]})
    assert "Normal" in get_mr_priority({"labels": []})


def test_analyze_mr_readiness_ready():
    """Test MR readiness when ready to merge."""
    mr_data = {"draft": False, "has_conflicts": False}
    result = analyze_mr_readiness(mr_data)
    assert "Ready to merge" in result


def test_analyze_mr_readiness_blocked():
    """Test MR readiness when blocked."""
    mr_data = {"draft": True}
    result = analyze_mr_readiness(mr_data)
    assert "Blocked" in result or "Draft" in result
