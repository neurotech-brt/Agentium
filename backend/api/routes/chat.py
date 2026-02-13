"""
Chat API for Sovereign to communicate with Head of Council.
Supports streaming responses for real-time communication.
"""
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities import Agent, HeadOfCouncil, Task
from backend.services.chat_service import ChatService
from backend.services.model_provider import ModelService

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatMessage(BaseModel):
    message: str
    stream: bool = True

class ChatResponse(BaseModel):
    response: str
    agent_id: str
    task_created: bool = False
    task_id: str = None

@router.post("/send", response_class=StreamingResponse)
async def send_message(
    chat_msg: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    Send message to Head of Council (00001).
    Returns streaming response for real-time updates.
    """
    # Get Head of Council
    head = db.query(HeadOfCouncil).filter_by(agentium_id="00001").first()
    
    if not head:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Head of Council not initialized"
        )
    
    if head.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Head of Council is {head.status.value}"
        )
    
    # Check if we should stream
    if chat_msg.stream:
        return StreamingResponse(
            _stream_response(head.agentium_id, chat_msg.message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # Non-streaming response
        response = await ChatService.process_message(head, chat_msg.message, db)
        return ChatResponse(
            response=response["content"],
            agent_id=head.agentium_id,
            task_created=response.get("task_created", False),
            task_id=response.get("task_id")
        )

async def _stream_response(
    agent_id: str, 
    message: str
) -> AsyncGenerator[str, None]:
    """
    Stream response from Head of Council.
    Format: SSE (Server-Sent Events)
    """
    from backend.models.database import SessionLocal
    from sqlalchemy.exc import DetachedInstanceError
    
    # Create a fresh session for the streaming context
    db = SessionLocal()
    try:
        # Re-fetch head with new session
        head = db.query(HeadOfCouncil).filter_by(agentium_id=agent_id).first()
        if not head:
            yield f"data: {json.dumps({'type': 'error', 'content': 'System Error: Head of Council agent not found.'})}\n\n"
            return

        # Send initial "thinking" event
        yield f"data: {json.dumps({'type': 'status', 'content': 'Head of Council is deliberating...'})}\n\n"
        
        # Safe config retrieval with error handling
        try:
            config = head.get_model_config(db)
            if not config:
                raise ValueError("No active model configuration found")
            
            # Pre-fetch config details to avoid detachment later
            config_id = config.id
            model_name = config.default_model
            
            # Verify provider availability
            provider = await ModelService.get_provider("sovereign", config_id)
            if not provider:
                raise ValueError("Could not initialize AI provider")
                
        except (ValueError, DetachedInstanceError, AttributeError) as e:
            # FRIENDLY ERROR MESSAGE
            error_msg = (
                "System Operational Warning: \n\n"
                "The Head of Council cannot be reached because no AI Model is currently connected. \n\n"
                "Please go to the 'Models' page and connect a provider (e.g., OpenAI, Anthropic, or Local) "
                "to initialize the system."
            )
            yield f"data: {json.dumps({'type': 'content', 'content': error_msg})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return
        
        # Build system prompt from ethos
        system_prompt = head.get_system_prompt()
        
        # Add context about available agents
        context = await ChatService.get_system_context(db)
        full_prompt = f"""{system_prompt}

Current System State:
{context}

You are speaking directly to the Sovereign. Address them respectfully and provide clear, actionable responses."""

        # Stream the response
        full_response = []
        
        # Using the provider (which might use async http clients)
        async for chunk in provider.stream_generate(full_prompt, message):
            full_response.append(chunk)
            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
        
        # Check if this should create a task
        full_text = "".join(full_response)
        task_info = await ChatService.analyze_for_task(head, message, full_text, db)
        
        # Send completion event with metadata
        yield f"""data: {json.dumps({
            'type': 'complete',
            'content': '',
            'metadata': {
                'agent_id': head.agentium_id,
                'model': model_name,
                'task_created': task_info['created'],
                'task_id': task_info.get('task_id')
            }
        })}\n\n"""
        
        # Log the interaction
        await ChatService.log_interaction(
            head.agentium_id,
            message,
            full_text,
            config_id,
            db
        )
        
    except Exception as e:
        print(f"Streaming error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': 'An unexpected error occurred during processing.'})}\n\n"
    finally:
        db.close()
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get chat history with Head of Council."""
    from backend.models.entities.audit import AuditLog
    
    logs = db.query(AuditLog).filter(
        AuditLog.actor_id == "00001",
        AuditLog.action == "chat_response"
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return {
        "messages": [
            {
                "id": log.id,
                "role": "head_of_council",
                "content": log.after_state.get("response") if log.after_state else "",
                "timestamp": log.created_at.isoformat(),
                "metadata": {
                    "prompt": log.before_state.get("prompt") if log.before_state else ""
                }
            }
            for log in reversed(logs)
        ]
    }

import json
