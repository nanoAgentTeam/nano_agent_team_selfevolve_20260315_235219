"""
Tests for the AgentMonitorTool wrapper.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.tools.agent_monitor_tool import AgentMonitorTool


class TestAgentMonitorTool:
    """Tests for AgentMonitorTool class."""

    def test_tool_has_required_attributes(self):
        """Test that the tool has name, description, and parameters_schema."""
        tool = AgentMonitorTool()
        
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'description')
        assert hasattr(tool, 'parameters_schema')
        assert hasattr(tool, 'execute')
        
        assert tool.name == "agent_monitor"
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
        assert isinstance(tool.parameters_schema, dict)

    def test_execute_with_get_status_summary_action(self):
        """Test execute method with get_status_summary action."""
        tool = AgentMonitorTool()
        
        mock_status = [
            {'name': 'Developer1', 'status': 'RUNNING', 'role': 'Developer'}
        ]
        
        with patch('backend.tools.agent_monitor_tool.get_agent_status_summary', return_value=mock_status):
            result = tool.execute(action="get_status_summary")
        
        assert result['success'] is True
        assert 'agents' in result
        assert result['agents'] == mock_status

    def test_execute_with_invalid_action(self):
        """Test execute method with invalid action returns error."""
        tool = AgentMonitorTool()
        
        result = tool.execute(action="invalid_action")
        
        assert result['success'] is False
        assert 'error' in result

    def test_execute_handles_exceptions(self):
        """Test that execute handles exceptions gracefully."""
        tool = AgentMonitorTool()
        
        with patch('backend.tools.agent_monitor_tool.get_agent_status_summary', side_effect=Exception("Test error")):
            result = tool.execute(action="get_status_summary")
        
        assert result['success'] is False
        assert 'error' in result
        assert "Test error" in result['error']
