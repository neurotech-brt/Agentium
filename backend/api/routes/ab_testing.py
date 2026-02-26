"""
A/B Model Testing API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.models.database import get_db
from backend.models.entities.ab_testing import (
    Experiment, ExperimentStatus, RunStatus, ModelPerformanceCache
)
from backend.services.ab_testing_service import ABTestingService
from backend.models.entities.ab_testing import ExperimentRun
from backend.api.dependencies.auth import get_current_user

router = APIRouter(prefix="/ab-testing", tags=["A/B Model Testing"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ExperimentCreate(BaseModel):
    name: str
    task_template: str
    config_ids: List[str]
    description: Optional[str] = ""
    system_prompt: Optional[str] = None
    iterations: int = 1


class QuickTestRequest(BaseModel):
    task: str
    config_ids: List[str]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _experiment_progress(experiment: Experiment) -> float:
    total = len(experiment.runs)
    if total == 0:
        return 0.0
    done = len([r for r in experiment.runs if r.status != RunStatus.PENDING])
    return round(done / total * 100, 1)


def _serialize_experiment(experiment: Experiment) -> dict:
    return {
        "id": experiment.id,
        "name": experiment.name,
        "description": experiment.description,
        "status": experiment.status.value,
        "models_tested": len(set(r.config_id for r in experiment.runs)),
        "progress": _experiment_progress(experiment),
        "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
        "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
        "completed_at": experiment.completed_at.isoformat() if experiment.completed_at else None,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/experiments")
async def create_experiment(
    data: ExperimentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create and auto-start a new A/B test experiment."""
    service = ABTestingService(db)
    experiment = await service.create_experiment(
        name=data.name,
        task_template=data.task_template,
        config_ids=data.config_ids,
        description=data.description or "",
        system_prompt=data.system_prompt,
        iterations=data.iterations
    )

    # Run in background so the endpoint returns immediately
    background_tasks.add_task(service.run_experiment, experiment.id)

    return {
        **_serialize_experiment(experiment),
        "message": "Experiment created and queued for execution"
    }


