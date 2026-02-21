"""
Checkpoint and time-travel models for Agentium.
Implements Phase 6.5: Session resumption and retry from any point.
"""

from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from backend.models.entities.base import BaseEntity
import enum


class CheckpointPhase(str, enum.Enum):
    """Phases at which checkpoints can be created."""
    PLAN_APPROVED = "plan_approved"
    EXECUTION_COMPLETE = "execution_complete"
    CRITIQUE_PASSED = "critique_passed"
    MANUAL = "manual"  # User-triggered or arbitrary safe points


class ExecutionCheckpoint(BaseEntity):
    """
    Serializable state snapshot for a specific point in a task's lifecycle.
    Allows for time-travel recovery and branching.
    """
    
    __tablename__ = 'execution_checkpoints'
    
    session_id = Column(String(100), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey('tasks.id'), nullable=False, index=True)
    phase = Column(Enum(CheckpointPhase), nullable=False)
    
    # Complete system state snapshot
    agent_states = Column(JSON, nullable=False, default=dict)  # State of agents involved
    artifacts = Column(JSON, nullable=False, default=list)     # Generated outputs (List of URLs/Refs)
    task_state_snapshot = Column(JSON, nullable=False, default=dict) # Full dump of the task at this point
    
    # Hierarchical branching support
    parent_checkpoint_id = Column(String(36), ForeignKey('execution_checkpoints.id'), nullable=True)
    branch_name = Column(String(100), nullable=True)
    
    # Relationships
    task = relationship("Task", foreign_keys=[task_id])
    parent_checkpoint = relationship("ExecutionCheckpoint", remote_side="ExecutionCheckpoint.id", backref="child_branches")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not kwargs.get('agentium_id'):
            # Prefix 'C' for Checkpoint
            session = kwargs.get('session_id', 'unknown')[:8]
            self.agentium_id = f"C{session}{datetime.utcnow().strftime('%H%M%S')}"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'session_id': self.session_id,
            'task_id': self.task_id,
            'phase': self.phase.value,
            'agent_states': self.agent_states,
            'artifacts': self.artifacts,
            'task_state_snapshot': self.task_state_snapshot,
            'parent_checkpoint_id': self.parent_checkpoint_id,
            'branch_name': self.branch_name
        })
        return base
