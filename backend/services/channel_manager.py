"""
Channel Manager - Routes external messages to appropriate agents.
"""

import secrets
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.models.database import get_db_context
from backend.models.entities.channels import ExternalChannel, ExternalMessage, ChannelType, ChannelStatus
from backend.models.entities import Agent, HeadOfCouncil, Task, TaskType, TaskPriority
from backend.models.entities.audit import AuditLog, AuditLevel, AuditCategory
from backend.services.model_provider import ModelService

class ChannelManager:
    """
    Central router for all external channel communications.
    Receives webhooks, creates tasks, sends responses.
    """
    
    @staticmethod
    async def receive_message(
        channel_id: str,
        sender_id: str,
        sender_name: Optional[str],
        content: str,
        message_type: str = "text",
        media_url: Optional[str] = None,
        raw_payload: Optional[Dict] = None,
        db: Session = None
    ) -> ExternalMessage:
        """
        Process incoming message from any channel.
        Creates ExternalMessage record and optionally creates Task.
        """
        if db is None:
            with get_db_context() as db:
                return await ChannelManager._process_message(
                    channel_id, sender_id, sender_name, content,
                    message_type, media_url, raw_payload, db
                )
        else:
            return await ChannelManager._process_message(
                channel_id, sender_id, sender_name, content,
                message_type, media_url, raw_payload, db
            )
    
    @staticmethod
    async def _process_message(
        channel_id: str,
        sender_id: str,
        sender_name: Optional[str],
        content: str,
        message_type: str,
        media_url: Optional[str],
        raw_payload: Optional[Dict],
        db: Session
    ) -> ExternalMessage:
        """Internal processing logic."""
        
        # Get channel
        channel = db.query(ExternalChannel).filter_by(id=channel_id).first()
        if not channel or channel.status != ChannelStatus.ACTIVE:
            raise ValueError(f"Channel {channel_id} not found or inactive")
        
        # Create message record
        message = ExternalMessage(
            channel_id=channel_id,
            sender_id=sender_id,
            sender_name=sender_name or sender_id,
            content=content,
            message_type=message_type,
            media_url=media_url,
            raw_payload=raw_payload,
            status="received"
        )
        
        db.add(message)
        channel.messages_received += 1
        channel.last_message_at = datetime.utcnow()
        db.commit()
        db.refresh(message)
        
        # Log receipt
        AuditLog.log(
            level=AuditLevel.INFO,
            category=AuditCategory.COMMUNICATION,
            actor_type="system",
            actor_id="CHANNEL_ROUTER",
            action="external_message_received",
            target_type="external_message",
            target_id=message.id,
            description=f"Received {channel.channel_type.value} message from {sender_id}",
            metadata={
                'channel_type': channel.channel_type.value,
                'channel_name': channel.name,
                'sender': sender_id
            }
        )
        db.commit()
        
        # Auto-create task if enabled
        if channel.auto_create_tasks:
            await ChannelManager._create_task_for_message(message, channel, db)
        
        return message
    
    @staticmethod
    async def _create_task_for_message(
        message: ExternalMessage,
        channel: ExternalChannel,
        db: Session
    ):
        """Create a task from external message and route to agents."""
        
        # Determine which agent handles this
        if channel.default_agent_id:
            assigned_agent = db.query(Agent).filter_by(id=channel.default_agent_id).first()
        else:
            # Default to Head of Council
            assigned_agent = db.query(HeadOfCouncil).first()
        
        if not assigned_agent:
            message.last_error = "No agent available to handle message"
            message.error_count += 1
            db.commit()
            return
        
        # Create task
        task = Task(
            title=f"{channel.name}: {message.content[:50]}...",
            description=f"""External message from {channel.channel_type.value} ({message.sender_id}):

{message.content}

[Channel: {channel.name} | Sender: {message.sender_name or message.sender_id}]""",
            task_type=TaskType.EXECUTION,
            priority=TaskPriority.HIGH if channel.require_approval else TaskPriority.NORMAL,
            created_by=f"channel:{channel.id}",
            head_of_council_id=assigned_agent.id if assigned_agent.agent_type.value == "head_of_council" else None,
            requires_deliberation=channel.require_approval
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Link message to task
        message.task_id = task.id
        message.mark_processing(assigned_agent.id)
        db.commit()
        
        # If urgent/high priority, notify immediately
        if channel.require_approval:
            # This would trigger WebSocket notification to frontend
            pass
    
    @staticmethod
    async def send_response(
        message_id: str,
        response_content: str,
        agent_id: str,
        db: Session = None
    ) -> bool:
        """
        Send response back to external channel.
        Called when agent completes task.
        """
        if db is None:
            with get_db_context() as db:
                return await ChannelManager._send_response(message_id, response_content, agent_id, db)
        else:
            return await ChannelManager._send_response(message_id, response_content, agent_id, db)
    
    @staticmethod
    async def _send_response(
        message_id: str,
        response_content: str,
        agent_id: str,
        db: Session
    ) -> bool:
        """Send response via appropriate channel adapter."""
        message = db.query(ExternalMessage).filter_by(id=message_id).first()
        if not message:
            return False
        
        channel = message.channel
        
        # Route to appropriate adapter
        success = False
        try:
            if channel.channel_type == ChannelType.WHATSAPP:
                success = await WhatsAppAdapter.send_message(
                    channel.config,
                    message.sender_id,
                    response_content
                )
            elif channel.channel_type == ChannelType.SLACK:
                success = await SlackAdapter.send_message(
                    channel.config,
                    message.sender_id,
                    response_content
                )
            elif channel.channel_type == ChannelType.TELEGRAM:
                success = await TelegramAdapter.send_message(
                    channel.config,
                    message.sender_id,
                    response_content
                )
            elif channel.channel_type == ChannelType.EMAIL:
                success = await EmailAdapter.send_message(
                    channel.config,
                    message.sender_id,
                    response_content,
                    subject=f"Re: {message.content[:30]}..."
                )
            
            if success:
                message.mark_responded(response_content, agent_id)
                
                AuditLog.log(
                    level=AuditLevel.INFO,
                    category=AuditCategory.COMMUNICATION,
                    actor_type="agent",
                    actor_id=agent_id,
                    action="external_response_sent",
                    target_type="external_message",
                    target_id=message_id,
                    description=f"Response sent via {channel.channel_type.value}",
                    metadata={
                        'channel': channel.name,
                        'recipient': message.sender_id,
                        'response_length': len(response_content)
                    }
                )
                db.commit()
            else:
                message.error_count += 1
                message.last_error = "Failed to send via channel adapter"
                db.commit()
                
        except Exception as e:
            message.error_count += 1
            message.last_error = str(e)
            db.commit()
            raise
        
        return success


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Channel Adapters (Implementations)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WhatsAppAdapter:
    """WhatsApp Business API integration."""
    
    @staticmethod
    async def send_message(config: Dict, recipient: str, content: str) -> bool:
        """
        Send WhatsApp message via WhatsApp Business API.
        Requires: phone_number_id, access_token
        """
        import httpx
        
        phone_number_id = config.get('phone_number_id')
        access_token = config.get('access_token')
        
        if not phone_number_id or not access_token:
            raise ValueError("WhatsApp not configured: missing phone_number_id or access_token")
        
        url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"body": content[:4096]}  # WhatsApp limit
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return True
            else:
                raise Exception(f"WhatsApp API error: {response.text}")
    
    @staticmethod
    def parse_webhook(payload: Dict) -> Dict[str, Any]:
        """Parse incoming WhatsApp webhook payload."""
        try:
            entry = payload.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [{}])[0]
            
            return {
                'sender_id': messages.get('from'),
                'sender_name': value.get('contacts', [{}])[0].get('profile', {}).get('name'),
                'content': messages.get('text', {}).get('body', ''),
                'message_type': messages.get('type', 'text'),
                'media_url': None,  # Extract if media type
                'raw_payload': payload
            }
        except Exception as e:
            raise ValueError(f"Failed to parse WhatsApp webhook: {e}")