@router.get("/experiments")
async def list_experiments(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List all experiments with optional status filter."""
    query = db.query(Experiment)
    if status:
        try:
            status_enum = ExperimentStatus(status)
            query = query.filter(Experiment.status == status_enum)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")

    experiments = query.order_by(Experiment.created_at.desc()).limit(limit).all()
    return [_serialize_experiment(e) for e in experiments]


@router.get("/experiments/{experiment_id}")
async def get_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get detailed experiment results including all runs and comparison."""
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()
    if not experiment:
        raise HTTPException(404, "Experiment not found")

    runs_data = []
    for run in experiment.runs:
        runs_data.append({
            "id": run.id,
            "model": run.model_name,
            "config_id": run.config_id,
            "iteration": run.iteration_number,
            "status": run.status.value,
            "tokens": run.tokens_used,
            "latency_ms": run.latency_ms,
            "cost_usd": run.cost_usd,
            "quality_score": run.overall_quality_score,
            "critic_plan_score": run.critic_plan_score,
            "critic_code_score": run.critic_code_score,
            "critic_output_score": run.critic_output_score,
            "constitutional_violations": run.constitutional_violations,
            "output_preview": (run.output_text[:300] + "...") if run.output_text and len(run.output_text) > 300 else run.output_text,
            "error_message": run.error_message,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        })

    comparison = None
    if experiment.results:
        result = experiment.results[0]
        comparison = {
            "winner": {
                "config_id": result.winner_config_id,
                "model": result.winner_model_name,
                "reason": result.selection_reason,
                "confidence": result.confidence_score
            },
            "model_comparisons": result.model_comparisons,
            "created_at": result.created_at.isoformat() if result.created_at else None
        }

    return {
        **_serialize_experiment(experiment),
        "task_template": experiment.task_template,
        "system_prompt": experiment.system_prompt,
        "test_iterations": experiment.test_iterations,
        "runs": runs_data,
        "comparison": comparison
    }


@router.post("/experiments/{experiment_id}/cancel")
async def cancel_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Cancel a running or pending experiment."""
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()
    if not experiment:
        raise HTTPException(404, "Experiment not found")

    if experiment.status not in (ExperimentStatus.RUNNING, ExperimentStatus.PENDING, ExperimentStatus.DRAFT):
        raise HTTPException(400, f"Cannot cancel experiment with status: {experiment.status.value}")

    experiment.status = ExperimentStatus.CANCELLED
    experiment.completed_at = datetime.utcnow()
    db.commit()

    return {"message": "Experiment cancelled", "id": experiment_id}


@router.delete("/experiments/{experiment_id}")
async def delete_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete an experiment and all its runs/results."""
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()
    if not experiment:
        raise HTTPException(404, "Experiment not found")

    if experiment.status == ExperimentStatus.RUNNING:
        raise HTTPException(400, "Cannot delete a running experiment. Cancel it first.")

    db.delete(experiment)
    db.commit()
    return {"message": "Experiment deleted", "id": experiment_id}


@router.get("/recommendations")
async def get_model_recommendations(
    task_category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get model recommendations based on historical experiments."""
    query = db.query(ModelPerformanceCache)
    if task_category:
        query = query.filter(ModelPerformanceCache.task_category == task_category)

    entries = query.order_by(ModelPerformanceCache.avg_quality_score.desc()).all()

    recommendations = [
        {
            "task_category": e.task_category,
            "recommended_model": e.best_model_name,
            "avg_quality_score": e.avg_quality_score,
            "avg_cost_usd": e.avg_cost_usd,
            "avg_latency_ms": e.avg_latency_ms,
            "success_rate": e.success_rate,
            "sample_size": e.sample_size,
            "last_updated": e.last_updated.isoformat() if e.last_updated else None
        }
        for e in entries
    ]

    return {
        "recommendations": recommendations,
        "total_categories": len(recommendations)
    }


@router.post("/quick-test")
async def quick_ab_test(
    data: QuickTestRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Quick A/B test — creates experiment, runs it synchronously, and returns results.
    Best for 2-3 models with simple tasks. Use /experiments for large tests.
    """
    service = ABTestingService(db)

    experiment = await service.create_experiment(
        name=f"Quick Test {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        task_template=data.task,
        config_ids=data.config_ids,
        iterations=1
    )

    # Run synchronously (blocking) for quick tests
    await service.run_experiment(experiment.id)

    # Reload from DB
    db.refresh(experiment)

    # Return full detail using get_experiment logic inline
    return await get_experiment(experiment.id, db, current_user)

@router.get("/stats")
async def get_ab_testing_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get overall A/B testing statistics."""
    from sqlalchemy import func
    
    try:
        total = db.query(func.count(Experiment.id)).scalar() or 0
        completed = db.query(func.count(Experiment.id)).filter(
            Experiment.status == ExperimentStatus.COMPLETED
        ).scalar() or 0
        running = db.query(func.count(Experiment.id)).filter(
            Experiment.status == ExperimentStatus.RUNNING
        ).scalar() or 0

        total_runs = db.query(func.count(ExperimentRun.id)).scalar() or 0
        cache_entries = db.query(func.count(ModelPerformanceCache.id)).scalar() or 0

        return {
            "total_experiments": total,
            "completed_experiments": completed,
            "running_experiments": running,
            "total_model_runs": total_runs,
            "cached_recommendations": cache_entries
        }
    except Exception as e:
        # Log error and return empty stats rather than crashing
        import logging
        logging.error(f"Error getting A/B testing stats: {e}")
        return {
            "total_experiments": 0,
            "completed_experiments": 0,
            "running_experiments": 0,
            "total_model_runs": 0,
            "cached_recommendations": 0
        }