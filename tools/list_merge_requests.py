import asyncio
from mcp.types import TextContent
from gitlab_api import (
    get_merge_requests,
    get_merge_request_pipeline,
    get_merge_request_changes
)
from utils import (
    format_date,
    get_state_explanation,
    get_pipeline_status_icon,
    analyze_mr_readiness,
    get_mr_priority,
    calculate_change_stats
)
import logging


async def get_enhanced_mr_data(gitlab_url, project_id, access_token, mr_iid):
    """Get enhanced data for a single MR using parallel API calls"""
    try:
        pipeline_task = get_merge_request_pipeline(
            gitlab_url, project_id, access_token, mr_iid
        )
        changes_task = get_merge_request_changes(
            gitlab_url, project_id, access_token, mr_iid
        )
        
        pipeline_result, changes_result = await asyncio.gather(
            pipeline_task, changes_task, return_exceptions=True
        )
        
        # Handle pipeline result
        if isinstance(pipeline_result, Exception):
            pipeline_data = None
            logging.warning(f"Pipeline fetch failed for MR {mr_iid}: {pipeline_result}")
        else:
            pipeline_status, pipeline_data, _ = pipeline_result
            if pipeline_status != 200:
                pipeline_data = None
        
        # Handle changes result
        if isinstance(changes_result, Exception):
            changes_data = None
            logging.warning(f"Changes fetch failed for MR {mr_iid}: {changes_result}")
        else:
            changes_status, changes_data, _ = changes_result
            if changes_status != 200:
                changes_data = None
        
        return pipeline_data, changes_data
        
    except Exception as e:
        logging.warning(f"Error fetching enhanced data for MR {mr_iid}: {e}")
        return None, None


