"""
Tool Creation API Routes
Covers all of Phase 6.1:
  - Core: propose, vote, list tools
  - Versioning: propose update, approve update, rollback, diff, changelog
  - Deprecation: deprecate, schedule sunset, execute sunset, restore
  - Analytics: tool stats, full report, agent usage, recent errors
  - Marketplace: publish, browse, import, rate, yank, update listing

ROUTE ORDER RULE:
  Static routes (/deprecated, /analytics/*, /marketplace/*)
  must come BEFORE wildcard routes (/{tool_name}/*)
  or FastAPI will swallow them as tool_name values.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from backend.models.database import get_db
from backend.models.schemas.tool_creation import ToolCreationRequest
from backend.services.tool_creation_service import ToolCreationService
from backend.services.tool_versioning import ToolVersioningService
from backend.services.tool_deprecation import ToolDeprecationService
from backend.services.tool_analytics import ToolAnalyticsService
from backend.services.tool_marketplace import ToolMarketplaceService

router = APIRouter(prefix="/tools", tags=["Tool Creation - Phase 6.1"])


# ═══════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════════

class VoteRequest(BaseModel):
    voter_agentium_id: str
    vote: str  # "for", "against", "abstain"

class ProposeUpdateRequest(BaseModel):
    new_code: str
    change_summary: str
    proposed_by: str

class ApproveUpdateRequest(BaseModel):
    pending_version_id: str
    approved_by_voting_id: Optional[str] = None

class RollbackRequest(BaseModel):
    target_version_number: int
    requested_by: str
    reason: str

class DeprecateRequest(BaseModel):
    deprecated_by: str
    reason: str
    replacement_tool_name: Optional[str] = None
    sunset_days: Optional[int] = None

class ScheduleSunsetRequest(BaseModel):
    requested_by: str
    sunset_days: int

class ForceSunsetRequest(BaseModel):
    forced_by: str

class RestoreRequest(BaseModel):
    restored_by: str
    reason: str

class ExecuteToolRequest(BaseModel):
    called_by: str
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None

class PublishListingRequest(BaseModel):
    tool_name: str
    display_name: str
    category: str
    tags: List[str] = Field(default_factory=list)
    published_by: str

class ImportToolRequest(BaseModel):
    requested_by: str

class FinalizeImportRequest(BaseModel):
    staging_id: str

class RateToolRequest(BaseModel):
    rated_by: str
    rating: float  # 1.0 - 5.0

class YankListingRequest(BaseModel):
    yanked_by: str
    reason: str

class UpdateListingRequest(BaseModel):
    updated_by: str


# ═══════════════════════════════════════════════════════════════
# CORE — Propose, Vote, List
# ═══════════════════════════════════════════════════════════════

@router.post("/propose")
async def propose_tool(
    request: ToolCreationRequest,
    db: Session = Depends(get_db),
):
    """Agent proposes a new tool. Triggers vote or auto-approves (Head only)."""
    service = ToolCreationService(db)
    result = service.propose_tool(request)
    if not result.get("proposed") and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/")
async def list_tools(
    status: Optional[str] = None,
    authorized_for_tier: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all tools, optionally filtered by status or authorized tier."""
    service = ToolCreationService(db)
    return service.list_tools(status=status, authorized_for_tier=authorized_for_tier)


# ═══════════════════════════════════════════════════════════════
# DEPRECATION — static routes (must be before /{tool_name}/*)
# ═══════════════════════════════════════════════════════════════

@router.get("/deprecated")
async def list_deprecated(db: Session = Depends(get_db)):
    """List all deprecated and sunset tools."""
    service = ToolDeprecationService(db)
    return service.list_deprecated_tools()


@router.post("/run-sunset-cleanup")
async def run_sunset_cleanup(db: Session = Depends(get_db)):
    """
    Trigger sunset cleanup manually (normally run by Celery beat scheduler).
    Hard-removes all tools whose sunset_at has passed.
    """
    service = ToolDeprecationService(db)
    return service.run_sunset_cleanup()


