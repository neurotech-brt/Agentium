"""
Federation Service (Phase 11.2)
===============================
Handles peer instance registration, cross-instance messaging, and federated task delegation.
Note: For external communication, instances use HTTP requests with a shared secret.
"""
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models.entities.federation import FederatedInstance, FederatedTask, FederatedVote
from backend.core.config import settings

class FederationService:
    @staticmethod
    def _hash_secret(secret: str) -> str:
        """Hash a shared secret for storage."""
        return hashlib.sha256(secret.encode()).hexdigest()

    @staticmethod
    def _verify_secret(secret: str, hashed_secret: str) -> bool:
        """Verify a shared secret against its hash."""
        return FederationService._hash_secret(secret) == hashed_secret

    @classmethod
    def register_peer(
        cls, db: Session, name: str, base_url: str, shared_secret: str, trust_level: str = "limited",
        capabilities: Optional[List[str]] = None
    ) -> FederatedInstance:
        """Register a new peer instance."""
        if not settings.FEDERATION_ENABLED:
            raise HTTPException(status_code=400, detail="Federation is not enabled on this instance.")
            
        existing = db.query(FederatedInstance).filter(FederatedInstance.base_url == base_url).first()
        if existing:
            raise HTTPException(status_code=400, detail="Peer with this base URL already registered.")
            
        peer = FederatedInstance(
            name=name,
            base_url=base_url,
            shared_secret_hash=cls._hash_secret(shared_secret),
            status="active",
            trust_level=trust_level,
            capabilities_shared=capabilities or []
        )
        db.add(peer)
        db.commit()
        db.refresh(peer)
        return peer

    @staticmethod
    def get_peer(db: Session, peer_id: str) -> FederatedInstance:
        """Get a registered peer."""
        peer = db.query(FederatedInstance).filter(FederatedInstance.id == peer_id).first()
        if not peer:
            raise HTTPException(status_code=404, detail="Peer not found.")
        return peer
        
    @staticmethod
    def authenticate_peer(db: Session, base_url: str, secret: str) -> FederatedInstance:
        """Authenticate an incoming request from a peer."""
        if not settings.FEDERATION_ENABLED:
            raise HTTPException(status_code=403, detail="Federation disabled.")
            
        peer = db.query(FederatedInstance).filter(FederatedInstance.base_url == base_url).first()
        if not peer:
            raise HTTPException(status_code=401, detail="Peer not registered.")
            
        if not FederationService._verify_secret(secret, peer.shared_secret_hash):
            raise HTTPException(status_code=401, detail="Invalid shared secret.")
            
        if peer.status != "active":
            raise HTTPException(status_code=403, detail=f"Peer status is {peer.status}.")
            
        # Update heartbeat
        peer.last_heartbeat_at = datetime.utcnow()
        db.commit()
        return peer

    @staticmethod
    def delegate_task(
        db: Session, target_peer_id: str, original_task_id: str, payload: Dict[str, Any]
    ) -> FederatedTask:
        """Record an outgoing delegated task. (Actual HTTP call happens asynchronously or in routing layer)."""
        peer = FederationService.get_peer(db, target_peer_id)
        if peer.status != "active":
            raise HTTPException(status_code=400, detail="Target peer is not active.")
            
        # In to-be-implemented HTTP client layer: send payload to peer.base_url
        
        fed_task = FederatedTask(
            target_instance_id=peer.id,
            original_task_id=original_task_id,
            status="pending"
        )
        db.add(fed_task)
        db.commit()
        db.refresh(fed_task)
        return fed_task

    @staticmethod
    def receive_delegated_task(
        db: Session, source_peer: FederatedInstance, original_task_id: str, payload: Dict[str, Any]
    ) -> FederatedTask:
        """Receive a task from a peer and create local record."""
        if source_peer.trust_level == "read_only":
            raise HTTPException(status_code=403, detail="Peer only has read_only access.")
            
        # Here we would create a local Task based on the payload.
        # For now, we just create the federation tracking record.
        local_task_id = str(uuid.uuid4()) # Placeholder for actual local task ID
        
        fed_task = FederatedTask(
            source_instance_id=source_peer.id,
            original_task_id=original_task_id,
            local_task_id=local_task_id,
            status="accepted"
        )
        db.add(fed_task)
        db.commit()
        db.refresh(fed_task)
        return fed_task

    @staticmethod
    def cleanup_stale_peers(db: Session, timeout_minutes: int = 1440):
        """Mark peers as suspended if no heartbeat within timeout."""
        timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        stale_peers = db.query(FederatedInstance).filter(
            FederatedInstance.status == "active",
            FederatedInstance.last_heartbeat_at < timeout_threshold
        ).all()
        
        for peer in stale_peers:
            peer.status = "suspended"
            
        if stale_peers:
            db.commit()
        return len(stale_peers)
