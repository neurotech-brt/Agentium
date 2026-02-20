"""
Task State Machine Service for Agentium.
Enforces legal state transitions according to Governance Architecture.
"""

from typing import Dict, List, Set
from enum import Enum

from backend.models.entities.task import TaskStatus


class IllegalStateTransition(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class TaskStateMachine:
    """
    Lightweight state machine enforcing legal task state transitions.
    Based on Governance Architecture specification.
    """
    
    # Legal transitions map: current_status -> set of allowed next statuses
    LEGAL_TRANSITIONS: Dict[TaskStatus, Set[TaskStatus]] = {
        TaskStatus.PENDING: {
            TaskStatus.DELIBERATING,
            TaskStatus.APPROVED,      # Skip deliberation for critical/sovereign
            TaskStatus.CANCELLED
        },
        TaskStatus.DELIBERATING: {
            TaskStatus.APPROVED,
            TaskStatus.REJECTED
        },
        TaskStatus.APPROVED: {
            TaskStatus.DELEGATING,
            TaskStatus.IN_PROGRESS,   # Skip delegation for simple tasks
            TaskStatus.CANCELLED
        },
        TaskStatus.DELEGATING: {
            TaskStatus.ASSIGNED
        },
        TaskStatus.ASSIGNED: {
            TaskStatus.IN_PROGRESS,
            TaskStatus.CANCELLED
        },
        TaskStatus.IN_PROGRESS: {
            TaskStatus.REVIEW,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.RETRYING,
            TaskStatus.STOPPED
        },
        TaskStatus.REVIEW: {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.RETRYING
        },
        TaskStatus.RETRYING: {
            TaskStatus.IN_PROGRESS,
            TaskStatus.ESCALATED      # After max retries
        },
        TaskStatus.ESCALATED: {
            TaskStatus.IN_PROGRESS,    # Council decides to retry
            TaskStatus.CANCELLED,      # Council decides to liquidate
            TaskStatus.FAILED          # Council confirms failure
        },
        TaskStatus.FAILED: {
            TaskStatus.RETRYING        # Only if retry_count < max
        },
        # Terminal states - no transitions allowed
        TaskStatus.COMPLETED: set(),
        TaskStatus.CANCELLED: set(),
        TaskStatus.STOPPED: set(),
        # IDLE states
        TaskStatus.IDLE_PENDING: {
            TaskStatus.IDLE_RUNNING,
            TaskStatus.CANCELLED
        },
        TaskStatus.IDLE_RUNNING: {
            TaskStatus.IDLE_PAUSED,
            TaskStatus.IDLE_COMPLETED,
            TaskStatus.FAILED
        },
        TaskStatus.IDLE_PAUSED: {
            TaskStatus.IDLE_RUNNING,
            TaskStatus.CANCELLED
        },
        TaskStatus.IDLE_COMPLETED: set(),  # Terminal
        TaskStatus.REJECTED: set()         # Terminal
    }
    
    @classmethod
    def validate_transition(cls, current: TaskStatus, proposed: TaskStatus) -> bool:
        """
        Validate if a state transition is legal.
        
        Args:
            current: Current task status
            proposed: Proposed new status
            
        Returns:
            True if transition is legal
            
        Raises:
            IllegalStateTransition: If transition is not allowed
        """
        # Same status is always allowed (no-op)
        if current == proposed:
            return True
        
        allowed = cls.LEGAL_TRANSITIONS.get(current, set())
        
        if proposed not in allowed:
            raise IllegalStateTransition(
                f"Illegal transition: {current.value} → {proposed.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        
        return True
    
    @classmethod
    def get_allowed_transitions(cls, current: TaskStatus) -> List[TaskStatus]:
        """Get list of allowed next states from current state."""
        return list(cls.LEGAL_TRANSITIONS.get(current, set()))
    
    @classmethod
    def is_terminal_state(cls, status: TaskStatus) -> bool:
        """Check if status is a terminal state (no further transitions)."""
        return len(cls.LEGAL_TRANSITIONS.get(status, set())) == 0
    
    @classmethod
    def can_transition_to(cls, current: TaskStatus, proposed: TaskStatus) -> bool:
        """Check if transition is possible without raising exception."""
        try:
            return cls.validate_transition(current, proposed)
        except IllegalStateTransition:
            return False


# Convenience function for use in models
def validate_status_transition(current_status: TaskStatus, new_status: TaskStatus) -> bool:
    """Convenience function to validate status transitions."""
    return TaskStateMachine.validate_transition(current_status, new_status)