class SlackAdapter:
    """Slack Bot integration."""
    
    @staticmethod
    async def send_message(config: Dict, channel_id: str, content: str) -> bool:
        """Send Slack message via Bot API."""
        import httpx
        
        bot_token = config.get('bot_token')
        if not bot_token:
            raise ValueError("Slack not configured: missing bot_token")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                json={
                    "channel": channel_id,
                    "text": content[:4000],  # Slack rough limit
                    "parse": "full"
                },
                headers={"Authorization": f"Bearer {bot_token}"}
            )
            
            data = response.json()
            if data.get('ok'):
                return True
            else:
                raise Exception(f"Slack API error: {data.get('error')}")
    
    @staticmethod
    def parse_webhook(payload: Dict) -> Dict[str, Any]:
        """Parse Slack event webhook."""
        event = payload.get('event', {})
        
        return {
            'sender_id': event.get('user'),
            'sender_name': None,  # Would need user lookup
            'content': event.get('text', ''),
            'message_type': 'text',
            'channel_id': event.get('channel'),
            'raw_payload': payload
        }


class TelegramAdapter:
    """Telegram Bot integration."""
    
    @staticmethod
    async def send_message(config: Dict, chat_id: str, content: str) -> bool:
        """Send Telegram message."""
        import httpx
        
        bot_token = config.get('bot_token')
        if not bot_token:
            raise ValueError("Telegram not configured: missing bot_token")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": content[:4096],  # Telegram limit
                    "parse_mode": "Markdown"
                }
            )
            
            if response.json().get('ok'):
                return True
            else:
                raise Exception(f"Telegram API error: {response.text}")


class EmailAdapter:
    """Email SMTP integration."""
    
    @staticmethod
    async def send_message(config: Dict, to_email: str, content: str, subject: str = "Response") -> bool:
        """Send email via SMTP."""
        import aiosmtplib
        from email.mime.text import MIMEText
        
        smtp_host = config.get('smtp_host')
        smtp_port = config.get('smtp_port', 587)
        smtp_user = config.get('smtp_user')
        smtp_pass = config.get('smtp_pass')
        from_email = config.get('from_email', smtp_user)
        
        if not all([smtp_host, smtp_user, smtp_pass]):
            raise ValueError("Email not configured: missing SMTP settings")
        
        msg = MIMEText(content)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        try:
            await aiosmtplib.send(
                msg,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_pass,
                start_tls=True
            )
            return True
        except Exception as e:
            raise Exception(f"SMTP error: {e}")