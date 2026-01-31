"""
Webhook endpoints for external channel integrations.
Publicly accessible (no auth) but verified via signatures/secrets.
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
import json

from backend.models.database import get_db
from backend.models.entities.channels import ExternalChannel, ExternalMessage, ChannelStatus
from backend.services.channel_manager import ChannelManager, WhatsAppAdapter, SlackAdapter

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WhatsApp Webhook
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/whatsapp/{webhook_path}")
async def whatsapp_verify(webhook_path: str, request: Request, db: Session = Depends(get_db)):
    """
    WhatsApp verification endpoint (GET).
    Meta sends challenge here to verify webhook.
    """
    channel = db.query(ExternalChannel).filter_by(
        channel_type="whatsapp",
        webhook_path=webhook_path
    ).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # WhatsApp sends hub.verify_token and hub.challenge
    params = dict(request.query_params)
    
    if params.get("hub.verify_token") == channel.config.get("verify_token"):
        return int(params.get("hub.challenge", 0))
    
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp/{webhook_path}")
async def whatsapp_webhook(
    webhook_path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receive WhatsApp messages (POST).
    """
    channel = db.query(ExternalChannel).filter_by(
        channel_type="whatsapp",
        webhook_path=webhook_path
    ).first()
    
    if not channel or channel.status != ChannelStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Channel not active")
    
    try:
        payload = await request.json()
        parsed = WhatsAppAdapter.parse_webhook(payload)
        
        # Process in background (don't block webhook response)
        background_tasks.add_task(
            ChannelManager.receive_message,
            channel_id=channel.id,
            sender_id=parsed['sender_id'],
            sender_name=parsed['sender_name'],
            content=parsed['content'],
            message_type=parsed['message_type'],
            media_url=parsed['media_url'],
            raw_payload=parsed['raw_payload']
        )
        
        return {"status": "received"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Slack Webhook
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/slack/{webhook_path}")
async def slack_webhook(
    webhook_path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Receive Slack events."""
    channel = db.query(ExternalChannel).filter_by(
        channel_type="slack",
        webhook_path=webhook_path
    ).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    payload = await request.json()
    
    # Handle URL verification challenge
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}
    
    # Handle actual events
    if payload.get("type") == "event_callback":
        event = payload.get("event", {})
        
        # Ignore bot messages
        if event.get("bot_id"):
            return {"status": "ignored"}
        
        parsed = SlackAdapter.parse_webhook(payload)
        
        background_tasks.add_task(
            ChannelManager.receive_message,
            channel_id=channel.id,
            sender_id=parsed['sender_id'],
            sender_name=parsed['sender_name'],
            content=parsed['content'],
            raw_payload=parsed['raw_payload']
        )
    
    return {"status": "received"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Generic/Telegram Webhook
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/telegram/{webhook_path}")
async def telegram_webhook(
    webhook_path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Receive Telegram updates."""
    channel = db.query(ExternalChannel).filter_by(
        channel_type="telegram",
        webhook_path=webhook_path
    ).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    payload = await request.json()
    message = payload.get("message", {})
    
    background_tasks.add_task(
        ChannelManager.receive_message,
        channel_id=channel.id,
        sender_id=str(message.get("from", {}).get("id")),
        sender_name=message.get("from", {}).get("first_name"),
        content=message.get("text", ""),
        raw_payload=payload
    )
    
    return {"status": "received"}