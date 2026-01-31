"""
Secure webhook endpoints with signature verification.
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import json

from backend.models.database import get_db
from backend.models.entities.channels import ExternalChannel, ChannelStatus
from backend.services.channel_manager import ChannelManager, WhatsAppAdapter, SlackAdapter
from backend.core.auth import WebhookAuth
from backend.core.security import decrypt_api_key

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

async def get_channel_by_path(
    channel_type: str,
    webhook_path: str,
    db: Session = Depends(get_db)
) -> ExternalChannel:
    """Get channel by webhook path."""
    channel = db.query(ExternalChannel).filter_by(
        channel_type=channel_type,
        webhook_path=webhook_path,
        status=ChannelStatus.ACTIVE
    ).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found or inactive")
    
    return channel

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WhatsApp Webhook (Secured)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/whatsapp/{webhook_path}")
async def whatsapp_verify(
    webhook_path: str,
    request: Request,
    channel: ExternalChannel = Depends(get_channel_by_path)
):
    """
    WhatsApp verification endpoint (GET).
    Meta sends challenge here to verify webhook.
    """
    params = dict(request.query_params)
    
    if params.get("hub.verify_token") == channel.config.get("verify_token"):
        return int(params.get("hub.challenge", 0))
    
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp/{webhook_path}")
async def whatsapp_webhook(
    webhook_path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    channel: ExternalChannel = Depends(get_channel_by_path),
    db: Session = Depends(get_db)
):
    """
    Receive WhatsApp messages with signature verification.
    """
    # Verify signature if app_secret is configured
    if channel.config.get('app_secret'):
        is_valid = await WebhookAuth.verify_whatsapp(request, channel.config)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Re-read body (consumed by auth check)
    body = await request.body()
    
    try:
        payload = json.loads(body)
        parsed = WhatsAppAdapter.parse_webhook(payload)
        
        # Process in background
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
# Slack Webhook (Secured)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/slack/{webhook_path}")
async def slack_webhook(
    webhook_path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    channel: ExternalChannel = Depends(get_channel_by_path),
    db: Session = Depends(get_db)
):
    """Receive Slack events with signature verification."""
    
    # Verify Slack signature
    if channel.config.get('signing_secret'):
        body = await request.body()
        signature = request.headers.get("X-Slack-Signature")
        timestamp = request.headers.get("X-Slack-Request-Timestamp")
        
        from backend.core.security import decrypt_api_key
        signing_secret = decrypt_api_key(channel.config['signing_secret'])
        
        from backend.core.auth import verify_slack_signature
        if not verify_slack_signature(body, signature, timestamp, signing_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        payload = json.loads(body)
    else:
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
# Telegram Webhook (Path-based security)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/telegram/{webhook_path}")
async def telegram_webhook(
    webhook_path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    channel: ExternalChannel = Depends(get_channel_by_path),
    db: Session = Depends(get_db)
):
    """
    Receive Telegram updates.
    Security is path-based (secret token in URL).
    """
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