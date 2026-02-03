from fastapi import APIRouter, Depends, HTTPException
from backend.core.tool_registry import tool_registry
from backend.core.auth import get_current_agent_tier

router = APIRouter(prefix="/tools", tags=["Tools"])

@router.get("/")
async def list_tools(agent_tier: str = Depends(get_current_agent_tier)):
    """List tools available to the authenticated agent."""
    return {"agent_tier": agent_tier, "tools": tool_registry.list_tools(agent_tier)}

@router.post("/execute")
async def execute_tool(
    tool_name: str,
    params: dict,
    agent_tier: str = Depends(get_current_agent_tier)
):
    """Execute a tool with parameters."""
    # Check authorization
    tool = tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if agent_tier not in tool["authorized_tiers"]:
        raise HTTPException(status_code=403, detail="Not authorized for this tool")
    
    # Execute
    result = tool_registry.execute_tool(tool_name, **params)
    return result