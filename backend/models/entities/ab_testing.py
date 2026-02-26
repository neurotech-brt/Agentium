"""
A/B Testing Framework - Database Entities
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    DateTime, ForeignKey, Enum
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from backend.models.entities.base import Base


class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskComplexity(str, enum.Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class Experiment(Base):
    """A/B test experiment definition."""
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Test Configuration
    task_template = Column(Text, nullable=False)
    system_prompt = Column(Text)
    test_iterations = Column(Integer, default=1)

    # Status
    status = Column(Enum(ExperimentStatus), default=ExperimentStatus.DRAFT)
    created_by = Column(String(50), default="sovereign")
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    runs = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")
    results = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentRun(Base):
    """Single execution of a model in an experiment."""
    __tablename__ = "experiment_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String(36), ForeignKey("experiments.id"))

    # Model Configuration
    config_id = Column(String(36), ForeignKey("user_model_configs.id"))
    model_name = Column(String(100))

    # Execution Details
    iteration_number = Column(Integer, default=1)
    status = Column(Enum(RunStatus), default=RunStatus.PENDING)

    # Results
    output_text = Column(Text)
    tokens_used = Column(Integer)
    latency_ms = Column(Integer)
    cost_usd = Column(Float)

    # Quality Metrics
    critic_plan_score = Column(Float)
    critic_code_score = Column(Float)
    critic_output_score = Column(Float)
    overall_quality_score = Column(Float)
    critic_feedback = Column(JSON)
    constitutional_violations = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    # Relationships
    experiment = relationship("Experiment", back_populates="runs")
    config = relationship("UserModelConfig")


class ExperimentResult(Base):
    """Aggregated results comparing all models in an experiment."""
    __tablename__ = "experiment_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String(36), ForeignKey("experiments.id"))

    # Winner Information
    winner_config_id = Column(String(36), ForeignKey("user_model_configs.id"))
    winner_model_name = Column(String(100))
    selection_reason = Column(Text)

    # Aggregate Metrics
    model_comparisons = Column(JSON)
    statistical_significance = Column(Float)

    # Recommendations
    recommended_for_similar = Column(Boolean, default=False)
    confidence_score = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="results")
    winner_config = relationship("UserModelConfig")


class ModelPerformanceCache(Base):
    """Cache of model performance for quick model selection."""
    __tablename__ = "model_performance_cache"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    task_category = Column(String(50))
    task_complexity = Column(Enum(TaskComplexity))

    best_config_id = Column(String(36), ForeignKey("user_model_configs.id"))
    best_model_name = Column(String(100))

    avg_latency_ms = Column(Integer)
    avg_cost_usd = Column(Float)
    avg_quality_score = Column(Float)
    success_rate = Column(Float)

    derived_from_experiment_id = Column(String(36), ForeignKey("experiments.id"))
    sample_size = Column(Integer)

    last_updated = Column(DateTime, default=datetime.utcnow)

    best_config = relationship("UserModelConfig")