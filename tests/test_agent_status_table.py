"""
Tests for AgentStatusTable component
"""

import pytest
import os
import json
import tempfile
import time

# Import the component we're testing
from src.tui.components.agent_status_table import AgentStatusTable


class TestAgentStatusTable:
    """Test suite for AgentStatusTable widget"""

    def test_widget_instantiation(self):
        """Test that the widget can be instantiated"""
        table = AgentStatusTable()
        assert table is not None
        assert isinstance(table, AgentStatusTable)

    def test_status_color_running(self):
        """Test RUNNING status is color-coded green"""
        table = AgentStatusTable()
        # Check the status color mapping
        assert "RUNNING" in table.STATUS_COLORS
        assert table.STATUS_COLORS["RUNNING"] == "green"

    def test_status_color_dead(self):
        """Test DEAD status is color-coded red"""
        table = AgentStatusTable()
        assert "DEAD" in table.STATUS_COLORS
        assert table.STATUS_COLORS["DEAD"] == "red"

    def test_status_color_idle(self):
        """Test IDLE status is color-coded yellow"""
        table = AgentStatusTable()
        assert "IDLE" in table.STATUS_COLORS
        assert table.STATUS_COLORS["IDLE"] == "yellow"

    def test_parse_registry_data(self):
        """Test parsing registry data from JSON"""
        table = AgentStatusTable()
        
        sample_registry = {
            "TestAgent": {
                "pid": 12345,
                "role": "Developer",
                "status": "RUNNING",
                "start_time": 1773595184.335905
            }
        }
        
        result = table._parse_registry_data(sample_registry)
        assert len(result) == 1
        assert result[0]["name"] == "TestAgent"
        assert result[0]["pid"] == 12345
        assert result[0]["role"] == "Developer"
        assert result[0]["status"] == "RUNNING"

    def test_empty_registry(self):
        """Test handling empty registry"""
        table = AgentStatusTable()
        result = table._parse_registry_data({})
        assert result == []

    def test_format_uptime(self):
        """Test uptime formatting"""
        table = AgentStatusTable()
        # Test with a start time 120 seconds ago
        import time
        start_time = time.time() - 120
        uptime_str = table._format_uptime(start_time)
        assert "2m" in uptime_str or "120s" in uptime_str

    def test_get_status_icon(self):
        """Test status icon mapping"""
        table = AgentStatusTable()
        assert table._get_status_icon("RUNNING") == "🟢"
        assert table._get_status_icon("DEAD") == "🔴"
        assert table._get_status_icon("IDLE") == "🟡"
        assert table._get_status_icon("UNKNOWN") == "❓"


class TestAgentStatusTableIntegration:
    """Integration tests with registry data"""

    def test_load_registry_from_file(self):
        """Test loading registry data from file"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = os.path.join(tmpdir, "registry.json")
            
            # Initial data
            initial_data = {
                "Agent1": {
                    "pid": 11111,
                    "role": "Developer",
                    "status": "RUNNING",
                    "start_time": 1773595184.335905
                }
            }
            
            with open(registry_path, 'w') as f:
                json.dump(initial_data, f)
            
            table = AgentStatusTable(blackboard_dir=tmpdir)
            table._load_registry()
            
            # Should have loaded the data
            assert len(table._agent_data) == 1
            assert table._agent_data[0]["name"] == "Agent1"

    def test_load_missing_registry(self):
        """Test handling missing registry file gracefully"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # No registry.json file
            table = AgentStatusTable(blackboard_dir=tmpdir)
            table._load_registry()
            
            # Should have empty data
            assert table._agent_data == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
