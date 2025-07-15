import asyncio
from mcp.types import TextContent
from gitlab_api import (
    get_merge_request_details as api_get_merge_request_details,
    get_merge_request_pipeline,
    get_merge_request_changes,
    get_merge_request_reviews
)
from utils import (
    format_date,
    get_state_explanation,
    get_pipeline_status_icon,
    calculate_change_stats,
    analyze_mr_readiness,
    get_mr_priority
)
import logging


async def get_merge_request_details(
    gitlab_url, project_id, access_token, args
):
    logging.info(f"get_merge_request_details called with args: {args}")
    mr_iid = args["merge_request_iid"]
    
    # Parallel API calls for comprehensive data
    tasks = [
        api_get_merge_request_details(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_pipeline(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_changes(gitlab_url, project_id, access_token, mr_iid),
        get_merge_request_reviews(gitlab_url, project_id, access_token, mr_iid)
    ]
    
    try:
        details_result, pipeline_result, changes_result, reviews_result = await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"Error in parallel API calls: {e}")
        raise Exception(f"Error fetching merge request data: {e}")
    
    # Extract results
    mr_status, mr_data, mr_error = details_result
    pipeline_status, pipeline_data, pipeline_error = pipeline_result
    changes_status, changes_data, changes_error = changes_result
    
    # Check for errors in main MR data (most critical)
    if mr_status != 200:
        logging.error(f"Error fetching merge request details: {mr_status} - {mr_error}")
        raise Exception(f"Error fetching merge request details: {mr_status} - {mr_error}")
    
    # Start building enhanced output
    state_icon = "✅" if mr_data['state'] == 'merged' else "🔄" if mr_data['state'] == 'opened' else "❌"
    result = f"# {state_icon} Merge Request !{mr_data['iid']}: {mr_data['title']}\n\n"
    
    # Main overview section
    result += "## 📋 Overview\n"
    result += f"**👤 Author**: {mr_data['author']['name']} (@{mr_data['author']['username']})\n"
    result += f"**📊 Status**: {mr_data['state']} ({get_state_explanation(mr_data['state'])})\n"
    result += f"**🏷️ Priority**: {get_mr_priority(mr_data)}\n"
    result += f"**📅 Created**: {format_date(mr_data['created_at'])}\n"
    result += f"**🔄 Updated**: {format_date(mr_data['updated_at'])}\n"
    result += f"**🌿 Branches**: `{mr_data['source_branch']}` → `{mr_data['target_branch']}`\n"
    
    # Pipeline status with enhanced data
    if pipeline_status == 200 and pipeline_data:
        pipeline_icon = get_pipeline_status_icon(pipeline_data.get('status'))
        result += f"**🔧 Pipeline**: {pipeline_icon} {pipeline_data.get('status', 'unknown')}\n"
        if pipeline_data.get('web_url'):
            result += f"  *[View Pipeline]({pipeline_data['web_url']})*\n"
    elif mr_data.get('pipeline'):
        # Fallback to basic pipeline info from MR data
        pipeline_status = mr_data['pipeline'].get('status')
        pipeline_icon = get_pipeline_status_icon(pipeline_status)
        result += f"**🔧 Pipeline**: {pipeline_icon} {pipeline_status or 'unknown'}\n"
    
    # Changes statistics
    if changes_status == 200:
        change_stats = calculate_change_stats(changes_data)
        result += f"**📈 Changes**: {change_stats}\n"
    
    # Merge readiness analysis
    readiness = analyze_mr_readiness(mr_data, pipeline_data)
    result += f"**🚦 Merge Status**: {readiness}\n"
    
    # Labels with visual indicators
    if mr_data.get('labels'):
        labels_str = ', '.join(f"`{label}`" for label in mr_data['labels'])
        result += f"**🏷️ Labels**: {labels_str}\n"
    
    # Draft/WIP status
    if mr_data.get('draft') or mr_data.get('work_in_progress'):
        result += "**⚠️ Status**: 🚧 Draft/Work in Progress\n"
    
    # Merge conflicts warning
    if mr_data.get('has_conflicts'):
        result += "**⚠️ Warning**: 🔥 Has merge conflicts\n"
    
    result += f"**🔗 URL**: {mr_data['web_url']}\n\n"
    
    # Description section
    if mr_data.get('description'):
        result += "## 📝 Description\n"
        result += f"{mr_data['description']}\n\n"
    
    # Technical details section
    result += "## 🔧 Technical Details\n"
    
    # Merge commit info
    if mr_data.get('merge_commit_sha'):
        result += f"**📦 Merge Commit**: `{mr_data['merge_commit_sha'][:8]}`\n"
    
    if mr_data.get('squash_commit_sha'):
        result += f"**🔄 Squash Commit**: `{mr_data['squash_commit_sha'][:8]}`\n"
    
    # Merge options
    merge_options = []
    if mr_data.get('squash'):
        merge_options.append("🔄 Squash commits")
    if mr_data.get('remove_source_branch'):
        merge_options.append("🗑️ Remove source branch")
    if mr_data.get('force_remove_source_branch'):
        merge_options.append("🗑️ Force remove source branch")
    
    if merge_options:
        result += f"**⚙️ Merge Options**: {', '.join(merge_options)}\n"
    
    # Assignees and reviewers
    if mr_data.get('assignees'):
        assignees = ', '.join(f"@{user['username']}" for user in mr_data['assignees'])
        result += f"**👥 Assignees**: {assignees}\n"
    
    if mr_data.get('reviewers'):
        reviewers = ', '.join(f"@{user['username']}" for user in mr_data['reviewers'])
        result += f"**👀 Reviewers**: {reviewers}\n"
    
    # Milestone
    if mr_data.get('milestone'):
        result += f"**🎯 Milestone**: {mr_data['milestone']['title']}\n"
    
    result += "\n"
    
    # Reviews summary if available
    if reviews_result and 'discussions' in reviews_result:
        discussions_status, discussions, _ = reviews_result['discussions']
        approvals_status, approvals, _ = reviews_result['approvals']
        
        result += "## 💬 Reviews Summary\n"
        
        # Discussion counts
        if discussions_status == 200 and discussions:
            total_discussions = len(discussions)
            resolved_count = sum(1 for d in discussions if d.get('resolved'))
            unresolved_count = total_discussions - resolved_count
            
            result += f"**Discussions**: {total_discussions} total, {resolved_count} resolved, {unresolved_count} unresolved\n"
            
            if unresolved_count > 0:
                result += f"⚠️ **{unresolved_count} unresolved discussion{'s' if unresolved_count > 1 else ''}**\n"
        
        # Approval status
        if approvals_status == 200 and approvals:
            approved_by = approvals.get('approved_by', [])
            approvals_left = approvals.get('approvals_left', 0)
            
            if approved_by:
                result += f"**Approvals**: ✅ {len(approved_by)} approval{'s' if len(approved_by) > 1 else ''}\n"
            
            if approvals_left > 0:
                result += f"**Needed**: ⏳ {approvals_left} more approval{'s' if approvals_left > 1 else ''}\n"
        
        result += "\n"
    
    # Action items section
    result += "## 📊 Action Items\n"
    action_items = []
    
    # Check for merge blockers
    if mr_data.get('draft') or mr_data.get('work_in_progress'):
        action_items.append("🚧 Remove draft/WIP status")
    
    if mr_data.get('has_conflicts'):
        action_items.append("⚠️ Resolve merge conflicts")
    
    if pipeline_status == 200 and pipeline_data and pipeline_data.get('status') == 'failed':
        action_items.append("❌ Fix failing pipeline")
    elif pipeline_status == 200 and pipeline_data and pipeline_data.get('status') == 'running':
        action_items.append("🔄 Wait for pipeline completion")
    
    # Check reviews
    if reviews_result and 'discussions' in reviews_result:
        discussions_status, discussions, _ = reviews_result['discussions']
        approvals_status, approvals, _ = reviews_result['approvals']
        
        if discussions_status == 200 and discussions:
            unresolved_count = sum(1 for d in discussions if not d.get('resolved'))
            if unresolved_count > 0:
                action_items.append(f"💬 Resolve {unresolved_count} pending discussion{'s' if unresolved_count > 1 else ''}")
        
        if approvals_status == 200 and approvals and approvals.get('approvals_left', 0) > 0:
            action_items.append(f"👥 Obtain {approvals['approvals_left']} more approval{'s' if approvals['approvals_left'] > 1 else ''}")
    
    # Check if ready to merge
    if mr_data['state'] == 'opened' and not action_items:
        action_items.append("✅ Ready to merge!")
    
    if action_items:
        for item in action_items:
            result += f"• {item}\n"
    else:
        result += "✅ No action items identified\n"
    
    # Quick actions
    result += "\n## 🚀 Quick Actions\n"
    if mr_data['state'] == 'opened':
        result += f"• [📝 Edit MR]({mr_data['web_url']}/edit)\n"
        result += f"• [💬 Add Comment]({mr_data['web_url']}#note_form)\n"
        result += f"• [🔄 View Changes]({mr_data['web_url']}/diffs)\n"
        if pipeline_data and pipeline_data.get('web_url'):
            result += f"• [🔧 View Pipeline]({pipeline_data['web_url']})\n"
    
    return [TextContent(type="text", text=result)] 