"""
A/B Model Testing Service for Agentium.
Executes tasks across multiple models and compares results.
"""

import uuid
import asyncio
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.entities.ab_testing import (
    Experiment, ExperimentRun, ExperimentResult,
    ExperimentStatus, RunStatus, ModelPerformanceCache, TaskComplexity
)
from backend.models.entities.user_config import UserModelConfig
from backend.services.model_provider import ModelService, calculate_cost


class CriticService:
    """Lightweight critic service for evaluating A/B test outputs."""

    def __init__(self, db: Session):
        self.db = db

    async def evaluate_output(
        self,
        task: str,
        output: str,
        system_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate output quality. Integrates with existing critic_agents.py if available,
        otherwise falls back to heuristic scoring.
        """
        try:
            # Try to import and use existing critic agents
            from backend.services.critic_agents import CriticAgents
            agents = CriticAgents(self.db)
            result = await agents.run_all_critics(
                task=task,
                output=output,
                context=system_context or ""
            )
            return {
                "plan_score": result.get("plan_score", 70.0),
                "code_score": result.get("code_score", 70.0),
                "output_score": result.get("output_score", 70.0),
                "violations": result.get("violations", 0),
                "feedback": result.get("feedback", {})
            }
        except Exception:
            # Fallback: heuristic scoring based on output characteristics
            return self._heuristic_score(task, output)

    def _heuristic_score(self, task: str, output: str) -> Dict[str, Any]:
        """Heuristic quality scoring when critic agents are unavailable."""
        output_len = len(output) if output else 0
        has_code = "```" in output or "def " in output or "function " in output

        # Basic output quality: reward length up to a point, penalize empty
        if output_len == 0:
            output_score = 0.0
        elif output_len < 50:
            output_score = 40.0
        elif output_len < 200:
            output_score = 65.0
        elif output_len < 2000:
            output_score = 80.0
        else:
            output_score = 75.0  # Very long outputs might be verbose

        # Code score
        code_score = 75.0 if has_code else 70.0

        # Plan score (check for structured thinking)
        has_structure = any(x in output for x in ["1.", "2.", "##", "**", "- "])
        plan_score = 78.0 if has_structure else 68.0

        return {
            "plan_score": plan_score,
            "code_score": code_score,
            "output_score": output_score,
            "violations": 0,
            "feedback": {
                "plan": "Heuristic evaluation",
                "code": "Heuristic evaluation",
                "output": "Heuristic evaluation"
            }
        }


class ABTestingService:
    """Service for running A/B tests between AI models."""

    def __init__(self, db: Session):
        self.db = db
        self.critic_service = CriticService(db)

    async def create_experiment(
        self,
        name: str,
        task_template: str,
        config_ids: List[str],
        description: str = "",
        system_prompt: Optional[str] = None,
        iterations: int = 1
    ) -> Experiment:
        """Create a new A/B test experiment."""

        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            task_template=task_template,
            system_prompt=system_prompt,
            test_iterations=iterations,
            status=ExperimentStatus.DRAFT
        )
        self.db.add(experiment)

        for config_id in config_ids:
            config = self.db.query(UserModelConfig).filter(
                UserModelConfig.id == config_id
            ).first()
            model_name = config.default_model if config else "unknown"
            for i in range(1, iterations + 1):
                run = ExperimentRun(
                    id=str(uuid.uuid4()),
                    experiment_id=experiment.id,
                    config_id=config_id,
                    model_name=model_name,
                    iteration_number=i,
                    status=RunStatus.PENDING
                )
                self.db.add(run)

        self.db.commit()
        self.db.refresh(experiment)
        return experiment

    async def run_experiment(self, experiment_id: str) -> Experiment:
        """Execute all runs in an experiment."""

        experiment = self.db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.utcnow()
        self.db.commit()

        try:
            pending_runs = [
                run for run in experiment.runs
                if run.status == RunStatus.PENDING
            ]

            semaphore = asyncio.Semaphore(3)

            async def run_with_semaphore(run: ExperimentRun):
                async with semaphore:
                    return await self._execute_single_run(run, experiment)

            results = await asyncio.gather(
                *[run_with_semaphore(run) for run in pending_runs],
                return_exceptions=True
            )

            failures = [r for r in results if isinstance(r, Exception)]
            experiment.status = ExperimentStatus.FAILED if failures and len(failures) == len(pending_runs) else ExperimentStatus.COMPLETED
            experiment.completed_at = datetime.utcnow()

            await self._generate_comparison(experiment)
            self.db.commit()
            return experiment

        except Exception as e:
            experiment.status = ExperimentStatus.FAILED
            experiment.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    async def _execute_single_run(
        self,
        run: ExperimentRun,
        experiment: Experiment
    ) -> ExperimentRun:
        """Execute a single model test."""

        run.status = RunStatus.RUNNING
        run.started_at = datetime.utcnow()
        self.db.commit()

        try:
            provider = await ModelService.get_provider(
                experiment.created_by or "sovereign",
                run.config_id,
            )

            if not provider:
                raise ValueError(f"Provider not found for config {run.config_id}")

            start_time = time.time()
            result = await provider.generate(
                system_prompt=experiment.system_prompt or "You are a helpful assistant.",
                user_message=experiment.task_template,
                agentium_id=f"ab-test-{run.id}"
            )
            latency_ms = int((time.time() - start_time) * 1000)

            run.output_text = result.get("content", "")
            run.tokens_used = result.get("tokens_used", 0)
            run.latency_ms = result.get("latency_ms", latency_ms)
            run.cost_usd = result.get("cost_usd", 0.0) or self._estimate_cost(
                run.config_id, run.tokens_used or 0
            )

            critic_results = await self.critic_service.evaluate_output(
                task=experiment.task_template,
                output=run.output_text,
                system_context=experiment.system_prompt
            )

            run.critic_plan_score = critic_results.get("plan_score", 0)
            run.critic_code_score = critic_results.get("code_score", 0)
            run.critic_output_score = critic_results.get("output_score", 0)
            run.critic_feedback = critic_results
            run.overall_quality_score = self._calculate_quality_score(critic_results)
            run.constitutional_violations = critic_results.get("violations", 0)
            run.status = RunStatus.COMPLETED
            run.completed_at = datetime.utcnow()

        except Exception as e:
            run.status = RunStatus.FAILED
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()

        self.db.commit()
        return run

    def _calculate_quality_score(self, critic_results: Dict) -> float:
        weights = {"plan_score": 0.25, "code_score": 0.35, "output_score": 0.40}
        total = sum(critic_results.get(k, 0) * w for k, w in weights.items())
        return round(total, 2)

    def _estimate_cost(self, config_id: str, tokens: int) -> float:
        """Use real pricing table via calculate_cost when provider info is available."""
        try:
            config = self.db.query(UserModelConfig).filter(
                UserModelConfig.id == config_id
            ).first()
            if config:
                return calculate_cost(
                    model_name=config.default_model or "",
                    provider=config.provider,
                    prompt_tokens=int(tokens * 0.6),
                    completion_tokens=int(tokens * 0.4),
                )
        except Exception:
            pass
        return round((tokens / 1_000_000) * 2.0, 8)

    async def _generate_comparison(self, experiment: Experiment) -> Optional[ExperimentResult]:
        """Generate aggregated comparison results."""

        model_stats: Dict[str, Any] = {}

        for run in experiment.runs:
            if run.status != RunStatus.COMPLETED:
                continue

            key = run.config_id
            if key not in model_stats:
                model_stats[key] = {
                    "config_id": key,
                    "model_name": run.model_name,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_latency": 0,
                    "quality_scores": [],
                    "run_count": 0
                }

            s = model_stats[key]
            s["total_tokens"] += run.tokens_used or 0
            s["total_cost"] += run.cost_usd or 0.0
            s["total_latency"] += run.latency_ms or 0
            s["quality_scores"].append(run.overall_quality_score or 0)
            s["run_count"] += 1

        if not model_stats:
            return None

        comparisons = []
        for config_id, s in model_stats.items():
            n = s["run_count"]
            comparisons.append({
                "config_id": config_id,
                "model_name": s["model_name"],
                "avg_tokens": round(s["total_tokens"] / n),
                "avg_cost_usd": round(s["total_cost"] / n, 6),
                "avg_latency_ms": int(s["total_latency"] / n),
                "avg_quality_score": round(sum(s["quality_scores"]) / n, 2),
                "success_rate": 100.0,
                "total_runs": n
            })

        winner = self._determine_winner(comparisons)

        result = ExperimentResult(
            id=str(uuid.uuid4()),
            experiment_id=experiment.id,
            winner_config_id=winner["config_id"],
            winner_model_name=winner["model_name"],
            selection_reason=winner["reason"],
            model_comparisons={"models": comparisons},
            confidence_score=winner["confidence"]
        )
        self.db.add(result)

        await self._update_performance_cache(experiment, winner, comparisons)
        self.db.commit()
        return result

    def _determine_winner(self, comparisons: List[Dict]) -> Dict:
        """Determine the winning model based on composite scoring."""

        if not comparisons:
            return {"config_id": None, "model_name": "N/A", "reason": "No successful runs", "confidence": 0}

        max_cost = max((c["avg_cost_usd"] for c in comparisons), default=1) or 1
        max_latency = max((c["avg_latency_ms"] for c in comparisons), default=1) or 1

        scored = []
        for comp in comparisons:
            quality = comp["avg_quality_score"]
            cost_score = (1 - (comp["avg_cost_usd"] / max_cost)) * 100
            latency_score = (1 - (comp["avg_latency_ms"] / max_latency)) * 100
            success_score = comp["success_rate"]

            composite = (
                quality * 0.40 +
                cost_score * 0.25 +
                latency_score * 0.20 +
                success_score * 0.15
            )
            scored.append({
                **comp,
                "composite_score": round(composite, 2),
                "breakdown": {
                    "quality": quality,
                    "cost_efficiency": round(cost_score, 2),
                    "speed": round(latency_score, 2),
                    "reliability": success_score
                }
            })

        winner = max(scored, key=lambda x: x["composite_score"])

        reason = (
            f"Selected {winner['model_name']} with composite score {winner['composite_score']}/100. "
            f"Quality: {winner['breakdown']['quality']}, "
            f"Cost-efficiency: {winner['breakdown']['cost_efficiency']}, "
            f"Speed: {winner['breakdown']['speed']}, "
            f"Reliability: {winner['breakdown']['reliability']}%"
        )

        if len(scored) > 1:
            runner_up = sorted(scored, key=lambda x: x["composite_score"], reverse=True)[1]
            margin = winner["composite_score"] - runner_up["composite_score"]
            confidence = min(100, max(50, 50 + margin * 2))
        else:
            confidence = 75.0

        return {
            "config_id": winner["config_id"],
            "model_name": winner["model_name"],
            "reason": reason,
            "confidence": round(confidence, 2)
        }

    async def _update_performance_cache(
        self,
        experiment: Experiment,
        winner: Dict,
        comparisons: List[Dict]
    ):
        """Update the model performance cache with experiment results."""

        task_category = self._categorize_task(experiment.task_template)
        winning_comp = next(
            (c for c in comparisons if c["config_id"] == winner["config_id"]),
            comparisons[0] if comparisons else None
        )
        if not winning_comp:
            return

        existing = self.db.query(ModelPerformanceCache).filter(
            ModelPerformanceCache.task_category == task_category
        ).first()

        if existing:
            existing.best_config_id = winner["config_id"]
            existing.best_model_name = winner["model_name"]
            existing.avg_quality_score = winning_comp["avg_quality_score"]
            existing.avg_cost_usd = winning_comp["avg_cost_usd"]
            existing.avg_latency_ms = winning_comp["avg_latency_ms"]
            existing.success_rate = winning_comp["success_rate"]
            existing.derived_from_experiment_id = experiment.id
            existing.sample_size = (existing.sample_size or 0) + winning_comp["total_runs"]
            existing.last_updated = datetime.utcnow()
        else:
            cache = ModelPerformanceCache(
                id=str(uuid.uuid4()),
                task_category=task_category,
                task_complexity=TaskComplexity.MEDIUM,
                best_config_id=winner["config_id"],
                best_model_name=winner["model_name"],
                avg_quality_score=winning_comp["avg_quality_score"],
                avg_cost_usd=winning_comp["avg_cost_usd"],
                avg_latency_ms=winning_comp["avg_latency_ms"],
                success_rate=winning_comp["success_rate"],
                derived_from_experiment_id=experiment.id,
                sample_size=winning_comp["total_runs"]
            )
            self.db.add(cache)

    async def get_best_model_for_task(
        self,
        task_description: str,
        task_category: Optional[str] = None
    ) -> Optional[UserModelConfig]:
        """Get the best model for a similar task based on historical experiments."""

        if not task_category:
            task_category = self._categorize_task(task_description)

        cache_entry = (
            self.db.query(ModelPerformanceCache)
            .filter(ModelPerformanceCache.task_category == task_category)
            .order_by(ModelPerformanceCache.avg_quality_score.desc())
            .first()
        )

        if cache_entry and cache_entry.best_config:
            return cache_entry.best_config

        return (
            self.db.query(UserModelConfig)
            .filter(UserModelConfig.is_default == True)
            .first()
        )

    def _categorize_task(self, description: str) -> str:
        desc_lower = description.lower()
        if any(kw in desc_lower for kw in ["code", "program", "function", "bug", "error", "script", "implement"]):
            return "coding"
        elif any(kw in desc_lower for kw in ["analyze", "analysis", "data", "report", "metrics", "compare"]):
            return "analysis"
        elif any(kw in desc_lower for kw in ["write", "draft", "creative", "story", "poem", "essay"]):
            return "creative"
        elif any(kw in desc_lower for kw in ["math", "calculate", "equation", "solve", "compute"]):
            return "mathematical"
        else:
            return "general"