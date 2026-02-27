"""
Phase 8 shared fixtures — real DB, real Redis, mock AI providers.
All tests run INSIDE the agentium-backend Docker container.
"""

import os
import sys
import time
import asyncio
import statistics
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

import pytest
import pytest_asyncio
import redis.asyncio as aioredis

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.database import get_db_context, SessionLocal, engine
from backend.models.schemas.messages import AgentMessage


# ───────────────────────────────────────────
# Metrics helpers
# ───────────────────────────────────────────

@dataclass
class MetricsCollector:
    """Accumulates latency / count metrics per test."""
    _samples: Dict[str, List[float]] = field(default_factory=dict)
    _counters: Dict[str, int] = field(default_factory=dict)

    def record(self, metric: str, value: float):
        self._samples.setdefault(metric, []).append(value)

    def increment(self, counter: str, by: int = 1):
        self._counters[counter] = self._counters.get(counter, 0) + by

    def count(self, counter: str) -> int:
        return self._counters.get(counter, 0)

    def p(self, metric: str, percentile: int) -> float:
        data = sorted(self._samples.get(metric, [0]))
        if not data:
            return 0.0
        idx = int(len(data) * percentile / 100)
        return data[min(idx, len(data) - 1)]

    def p50(self, metric: str) -> float:
        return self.p(metric, 50)

    def p95(self, metric: str) -> float:
        return self.p(metric, 95)

    def p99(self, metric: str) -> float:
        return self.p(metric, 99)

    def mean(self, metric: str) -> float:
        data = self._samples.get(metric, [0])
        return statistics.mean(data)

    def total(self, metric: str) -> float:
        return sum(self._samples.get(metric, [0]))

    def sample_count(self, metric: str) -> int:
        return len(self._samples.get(metric, []))

    def summary(self, metric: str) -> Dict[str, float]:
        return {
            "count": self.sample_count(metric),
            "p50": self.p50(metric),
            "p95": self.p95(metric),
            "p99": self.p99(metric),
            "mean": self.mean(metric),
        }

    def report(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for k in self._samples:
            result[k] = self.summary(k)
        result["counters"] = dict(self._counters)
        return result


@contextmanager
def timer():
    """Yields an object whose .elapsed_ms is set after the block."""

    class _Timer:
        elapsed_ms: float = 0.0
    t = _Timer()
    start = time.perf_counter()
    yield t
    t.elapsed_ms = (time.perf_counter() - start) * 1000


# ───────────────────────────────────────────
# Fixtures
# ───────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_session():
    """Real PostgreSQL session (lives for the entire test session)."""
    with get_db_context() as session:
        yield session


@pytest.fixture
def db():
    """Per-test PostgreSQL session with auto-rollback."""
    session = SessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def metrics():
    """Fresh metrics collector per test."""
    return MetricsCollector()


@pytest_asyncio.fixture
async def redis_client():
    """Live async Redis client."""
    url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    client = await aioredis.from_url(url, decode_responses=True)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def message_bus():
    """Initialised MessageBus connected to Redis."""
    from backend.services.message_bus import MessageBus
    bus = MessageBus()
    await bus.connect()
    yield bus
    await bus.disconnect()


@pytest.fixture
def cleanup_agents(db):
    """
    Tracks agent IDs created during a test and deletes them on teardown.
    Usage:
        cleanup_agents.track("30001")
        ...
    """

    class _Cleaner:
        def __init__(self):
            self._ids: List[str] = []

        def track(self, agentium_id: str):
            self._ids.append(agentium_id)

        def cleanup(self, session):
            if not self._ids:
                return
            from backend.models.entities.agents import Agent
            try:
                session.query(Agent).filter(
                    Agent.agentium_id.in_(self._ids)
                ).delete(synchronize_session="fetch")
                session.commit()
            except Exception:
                session.rollback()

    cleaner = _Cleaner()
    yield cleaner
    cleaner.cleanup(db)


def make_agent_message(
    sender_id: str = "30001",
    recipient_id: str = "20001",
    direction: str = "up",
    msg_type: str = "intent",
    content: str = "test message",
    **kwargs,
) -> AgentMessage:
    """Helper to build AgentMessage with sane defaults."""
    return AgentMessage(
        sender_id=sender_id,
        recipient_id=recipient_id,
        route_direction=direction,
        message_type=msg_type,
        content=content,
        **kwargs,
    )
