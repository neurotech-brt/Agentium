from unittest.mock import MagicMock
from backend.services.self_improvement_service import SelfImprovementService

def test_optimize_performance_no_tasks():
    service = SelfImprovementService()
    db = MagicMock()
    # Mock task query to return empty list
    db.query.return_value.filter.return_value.all.return_value = []
    
    result = service.optimize_performance(db)
    
    assert result["optimized"] == 0
    assert "insights" in result

def test_auto_generate_tools():
    service = SelfImprovementService()
    db = MagicMock()
    
    result = service.auto_generate_tools(db)
    
    assert "tools_generated" in result
    assert result["tools_generated"] == 0
    assert "status" in result
