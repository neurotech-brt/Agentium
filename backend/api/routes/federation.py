"""
Federation API Routes
Endpoints for managing peer instances and cross-instance communication.
"""
from typing import List, Dict, Any

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.federation_service import FederationService
from backend.api.routes.rbac import get_current_user_from_token
from backend.models.entities.user import User

router = APIRouter(prefix="/federation", tags=["Federation"])


# --- Schemas ---

class PeerRegisterRequest(BaseModel):
    name: str
    base_url: str
    shared_secret: str
    trust_level: str = "limited"
    capabilities: List[str] = []

class TaskDelegateRequest(BaseModel):
    target_peer_id: str
    original_task_id: str
    payload: Dict[str, Any]

class TaskReceiveRequest(BaseModel):
    original_task_id: str
    payload: Dict[str, Any]


# --- Admin Endpoints (Require Admin / Sovereign) ---

@router.post("/peers", status_code=status.HTTP_201_CREATED)
def register_peer(
    request: PeerRegisterRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    """Register a new peer Agentium instance. Requires admin privileges."""
    # Use is_admin as the sovereign gate — is_sovereign is not a real column
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only Sovereign (admin) can register peers.")

    peer = FederationService.register_peer(
        db=db,
        name=request.name,
        base_url=request.base_url,
        shared_secret=request.shared_secret,
        trust_level=request.trust_level,
        capabilities=request.capabilities,
    )
    return {
        "id": peer.id,
        "name": peer.name,
        "status": peer.status,
        "trust_level": peer.trust_level,
    }


@router.get("/peers")
def list_peers(
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    """List all registered peer instances."""
    from backend.models.entities.federation import FederatedInstance
    peers = db.query(FederatedInstance).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "base_url": p.base_url,
            "status": p.status,
            "trust_level": p.trust_level,
            "last_heartbeat_at": p.last_heartbeat_at,
        }
        for p in peers
    ]


# --- Outgoing Operations ---

@router.post("/tasks/delegate")
def delegate_task(
    request: TaskDelegateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    """Record an outgoing delegated task."""
    fed_task = FederationService.delegate_task(
        db=db,
        target_peer_id=request.target_peer_id,
        original_task_id=request.original_task_id,
        payload=request.payload,
    )
    return {"id": fed_task.id, "status": fed_task.status}


# --- Incoming Webhook Endpoints (Require Shared Secret Auth) ---

def authenticate_peer(
    x_agentium_peer_url: str = Header(...),
    x_agentium_secret: str = Header(...),
    db: Session = Depends(get_db),
):
    """Dependency to authenticate incoming peer requests via shared secret."""
    peer = FederationService.authenticate_peer(db, x_agentium_peer_url, x_agentium_secret)
    if not peer:
        raise HTTPException(status_code=401, detail="Invalid peer credentials.")
    return peer


@router.post("/webhooks/tasks/receive")
def receive_delegated_task(
    request: TaskReceiveRequest,
    peer=Depends(authenticate_peer),
    db: Session = Depends(get_db),
):
    """Receive a task delegated from a peer instance."""
    fed_task = FederationService.receive_delegated_task(
        db=db,
        source_peer=peer,
        original_task_id=request.original_task_id,
        payload=request.payload,
    )
    return {"accepted": True, "local_task_id": fed_task.local_task_id}