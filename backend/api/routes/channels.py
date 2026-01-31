"""
Channel management API for frontend.
CRUD operations for external channel configurations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities.channels import ExternalChannel, ExternalMessage, ChannelType, ChannelStatus
from backend.models.entities.agents import Agent

router = APIRouter(prefix="/channels", tags=["Channels"])

class ChannelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    channel_type: ChannelType
    config: dict = Field(default_factory=dict)
    default_agent_id: Optional[str] = None
    auto_create_tasks: bool = True
    require_approval: bool = False

class ChannelResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    config: dict
    routing: dict
    stats: dict

@router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: ChannelCreate,
    db: Session = Depends(get_db)
):
    """Create new channel configuration."""
    import secrets
    
    # Generate unique webhook path
    webhook_path = secrets.token_urlsafe(16)
    
    channel = ExternalChannel(
        name=channel_data.name,
        channel_type=channel_data.channel_type,
        status=ChannelStatus.PENDING,
        config=channel_data.config,
        default_agent_id=channel_data.default_agent_id,
        auto_create_tasks=channel_data.auto_create_tasks,
        require_approval=channel_data.require_approval,
        webhook_path=webhook_path
    )
    
    db.add(channel)
    db.commit()
    db.refresh(channel)
    
    return channel.to_dict()

@router.get("/", response_model=List[ChannelResponse])
async def list_channels(db: Session = Depends(get_db)):
    """List all configured channels."""
    channels = db.query(ExternalChannel).all()
    return [c.to_dict() for c in channels]

@router.get("/{channel_id}")
async def get_channel(channel_id: str, db: Session = Depends(get_db)):
    """Get channel details."""
    channel = db.query(ExternalChannel).filter_by(id=channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel.to_dict()

@router.get("/{channel_id}/messages")
async def get_channel_messages(
    channel_id: str,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get messages for a channel (Unified Inbox view)."""
    query = db.query(ExternalMessage).filter_by(channel_id=channel_id)
    
    if status:
        query = query.filter_by(status=status)
    
    messages = query.order_by(ExternalMessage.created_at.desc()).limit(limit).all()
    return {
        "messages": [m.to_dict() for m in messages],
        "count": len(messages)
    }

@router.get("/messages/all")
async def get_all_messages(
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all messages across all channels (Unified Inbox)."""
    query = db.query(ExternalMessage)
    
    if status:
        query = query.filter_by(status=status)
    
    messages = query.order_by(ExternalMessage.created_at.desc()).limit(limit).all()
    return {
        "messages": [m.to_dict() for m in messages],
        "count": len(messages)
    }

@router.post("/{channel_id}/activate")
async def activate_channel(
    channel_id: str,
    credentials: dict,
    db: Session = Depends(get_db)
):
    """Activate channel with credentials (update from Pending to Active)."""
    channel = db.query(ExternalChannel).filter_by(id=channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Validate credentials (e.g., test API call)
    # TODO: Implement validation per channel type
    
    # Merge new credentials with existing config
    channel.config.update(credentials)
    channel.status = ChannelStatus.ACTIVE
    db.commit()
    
    return {"status": "activated", "webhook_url": channel.generate_webhook_url("https://your-domain.com")}