async def list_merge_requests(gitlab_url, project_id, access_token, args):
    logging.info(f"list_merge_requests called with args: {args}")
    
    # Prepare parameters for API call
    state = args.get("state", "opened")
    target_branch = args.get("target_branch")
    limit = args.get("limit", 10)
    
    params = {
        "state": state,
        "per_page": limit,
        "order_by": "updated_at",
        "sort": "desc"
    }
    
    if target_branch:
        params["target_branch"] = target_branch
    
    # Get basic MR data
    status, data, error = await get_merge_requests(
        gitlab_url, project_id, access_token, params
    )
    
    if status != 200:
        logging.error(f"Error listing merge requests: {status} - {error}")
        raise Exception(f"Error listing merge requests: {status} - {error}")
    
    # Start building enhanced response
    state_filter = f" ({state})" if state != "all" else ""
    result = f"# 📋 Merge Requests{state_filter}\n"
    result += f"*Found {len(data)} merge request{'s' if len(data) != 1 else ''}*\n\n"
    
    if not data:
        result += "📭 No merge requests found.\n"
        if state == "opened":
            result += "💡 **Tip**: Create a merge request to start the development workflow.\n"
        return [TextContent(type="text", text=result)]
    
    # Get enhanced data for all MRs in parallel (limit to first 5 for performance)
    enhanced_data_tasks = []
    for mr in data[:5]:  # Limit parallel calls for performance
        task = get_enhanced_mr_data(
            gitlab_url, project_id, access_token, mr['iid']
        )
        enhanced_data_tasks.append(task)
    
    try:
        enhanced_results = await asyncio.gather(*enhanced_data_tasks)
    except Exception as e:
        logging.warning(f"Error in parallel enhanced data fetch: {e}")
        enhanced_results = [(None, None)] * len(data[:5])
    
    # Process and format each MR with enhanced data
    for i, mr in enumerate(data):
        # Get enhanced data if available
        if i < len(enhanced_results):
            pipeline_data, changes_data = enhanced_results[i]
        else:
            pipeline_data, changes_data = None, None
        
        # MR Header with visual indicators
        if mr['state'] == 'merged':
            state_icon = "✅"
        elif mr['state'] == 'opened':
            state_icon = "🔄"
        else:
            state_icon = "❌"
        
        result += f"## {state_icon} !{mr['iid']}: {mr['title']}\n"
        
        # Basic info with enhanced formatting
        author_name = mr['author']['name']
        author_username = mr['author']['username']
        result += f"**👤 Author**: {author_name} (@{author_username})\n"
        result += f"**📊 Status**: {mr['state']} ({get_state_explanation(mr['state'])})\n"
        
        # Priority and readiness
        priority = get_mr_priority(mr)
        readiness = analyze_mr_readiness(mr, pipeline_data)
        result += f"**🏷️ Priority**: {priority}\n"
        result += f"**🚦 Merge Status**: {readiness}\n"
        
        # Dates with better formatting
        result += f"**📅 Created**: {format_date(mr['created_at'])}\n"
        result += f"**🔄 Updated**: {format_date(mr['updated_at'])}\n"
        
        # Branch info
        source_branch = mr['source_branch']
        target_branch = mr['target_branch']
        result += f"**🌿 Branches**: `{source_branch}` → `{target_branch}`\n"
        
        # Pipeline status with enhanced data
        if pipeline_data:
            pipeline_status = pipeline_data.get('status')
            pipeline_icon = get_pipeline_status_icon(pipeline_status)
            result += f"**🔧 Pipeline**: {pipeline_icon} {pipeline_status}\n"
            
            # Add pipeline details if available
            if pipeline_data.get('web_url'):
                result += f"  *[View Pipeline]({pipeline_data['web_url']})*\n"
        elif mr.get('pipeline'):
            # Fallback to basic pipeline info from MR data
            pipeline_status = mr['pipeline'].get('status')
            pipeline_icon = get_pipeline_status_icon(pipeline_status)
            result += f"**🔧 Pipeline**: {pipeline_icon} {pipeline_status or 'unknown'}\n"
        
        # Changes statistics
        if changes_data:
            change_stats = calculate_change_stats(changes_data)
            result += f"**📈 Changes**: {change_stats}\n"
        
        # Labels with visual indicators
        if mr.get('labels'):
            labels_str = ', '.join(f"`{label}`" for label in mr['labels'])
            result += f"**🏷️ Labels**: {labels_str}\n"
        
        # Draft/WIP status
        if mr.get('draft') or mr.get('work_in_progress'):
            result += "**⚠️ Status**: 🚧 Draft/Work in Progress\n"
        
        # Merge conflicts warning
        if mr.get('has_conflicts'):
            result += "**⚠️ Warning**: 🔥 Has merge conflicts\n"
        
        # Quick actions
        result += f"**🔗 Actions**: [View MR]({mr['web_url']})"
        if mr['state'] == 'opened':
            result += f" | [Review]({mr['web_url']})"
        result += "\n\n"
    
    # Add comprehensive summary section
    result += "## 📊 Summary\n"
    
    # State breakdown
    state_counts = {}
    for mr in data:
        state = mr['state']
        state_counts[state] = state_counts.get(state, 0) + 1
    
    result += "**State Breakdown**:\n"
    for state, count in state_counts.items():
        if state == 'merged':
            icon = "✅"
        elif state == 'opened':
            icon = "🔄"
        else:
            icon = "❌"
        result += f"  • {icon} {state.title()}: {count}\n"
    
    # Priority analysis
    priority_counts = {}
    for mr in data:
        priority = get_mr_priority(mr)
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    if len(priority_counts) > 1:
        result += "\n**Priority Breakdown**:\n"
        for priority, count in priority_counts.items():
            result += f"  • {priority}: {count}\n"
    
    # Action items for opened MRs
    opened_mrs = [mr for mr in data if mr['state'] == 'opened']
    
    if opened_mrs:
        result += "\n**🎯 Action Items**:\n"
        
        # Count different types of issues
        has_conflicts = sum(1 for mr in opened_mrs if mr.get('has_conflicts'))
        drafts = sum(1 for mr in opened_mrs if mr.get('draft') or mr.get('work_in_progress'))
        
        # Count pipeline issues from enhanced data
        failed_pipelines = 0
        for i, mr in enumerate(opened_mrs):
            if i < len(enhanced_results):
                pipeline_data, _ = enhanced_results[i]
                if pipeline_data and pipeline_data.get('status') == 'failed':
                    failed_pipelines += 1
        
        if has_conflicts:
            result += f"  • 🔥 {has_conflicts} MR{'s' if has_conflicts > 1 else ''} with merge conflicts\n"
        if drafts:
            result += f"  • 🚧 {drafts} draft MR{'s' if drafts > 1 else ''} in progress\n"
        if failed_pipelines:
            result += f"  • ❌ {failed_pipelines} MR{'s' if failed_pipelines > 1 else ''} with failed pipelines\n"
        
        # Calculate ready MRs
        ready_count = len(opened_mrs) - has_conflicts - drafts - failed_pipelines
        if ready_count > 0:
            result += f"  • ✅ {ready_count} MR{'s' if ready_count > 1 else ''} ready for review\n"
        
        # Next steps
        result += "\n**📋 Next Steps**:\n"
        if has_conflicts:
            result += "  • 🔧 Resolve merge conflicts to unblock development\n"
        if failed_pipelines:
            result += "  • 🔧 Fix failing pipelines to ensure quality\n"
        if ready_count > 0:
            result += "  • 👀 Review and approve ready merge requests\n"
    else:
        result += "\n**🎯 Action Items**:\n"
        if state == "opened":
            result += "  • 🎉 No open merge requests - ready for new features!\n"
        else:
            result += "  • 📊 Consider filtering by 'opened' state to see active work\n"
    
    return [TextContent(type="text", text=result)] 