# ═══════════════════════════════════════════════════════════════
# ANALYTICS — static routes (must be before /{tool_name}/*)
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics/report")
async def get_analytics_report(
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Full analytics report across all tools for the last N days."""
    service = ToolAnalyticsService(db)
    return service.get_full_report(days=days)


@router.get("/analytics/errors")
async def get_recent_errors(
    tool_name: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Recent failed tool calls, optionally filtered by tool name."""
    service = ToolAnalyticsService(db)
    return service.get_recent_errors(tool_name=tool_name, limit=limit)


@router.get("/analytics/agent/{agentium_id}")
async def get_agent_tool_usage(
    agentium_id: str,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Which tools has a specific agent been using?"""
    service = ToolAnalyticsService(db)
    return service.get_agent_tool_usage(agentium_id=agentium_id, days=days)


# ═══════════════════════════════════════════════════════════════
# MARKETPLACE — static routes (must be before /{tool_name}/*)
# ═══════════════════════════════════════════════════════════════

@router.post("/marketplace/publish")
async def publish_tool(
    body: PublishListingRequest,
    db: Session = Depends(get_db),
):
    """Publish an activated tool to the marketplace. Head/Council only."""
    service = ToolMarketplaceService(db)
    result = service.publish_tool(
        tool_name=body.tool_name,
        display_name=body.display_name,
        category=body.category,
        tags=body.tags,
        published_by=body.published_by,
    )
    if not result.get("published"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/marketplace")
async def browse_marketplace(
    category: Optional[str] = None,
    tags: Optional[str] = None,        # comma-separated
    search: Optional[str] = None,
    include_remote: bool = True,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """Browse marketplace listings with optional filters."""
    service = ToolMarketplaceService(db)
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    return service.browse_marketplace(
        category=category,
        tags=tag_list,
        search_query=search,
        include_remote=include_remote,
        page=page,
        page_size=page_size,
    )


@router.post("/marketplace/{listing_id}/import")
async def import_tool(
    listing_id: str,
    body: ImportToolRequest,
    db: Session = Depends(get_db),
):
    """
    Stage a marketplace tool for import.
    Returns an import_payload to submit via /tools/propose for Council vote.
    """
    service = ToolMarketplaceService(db)
    result = service.import_tool(listing_id=listing_id, requested_by=body.requested_by)
    if not result.get("staged"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/marketplace/{listing_id}/finalize-import")
async def finalize_import(
    listing_id: str,
    body: FinalizeImportRequest,        # ← fixed: was a loose query param before
    db: Session = Depends(get_db),
):
    """Mark a marketplace import as complete after Council approval."""
    service = ToolMarketplaceService(db)
    result = service.finalize_import(listing_id=listing_id, staging_id=body.staging_id)
    if not result.get("finalized"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/marketplace/{listing_id}/rate")
async def rate_tool(
    listing_id: str,
    body: RateToolRequest,
    db: Session = Depends(get_db),
):
    """Rate a marketplace tool listing (1.0 - 5.0)."""
    service = ToolMarketplaceService(db)
    result = service.rate_tool(
        listing_id=listing_id,
        rated_by=body.rated_by,
        rating=body.rating,
    )
    if not result.get("rated"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/marketplace/{listing_id}/yank")
async def yank_listing(
    listing_id: str,
    body: YankListingRequest,
    db: Session = Depends(get_db),
):
    """Retract a marketplace listing. Head or original publisher only."""
    service = ToolMarketplaceService(db)
    result = service.yank_listing(
        listing_id=listing_id,
        yanked_by=body.yanked_by,
        reason=body.reason,
    )
    if not result.get("yanked"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/marketplace/{tool_name}/update-listing")
async def update_listing(
    tool_name: str,
    body: UpdateListingRequest,
    db: Session = Depends(get_db),
):
    """Refresh a marketplace listing to the tool's current active version."""
    service = ToolMarketplaceService(db)
    result = service.update_listing(tool_name=tool_name, updated_by=body.updated_by)
    if not result.get("updated"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# ═══════════════════════════════════════════════════════════════
# WILDCARD ROUTES — /{tool_name}/* must come LAST
# ═══════════════════════════════════════════════════════════════

@router.post("/{tool_name}/vote")
async def vote_on_tool(
    tool_name: str,
    body: VoteRequest,
    db: Session = Depends(get_db),
):
    """Council member casts a vote on a pending tool proposal."""
    service = ToolCreationService(db)
    result = service.vote_on_tool(tool_name, body.voter_agentium_id, body.vote)
    if not result.get("voted"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    body: ExecuteToolRequest,
    db: Session = Depends(get_db),
):
    """Execute a registered tool. Automatically records usage analytics."""
    service = ToolCreationService(db)
    return service.execute_tool(tool_name, body.called_by, body.kwargs, body.task_id)


@router.get("/{tool_name}/analytics")
async def get_tool_analytics(
    tool_name: str,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Per-tool analytics: call counts, error rate, latency percentiles, top callers."""
    service = ToolAnalyticsService(db)
    return service.get_tool_stats(tool_name=tool_name, days=days)


@router.post("/{tool_name}/deprecate")
async def deprecate_tool(
    tool_name: str,
    body: DeprecateRequest,
    db: Session = Depends(get_db),
):
    """Soft-deprecate a tool. Still callable, but marked deprecated. Head/Council only."""
    service = ToolDeprecationService(db)
    result = service.deprecate_tool(
        tool_name=tool_name,
        deprecated_by=body.deprecated_by,
        reason=body.reason,
        replacement_tool_name=body.replacement_tool_name,
        sunset_days=body.sunset_days,
    )
    if not result.get("deprecated"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{tool_name}/schedule-sunset")
async def schedule_sunset(
    tool_name: str,
    body: ScheduleSunsetRequest,
    db: Session = Depends(get_db),
):
    """Schedule a hard-removal date for a tool (minimum 7 days). Head/Council only."""
    service = ToolDeprecationService(db)
    result = service.schedule_sunset(
        tool_name=tool_name,
        requested_by=body.requested_by,
        sunset_days=body.sunset_days,
    )
    if not result.get("scheduled"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{tool_name}/execute-sunset")
async def execute_sunset(
    tool_name: str,
    body: ForceSunsetRequest,
    db: Session = Depends(get_db),
):
    """Hard-remove a tool. Requires sunset date to have passed (or Head force)."""
    service = ToolDeprecationService(db)
    result = service.execute_sunset(
        tool_name=tool_name,
        forced_by=body.forced_by if body.forced_by else None,
    )
    if not result.get("executed"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{tool_name}/restore")
async def restore_tool(
    tool_name: str,
    body: RestoreRequest,
    db: Session = Depends(get_db),
):
    """Restore a deprecated tool back to active. Head/Council only."""
    service = ToolDeprecationService(db)
    result = service.restore_tool(
        tool_name=tool_name,
        restored_by=body.restored_by,
        reason=body.reason,
    )
    if not result.get("restored"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{tool_name}/versions/propose-update")
async def propose_tool_update(
    tool_name: str,
    body: ProposeUpdateRequest,
    db: Session = Depends(get_db),
):
    """Propose a code update to an existing tool (creates a pending version)."""
    service = ToolVersioningService(db)
    result = service.propose_update(
        tool_name=tool_name,
        new_code=body.new_code,
        change_summary=body.change_summary,
        proposed_by=body.proposed_by,
    )
    if not result.get("proposed"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{tool_name}/versions/approve-update")
async def approve_tool_update(
    tool_name: str,
    body: ApproveUpdateRequest,
    db: Session = Depends(get_db),
):
    """Approve and activate a pending tool version (post-vote or Head auto-approve)."""
    service = ToolVersioningService(db)
    result = service.approve_update(
        tool_name=tool_name,
        pending_version_id=body.pending_version_id,
        approved_by_voting_id=body.approved_by_voting_id,
    )
    if not result.get("approved"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{tool_name}/versions/rollback")
async def rollback_tool(
    tool_name: str,
    body: RollbackRequest,
    db: Session = Depends(get_db),
):
    """Roll back a tool to a specific prior version. Head/Council only."""
    service = ToolVersioningService(db)
    result = service.rollback(
        tool_name=tool_name,
        target_version_number=body.target_version_number,
        requested_by=body.requested_by,
        reason=body.reason,
    )
    if not result.get("rolled_back"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/{tool_name}/versions/changelog")
async def get_changelog(
    tool_name: str,
    db: Session = Depends(get_db),
):
    """Get full version history and changelog for a tool."""
    service = ToolVersioningService(db)
    return service.get_changelog(tool_name)


@router.get("/{tool_name}/versions/diff")
async def get_version_diff(
    tool_name: str,
    version_a: int,
    version_b: int,
    db: Session = Depends(get_db),
):
    """Get a unified diff between two versions of a tool."""
    service = ToolVersioningService(db)
    result = service.get_diff(tool_name, version_a, version_b)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result