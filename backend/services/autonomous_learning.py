"""
Autonomous Learning Engine — Phase 10.4.

Background daemon that polls CritiqueReview outcomes and extracts
structured "Best Practices" from highly successful tasks and
"Anti-Patterns" from repeatedly rejected tasks.

Extractions are stored back into ChromaDB via KnowledgeService for
future RAG context injection.

Scheduling:
    Registered with APScheduler to run every 6 hours.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LearningExtraction:
    """A single extracted learning (best practice or anti-pattern)."""
    category: str  # "best_practice" or "anti_pattern"
    summary: str
    source_task_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "summary": self.summary,
            "source_task_ids": self.source_task_ids,
            "confidence": round(self.confidence, 3),
            "extracted_at": self.extracted_at,
        }


@dataclass
class LearningStats:
    """Statistics about the autonomous learning engine."""
    total_reviews_processed: int = 0
    best_practices_extracted: int = 0
    anti_patterns_extracted: int = 0
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AutonomousLearningEngine:
    """
    Extracts reusable knowledge from critic review outcomes.

    - Best Practices: from tasks that passed ALL critic reviews on first attempt
    - Anti-Patterns: from tasks that were rejected ≥3 times

    Usage::

        engine = AutonomousLearningEngine()
        stats = engine.analyze_outcomes(db)
    """

    # Minimum reviews to consider a task for learning extraction
    MIN_REVIEWS_FOR_LEARNING = 1
    # Tasks with this many rejections are anti-pattern candidates
    ANTI_PATTERN_REJECTION_THRESHOLD = 3
    # Only extract from reviews created in the last N days
    LOOKBACK_DAYS = 7

    def __init__(self):
        self._stats = LearningStats()

    # ── Core Analysis ─────────────────────────────────────────────────────

    def analyze_outcomes(self, db: Session) -> Dict[str, Any]:
        """
        Main entry point. Scans recent CritiqueReviews and extracts learnings.

        Returns a summary dict of what was extracted.
        """
        from backend.models.entities.critics import CritiqueReview, CriticVerdict

        cutoff = datetime.utcnow() - timedelta(days=self.LOOKBACK_DAYS)

        # Get unprocessed reviews
        reviews = self.get_unprocessed_reviews(db, since=cutoff)
        if not reviews:
            logger.info("Autonomous Learning: no unprocessed reviews found")
            return {"processed": 0, "best_practices": 0, "anti_patterns": 0}

        # Group reviews by task_id
        task_reviews: Dict[str, List] = {}
        for review in reviews:
            task_reviews.setdefault(review.task_id, []).append(review)

        best_practices: List[LearningExtraction] = []
        anti_patterns: List[LearningExtraction] = []

        for task_id, task_review_list in task_reviews.items():
            bp = self.extract_best_practices(task_id, task_review_list)
            if bp:
                best_practices.extend(bp)

            ap = self.extract_anti_patterns(task_id, task_review_list)
            if ap:
                anti_patterns.extend(ap)

        # Store learnings in ChromaDB
        stored = self.store_learnings(db, best_practices, anti_patterns)

        # Mark reviews as processed
        for review in reviews:
            review.learning_extracted = True
        db.commit()

        self._stats.total_reviews_processed += len(reviews)
        self._stats.best_practices_extracted += len(best_practices)
        self._stats.anti_patterns_extracted += len(anti_patterns)
        self._stats.last_run_at = datetime.utcnow().isoformat()

        return {
            "processed": len(reviews),
            "best_practices": len(best_practices),
            "anti_patterns": len(anti_patterns),
            "stored": stored,
        }

    # ── Extraction Logic ──────────────────────────────────────────────────

    def extract_best_practices(
        self,
        task_id: str,
        reviews: List,
    ) -> List[LearningExtraction]:
        """
        Extract best practices from tasks with zero critic failures.

        A task is a best practice candidate if ALL its reviews have
        verdict PASS on the first attempt (retry_count == 0).
        """
        from backend.models.entities.critics import CriticVerdict

        all_passed = all(
            getattr(r, "verdict", None) == CriticVerdict.PASS
            and getattr(r, "retry_count", 0) == 0
            for r in reviews
        )

        if not all_passed or len(reviews) < self.MIN_REVIEWS_FOR_LEARNING:
            return []

        # Build a summary of what made this task successful
        critic_types = list({getattr(r, "critic_type", "unknown") for r in reviews})
        summary = (
            f"Task {task_id} passed all critic reviews "
            f"({', '.join(str(ct) for ct in critic_types)}) "
            f"on first attempt with {len(reviews)} review(s)."
        )

        return [LearningExtraction(
            category="best_practice",
            summary=summary,
            source_task_ids=[task_id],
            confidence=0.9,
        )]

    def extract_anti_patterns(
        self,
        task_id: str,
        reviews: List,
    ) -> List[LearningExtraction]:
        """
        Extract anti-patterns from tasks with ≥3 rejections.

        Collects rejection reasons to build a structured anti-pattern.
        """
        from backend.models.entities.critics import CriticVerdict

        rejections = [
            r for r in reviews
            if getattr(r, "verdict", None) == CriticVerdict.REJECT
        ]

        if len(rejections) < self.ANTI_PATTERN_REJECTION_THRESHOLD:
            return []

        # Collect unique rejection reasons
        reasons = list({
            getattr(r, "rejection_reason", "No reason given") or "No reason given"
            for r in rejections
        })

        summary = (
            f"Task {task_id} was rejected {len(rejections)} time(s). "
            f"Rejection reasons: {'; '.join(reasons[:5])}"
        )

        return [LearningExtraction(
            category="anti_pattern",
            summary=summary,
            source_task_ids=[task_id],
            confidence=0.8,
        )]

    # ── Storage ───────────────────────────────────────────────────────────

    def store_learnings(
        self,
        db: Session,
        best_practices: List[LearningExtraction],
        anti_patterns: List[LearningExtraction],
    ) -> int:
        """Store extracted learnings in ChromaDB via KnowledgeService."""
        stored_count = 0
        try:
            from backend.services.knowledge_service import get_knowledge_service
            ks = get_knowledge_service()
        except Exception:
            logger.error("KnowledgeService unavailable; cannot store learnings")
            return 0

        for bp in best_practices:
            try:
                doc_id = f"bp_{bp.source_task_ids[0]}_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
                ks.store_or_revise_knowledge(
                    content=bp.summary,
                    collection_name="task_patterns",
                    doc_id=doc_id,
                    metadata={
                        "type": "best_practice",
                        "source_task_ids": ",".join(bp.source_task_ids),
                        "confidence": bp.confidence,
                        "extracted_at": bp.extracted_at,
                    },
                )
                stored_count += 1
            except Exception as exc:
                logger.warning("Failed to store best practice: %s", exc)

        for ap in anti_patterns:
            try:
                doc_id = f"ap_{ap.source_task_ids[0]}_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
                ks.store_or_revise_knowledge(
                    content=ap.summary,
                    collection_name="task_patterns",
                    doc_id=doc_id,
                    metadata={
                        "type": "anti_pattern",
                        "source_task_ids": ",".join(ap.source_task_ids),
                        "confidence": ap.confidence,
                        "extracted_at": ap.extracted_at,
                    },
                )
                stored_count += 1
            except Exception as exc:
                logger.warning("Failed to store anti-pattern: %s", exc)

        return stored_count

    # ── Query Helpers ─────────────────────────────────────────────────────

    def get_unprocessed_reviews(
        self,
        db: Session,
        since: Optional[datetime] = None,
    ) -> List:
        """Get reviews that haven't been processed for learning yet."""
        from backend.models.entities.critics import CritiqueReview

        query = db.query(CritiqueReview).filter(
            CritiqueReview.learning_extracted == False,  # noqa: E712
        )
        if since:
            query = query.filter(CritiqueReview.created_at >= since)

        return query.all()

    def get_learning_stats(self) -> Dict[str, Any]:
        """Return current learning engine statistics."""
        return {
            "total_reviews_processed": self._stats.total_reviews_processed,
            "best_practices_extracted": self._stats.best_practices_extracted,
            "anti_patterns_extracted": self._stats.anti_patterns_extracted,
            "last_run_at": self._stats.last_run_at,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_learning_engine: Optional[AutonomousLearningEngine] = None


def get_learning_engine() -> AutonomousLearningEngine:
    """Return the singleton AutonomousLearningEngine."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = AutonomousLearningEngine()
    return _learning_engine
