"""
Tests for AgentDiagnosisTool
"""
import pytest
from backend.tools.agent_diagnosis_tool import AgentDiagnosisTool
from backend.utils.agent_diagnosis import AgentHealthStatus


class TestAgentDiagnosisTool:
    """Test suite for AgentDiagnosisTool"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tool = AgentDiagnosisTool()
    
    def test_tool_name(self):
        """Test tool has correct name"""
        assert self.tool.name == "agent_diagnosis"
    
    def test_tool_description(self):
        """Test tool has description"""
        assert self.tool.description is not None
        assert len(self.tool.description) > 0
        assert "diagnose" in self.tool.description.lower()
    
    def test_parameters_schema(self):
        """Test parameters schema is valid"""
        schema = self.tool.parameters_schema
        assert schema is not None
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "error_rate" in schema["properties"]
        assert "response_time_avg" in schema["properties"]
        assert "success_rate" in schema["properties"]
    
    def test_required_parameters(self):
        """Test required parameters are defined"""
        schema = self.tool.parameters_schema
        required = schema.get("required", [])
        assert "error_rate" in required
        assert "response_time_avg" in required
        assert "success_rate" in required
    
    def test_execute_healthy_agent(self):
        """Test diagnosis of a healthy agent"""
        result = self.tool.execute(
            error_rate=0.05,
            response_time_avg=2.0,
            success_rate=0.95
        )
        assert "status" in result
        assert "issues" in result
        assert "recommendations" in result
        assert "summary" in result
    
    def test_execute_unhealthy_agent(self):
        """Test diagnosis of an unhealthy agent"""
        result = self.tool.execute(
            error_rate=0.5,
            response_time_avg=10.0,
            success_rate=0.5
        )
        assert "status" in result
        assert result["status"] in ["healthy", "degraded", "unhealthy", "critical"]
        assert isinstance(result["issues"], list)
        assert isinstance(result["recommendations"], list)
    
    def test_execute_with_memory_usage(self):
        """Test diagnosis with optional memory usage parameter"""
        result = self.tool.execute(
            error_rate=0.1,
            response_time_avg=3.0,
            success_rate=0.9,
            memory_usage_mb=512.0
        )
        assert result is not None
        assert "metrics" in result
    
    def test_execute_returns_dict(self):
        """Test execute returns a dictionary"""
        result = self.tool.execute(
            error_rate=0.2,
            response_time_avg=5.0,
            success_rate=0.8
        )
        assert isinstance(result, dict)
    
    def test_status_values(self):
        """Test that status values are valid"""
        test_cases = [
            (0.01, 1.0, 0.99),  # Very healthy
            (0.1, 3.0, 0.9),    # Normal
            (0.3, 8.0, 0.7),    # Degraded
            (0.5, 15.0, 0.5),   # Unhealthy
        ]
        
        for error_rate, response_time, success_rate in test_cases:
            result = self.tool.execute(
                error_rate=error_rate,
                response_time_avg=response_time,
                success_rate=success_rate
            )
            assert result["status"] in ["healthy", "degraded", "unhealthy", "critical"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
