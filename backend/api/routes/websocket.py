"""
WebSocket endpoint for real-time chat with authentication.
User must authenticate BEFORE or DURING connection.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities import Agent, HeadOfCouncil
from backend.services.chat_service import ChatService
from backend.core.config import settings

router = APIRouter()

class ConnectionManager:
    """Manage authenticated WebSocket connections."""
    def __init__(self):
        # Map: websocket -> user_info
        self.active_connections: dict = {}
        # Map: user_id -> websocket (for direct messaging)
        self.user_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, token: str, db: Session):
        """
        Authenticate connection BEFORE accepting.
        Returns user info if successful, raises exception if not.
        """
        try:
            # Verify JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            username = payload.get("sub")
            
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Check if Head of Council exists
            head = db.query(HeadOfCouncil).filter_by(agentium_id="00001").first()
            if not head:
                raise HTTPException(status_code=503, detail="System not initialized")
            
            # Accept connection
            await websocket.accept()
            
            # Store connection info
            user_info = {
                "username": username,
                "role": payload.get("role", "sovereign"),
                "head_agent_id": head.id,
                "head_agentium_id": head.agentium_id
            }
            
            self.active_connections[websocket] = user_info
            self.user_connections[username] = websocket
            
            print(f"WebSocket authenticated: {username}")
            return user_info
            
        except JWTError:
            # Reject connection
            await websocket.close(code=4001, reason="Invalid authentication")
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def disconnect(self, websocket: WebSocket):
        """Remove connection."""
        if websocket in self.active_connections:
            user_info = self.active_connections[websocket]
            if user_info["username"] in self.user_connections:
                del self.user_connections[user_info["username"]]
            del self.active_connections[websocket]
    
    async def send_personal_message(self, message: str, username: str):
        """Send message to specific user."""
        if username in self.user_connections:
            websocket = self.user_connections[username]
            await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast to all authenticated connections."""
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str | None = None,  # Pass token as query param: ws://localhost:8000/ws/chat?token=xyz
    db: Session = Depends(get_db)
):
    """
    Authenticated WebSocket endpoint for Sovereign ↔ Head of Council chat.
    
    Connection flow:
    1. Client connects with ?token=JWT in URL
    2. Server validates JWT BEFORE accepting
    3. If valid: connection accepted, can send/receive
    4. If invalid: connection rejected with 4001 code
    """
    
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    try:
        # Authenticate BEFORE accepting
        user_info = await manager.connect(websocket, token, db)
        
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "content": f"Welcome {user_info['username']}. Connected to Head of Council ({user_info['head_agentium_id']}).",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send any pending messages or status
        await websocket.send_json({
            "type": "status",
            "content": "Head of Council is ready to receive commands.",
            "agent_id": user_info['head_agentium_id']
        })
        
    except HTTPException:
        return  # Already closed by connect()
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))
        return
    
    # Handle messages
    try:
        while True:
            # Receive message from client (Sovereign)
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                content = message_data.get("content", "")
                
                if not content:
                    continue
                
                # Acknowledge receipt
                await websocket.send_json({
                    "type": "status",
                    "content": "Processing your command..."
                })
                
                # Get Head of Council
                head = db.query(HeadOfCouncil).filter_by(
                    id=user_info["head_agent_id"]
                ).first()
                
                # Process message (async)
                response = await ChatService.process_message(head, content, db)
                
                # Send response
                await websocket.send_json({
                    "type": "message",
                    "role": "head_of_council",
                    "content": response["content"],
                    "metadata": {
                        "agent_id": user_info['head_agentium_id'],
                        "model": response.get("model"),
                        "task_created": response.get("task_created"),
                        "task_id": response.get("task_id")
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Broadcast to other connections (if multi-device)
                # await manager.broadcast(f"New command from {user_info['username']}")
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid message format"
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error processing message: {str(e)}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"WebSocket disconnected: {user_info.get('username', 'unknown')}")
    
    except Exception as e:
        manager.disconnect(websocket)
        print(f"WebSocket error: {e}")

import json
from datetime import datetime