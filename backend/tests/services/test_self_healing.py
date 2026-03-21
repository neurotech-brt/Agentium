import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from backend.services.self_healing_service import SelfHealingService
from backend.models.entities.agents import Agent, AgentStatus
from backend.models.entities.audit import AuditLog
from backend.models.entities.task import Task, TaskStatus
import pytest_asyncio

@pytest.fixture
def mock_db():
    db = MagicMock()
    return db

def test_heartbeat_update(mock_db):
    # Mock some active agents
    agent1 = Agent(agentium_id="A1", status=AgentStatus.WORKING)
    agent2 = Agent(agentium_id="A2", status=AgentStatus.IDLE)
    
    # Mock query builder
    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = [agent1, agent2]
    mock_db.query.return_value = mock_query

    result = SelfHealingService.update_heartbeats(mock_db)

    assert result["updated"] == 2
    assert getattr(agent1, 'last_heartbeat_at', None) is not None
    assert getattr(agent2, 'last_heartbeat_at', None) is not None
    mock_db.commit.assert_called_once()

@patch('backend.services.self_healing_service.websocket_manager')
def test_detect_crashed_agents(mock_ws, mock_db):
    agent_crashed = Agent(
        agentium_id="CRASH1",
        status=AgentStatus.WORKING,
        last_heartbeat_at=datetime.utcnow() - timedelta(minutes=6),
        is_active=True
    )
    
    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = [agent_crashed]
    mock_db.query.return_value = mock_query
    
    # Mock recovery service internally called
    with patch('backend.services.self_healing_service.SelfHealingService.recover_agent') as mock_recover:
        result = SelfHealingService.detect_crashed_agents(mock_db)
        
        assert result["detected"] == 1
        assert agent_crashed.status == AgentStatus.OFFLINE
        mock_recover.assert_called_once_with(mock_db, agent_crashed)
        
        # Test WS broadcast
        mock_ws.broadcast.assert_called_once()

def test_graceful_degradation_triggers(mock_db):
    # Mock all agents having OPEN circuit breakers
    # This should trigger degraded mode
    with patch('backend.services.agent_orchestrator.AgentOrchestrator') as MockOrch:
        mock_orch_instance = MockOrch.return_value
        mock_orch_instance._circuit_breakers = {
            "A1": {"state": "open"},
            "A2": {"state": "open"}
        }

        # The query for active agents length matches CB open length
        mock_query = MagicMock()
        mock_query.filter_by.return_value.count.return_value = 2
        mock_db.query.return_value = mock_query

        with patch('backend.services.self_healing_service.websocket_manager') as mock_ws:
            result = SelfHealingService.check_degradation_triggers(mock_db)
            
            assert result["system_mode"] == "degraded"
            assert result["active_circuit_breakers"] == 2

            # Try again with resolved CBs
            mock_orch_instance._circuit_breakers = {
                "A1": {"state": "closed"}
            }
            result_restored = SelfHealingService.check_degradation_triggers(mock_db)
            assert result_restored["system_mode"] == "normal"
