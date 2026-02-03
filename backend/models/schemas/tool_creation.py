from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None

class ToolCreationRequest(BaseModel):
    tool_name: str = Field(..., description="Unique name for the new tool")
    description: str = Field(..., description="What the tool does")
    parameters: List[ToolParameter]
    code_template: str = Field(..., description="Python code implementing the tool")
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    authorized_tiers: List[str] = Field(default_factory=lambda: ["0xxxx"])  # Default: Head only
    created_by_agentium_id: str
    rationale: str = Field(..., description="Why this tool is needed")

class ToolApprovalRequest(BaseModel):
    tool_name: str
    proposed_by_agentium_id: str
    requires_vote: bool = False
    council_member_ids: List[str] = Field(default_factory=list)