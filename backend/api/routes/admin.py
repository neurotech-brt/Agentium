"""
Admin API for system configuration.
Only accessible by Head of Council (00001).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from backend.models.database import get_db
from backend.core.auth import get_current_agent
from backend.models.entities.agents import Agent
from backend.services.token_optimizer import idle_budget, token_optimizer

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

class BudgetUpdateRequest(BaseModel):
    daily_token_limit: int = 100000
    daily_cost_limit: float = 5.0

@router.post("/budget")
async def update_budget(
    request: BudgetUpdateRequest,
    db: Session = Depends(get_db),
    agent: Agent = Depends(get_current_agent)
) -> Dict[str, Any]:
    """
    Update daily budget limits. Only Head of Council (00001) can modify.
    """
    # Authorization check - Only Head can modify
    if not agent.agentium_id.startswith('0'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Head of Council (0xxxx) can modify system budget"
        )
    
    # Validate inputs
    if request.daily_token_limit < 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token limit must be at least 1,000"
        )
    
    if request.daily_cost_limit < 0.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cost limit cannot be negative"
        )
    
    if request.daily_cost_limit > 1000.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cost limit cannot exceed $1,000/day"
        )
    
    # Update the singleton instance
    idle_budget.daily_token_limit = request.daily_token_limit
    idle_budget.daily_cost_limit = request.daily_cost_limit
    
    # Log the change (in production, save to DB for persistence)
    try:
        from backend.models.entities.audit import AuditLog, AuditLevel, AuditCategory
        audit = AuditLog(
            level=AuditLevel.INFO,
            category=AuditCategory.GOVERNANCE,
            actor_type="agent",
            actor_id=agent.agentium_id,
            action="budget_updated",
            description=f"Budget updated to ${request.daily_cost_limit}/day, {request.daily_token_limit:,} tokens",
            after_state={
                "daily_token_limit": request.daily_token_limit,
                "daily_cost_limit": request.daily_cost_limit,
                "updated_by": agent.agentium_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        db.add(audit)
        db.commit()
    except:
        pass  # Don't fail if audit logging fails
    
    return {
        "success": True,
        "message": "Budget updated successfully",
        "new_budget": {
            "daily_token_limit": idle_budget.daily_token_limit,
            "daily_cost_limit": idle_budget.daily_cost_limit
        },
        "changed_by": agent.agentium_id
    }

@router.get("/budget")
async def get_current_budget(
    agent: Agent = Depends(get_current_agent)
) -> Dict[str, Any]:
    """
    Get current budget status. Accessible by all authenticated agents.
    """
    # Get real-time status
    status = idle_budget.get_status()
    
    return {
        "current_limits": {
            "daily_token_limit": status["daily_token_limit"],
            "daily_cost_limit": status["daily_cost_limit_usd"]
        },
        "usage": status,
        "can_modify": agent.agentium_id.startswith('0'),  # Only Head can modify
        "optimizer_status": token_optimizer.get_status()
    }