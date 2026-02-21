"""
CheckpointService for Agentium.

Handles the creation, retrieval, and application of checkpoints
for Phase 6.5 Time-Travel and Branching functionality.
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session
from backend.models.entities.checkpoint import ExecutionCheckpoint, CheckpointPhase
from backend.models.entities.task import Task
from backend.models.entities.audit import AuditLog, AuditLevel, AuditCategory


class CheckpointService:
    """
    Manages state snapshots for tasks, allowing resumption, 
    retry from past states, and divergent branching.
    """

    @staticmethod
    def create_checkpoint(
        db: Session,
        task_id: str,
        phase: CheckpointPhase,
        actor_id: str = "system",
        artifacts: Optional[List[Dict[str, Any]]] = None
    ) -> ExecutionCheckpoint:
        """
        Takes a snapshot of complete system state for a given task.
        Extracts subtasks, task metadata, and relevant configurations.
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        # Serialize current task state
        task_snapshot = task.to_dict()
        
        # In a real system you would extract complex relational sub-state here
        # e.g., fetching subtasks and agent assignments
        
        checkpoint = ExecutionCheckpoint(
            id=str(uuid.uuid4()),
            session_id=task.session_id,
            task_id=task.id,
            phase=phase,
            agent_states={}, # Optionally extract rich agent tracking data
            artifacts=artifacts or [],
            task_state_snapshot=task_snapshot
        )

        db.add(checkpoint)
        
        AuditLog.log(
            level=AuditLevel.INFO,
            category=AuditCategory.SYSTEM,
            actor_type="system",
            actor_id=actor_id,
            action="checkpoint_created",
            target_type="checkpoint",
            target_id=checkpoint.id,
            description=f"Automated checkpoint created for task {task_id} at phase {phase.value}"
        )
        
        db.commit()
        db.refresh(checkpoint)
        return checkpoint

    @staticmethod
    def resume_from_checkpoint(
        db: Session,
        checkpoint_id: str,
        actor_id: str = "user"
    ) -> Task:
        """
        Restores a task's state to match the given checkpoint (Time Travel).
        """
        checkpoint = db.query(ExecutionCheckpoint).filter(ExecutionCheckpoint.id == checkpoint_id).first()
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found.")

        task = db.query(Task).filter(Task.id == checkpoint.task_id).first()
        if not task:
            raise ValueError(f"Task {checkpoint.task_id} not found.")

        snapshot = checkpoint.task_state_snapshot
        
        # Restore fundamental properties
        # For a hard restore, we revert status, results, etc.
        if 'status' in snapshot:
            task.set_status(snapshot['status'], actor_id=actor_id, note=f"Resumed from checkpoint {checkpoint_id}")
            
        if 'result_data' in snapshot:
            task.result_data = snapshot['result_data']

        AuditLog.log(
            level=AuditLevel.WARNING,
            category=AuditCategory.SYSTEM,
            actor_type="user",
            actor_id=actor_id,
            action="checkpoint_resumed",
            target_type="task",
            target_id=task.id,
            description=f"Task {task.id} time-travelled to checkpoint {checkpoint_id}"
        )

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def branch_from_checkpoint(
        db: Session,
        checkpoint_id: str,
        branch_name: str,
        new_supervisor_id: Optional[str] = None,
        actor_id: str = "user"
    ) -> Task:
        """
        Creates a clone task from a specific checkpoint's state to allow
        parallel execution strategies without altering the original flow.
        """
        checkpoint = db.query(ExecutionCheckpoint).filter(ExecutionCheckpoint.id == checkpoint_id).first()
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found.")

        snapshot = checkpoint.task_state_snapshot
        
        # Create a new branch task avoiding unique constraints like ID or Agentium ID
        new_task_id = str(uuid.uuid4())
        
        new_task = Task(
            id=new_task_id,
            description=snapshot.get('description'),
            supervisor_id=new_supervisor_id or snapshot.get('supervisor_id'),
            priority=snapshot.get('priority'),
            type=snapshot.get('type'),
            session_id=snapshot.get('session_id'),
            acceptance_criteria=snapshot.get('acceptance_criteria'),
            veto_authority=snapshot.get('veto_authority'),
            input_data=snapshot.get('input_data')
        )

        db.add(new_task)
        
        # Create a branch checkpoint
        branch_checkpoint = ExecutionCheckpoint(
            id=str(uuid.uuid4()),
            session_id=new_task.session_id,
            task_id=new_task.id,
            phase=checkpoint.phase,
            agent_states=checkpoint.agent_states,
            artifacts=checkpoint.artifacts,
            task_state_snapshot=new_task.to_dict(),
            parent_checkpoint_id=checkpoint.id,
            branch_name=branch_name
        )
        db.add(branch_checkpoint)

        AuditLog.log(
            level=AuditLevel.INFO,
            category=AuditCategory.TASK,
            actor_type="user",
            actor_id=actor_id,
            action="checkpoint_branched",
            target_type="task",
            target_id=new_task.id,
            description=f"Branched from checkpoint {checkpoint_id} into new task {new_task.id}"
        )

        db.commit()
        db.refresh(new_task)
        return new_task

    @staticmethod
    def cleanup_old_checkpoints(db: Session, max_age_days: int = 90) -> int:
        """
        Purges execution checkpoints older than a specific age threshold.
        By default, cleans up checkpoints older than 90 days.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        checkpoints_to_delete = db.query(ExecutionCheckpoint).filter(
            ExecutionCheckpoint.created_at < cutoff_date
        ).all()
        
        count = len(checkpoints_to_delete)
        for ck in checkpoints_to_delete:
            db.delete(ck)
            
        if count > 0:
            AuditLog.log(
                level=AuditLevel.INFO,
                category=AuditCategory.SYSTEM,
                actor_type="system",
                actor_id="cleanup_cron",
                action="checkpoint_cleanup",
                description=f"Deleted {count} checkpoints older than {max_age_days} days"
            )
            db.commit()
            
        return count
