"""
API routes for ExecutionCheckpoints (Time-Travel and Branching).
Phase 6.5 implementation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities.checkpoint import ExecutionCheckpoint, CheckpointPhase
from backend.services.checkpoint_service import CheckpointService
from backend.api.schemas.checkpoint import (
    CheckpointCreate,
    CheckpointResponse,
    CheckpointBranchRequest
)
from backend.api.schemas.task import TaskResponse

router = APIRouter(prefix="/checkpoints", tags=["checkpoints"])


@router.post("", response_model=CheckpointResponse, status_code=status.HTTP_201_CREATED)
def create_checkpoint(
    payload: CheckpointCreate,
    db: Session = Depends(get_db)
):
    """Manually create a checkpoint for a specific task line."""
    try:
        checkpoint = CheckpointService.create_checkpoint(
            db=db,
            task_id=payload.task_id,
            phase=payload.phase,
            actor_id="user_api", # Ideally from auth token
            artifacts=payload.artifacts
        )
        return checkpoint
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[CheckpointResponse])
def list_checkpoints(
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Fetch checkpoints, filterable by session or original task ID."""
    query = db.query(ExecutionCheckpoint).filter(ExecutionCheckpoint.is_active == True)
    
    if session_id:
        query = query.filter(ExecutionCheckpoint.session_id == session_id)
    if task_id:
        query = query.filter(ExecutionCheckpoint.task_id == task_id)
        
    return query.order_by(ExecutionCheckpoint.created_at.desc()).limit(limit).all()


@router.get("/{checkpoint_id}", response_model=CheckpointResponse)
def get_checkpoint(checkpoint_id: str, db: Session = Depends(get_db)):
    """Get single checkpoint details."""
    checkpoint = db.query(ExecutionCheckpoint).filter(ExecutionCheckpoint.id == checkpoint_id).first()
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return checkpoint


@router.post("/{checkpoint_id}/resume", response_model=TaskResponse)
def resume_from_checkpoint(
    checkpoint_id: str,
    db: Session = Depends(get_db)
):
    """
    Time-travel: Restores the given task back to the target checkpoint.
    """
    try:
        restored_task = CheckpointService.resume_from_checkpoint(
            db=db,
            checkpoint_id=checkpoint_id,
            actor_id="user_api"
        )
        return restored_task
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{checkpoint_id}/branch", response_model=TaskResponse)
def branch_from_checkpoint(
    checkpoint_id: str,
    payload: CheckpointBranchRequest,
    db: Session = Depends(get_db)
):
    """
    Branching: Clones the checkpoint into a new separate task tree 
    to try an alternative approach.
    """
    try:
        new_task = CheckpointService.branch_from_checkpoint(
            db=db,
            checkpoint_id=checkpoint_id,
            branch_name=payload.branch_name,
            new_supervisor_id=payload.new_supervisor_id,
            actor_id="user_api"
        )
        return new_task
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
