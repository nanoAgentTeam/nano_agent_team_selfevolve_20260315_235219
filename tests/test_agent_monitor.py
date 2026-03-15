"""
Tests for the agent_monitor utility module.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
from backend.utils.agent_monitor import get_agent_status_summary, get_task_progress_summary, estimate_session_cost

class TestGetAgentStatusSummary:
    """Tests for get_agent_status_summary function."""

    def test_returns_empty_list_when_no_agents(self):
        """Test that empty registry returns empty list."""
        with patch('backend.utils.agent_monitor._read_registry_json', return_value={}):
            result = get_agent_status_summary()

        assert result == []

    def test_returns_structured_agent_data(self):
        """Test that agent data is returned in structured format."""
        mock_registry = {
            'Developer1': {
                'pid': 12345,
                'role': 'Developer',
                'status': 'RUNNING',
                'verified_status': 'ALIVE'
            },
            'Tester': {
                'pid': 12346,
                'role': 'Tester',
                'status': 'DEAD',
                'verified_status': 'DEAD'
            }
        }
        
        with patch('backend.utils.agent_monitor._read_registry_json', return_value=mock_registry):
            result = get_agent_status_summary()

        assert len(result) == 2
        assert result[0]['name'] == 'Developer1'
        assert result[0]['status'] == 'RUNNING'
        assert result[0]['verified_status'] == 'ALIVE'
        assert result[1]['name'] == 'Tester'
        assert result[1]['status'] == 'DEAD'

    def test_includes_all_required_fields(self):
        """Test that all required fields are present in output."""
        mock_registry = {
            'Architect': {
                'pid': 11111,
                'role': 'Architect',
                'status': 'RUNNING',
                'start_time': 1234567890.0,
                'verified_status': 'ALIVE'
            }
        }
        
        with patch('backend.utils.agent_monitor._read_registry_json', return_value=mock_registry):
            result = get_agent_status_summary()

        assert len(result) == 1
        agent = result[0]
        assert 'name' in agent
        assert 'pid' in agent
        assert 'role' in agent
        assert 'status' in agent
        assert 'verified_status' in agent

class TestGetTaskProgressSummary:
    """Tests for get_task_progress_summary function."""

    def test_returns_empty_metrics_when_no_tasks(self, tmp_path):
        """Test that empty plan returns zero metrics."""
        # Create a fake central_plan.md
        central_plan = tmp_path / "global_indices" / "central_plan.md"
        central_plan.parent.mkdir()
        central_plan.write_text('{"tasks": []}')

        result = get_task_progress_summary(blackboard_path=tmp_path)

        assert result['total'] == 0
        assert result['pending'] == 0
        assert result['in_progress'] == 0
        assert result['done'] == 0
        assert result['blocked'] == 0

    def test_calculates_correct_counts(self, tmp_path):
        """Test that task counts are calculated correctly."""
        # Create a fake central_plan.md with task data
        central_plan = tmp_path / "global_indices" / "central_plan.md"
        central_plan.parent.mkdir()
        central_plan.write_text('''
{
  "tasks": [
    {"id": 1, "status": "DONE"},
    {"id": 2, "status": "DONE"},
    {"id": 3, "status": "IN_PROGRESS"},
    {"id": 4, "status": "PENDING"},
    {"id": 5, "status": "BLOCKED"}
  ]
}
''')

        result = get_task_progress_summary(blackboard_path=tmp_path)

        assert result['total'] == 5
        assert result['done'] == 2
        assert result['in_progress'] == 1
        assert result['pending'] == 1
        assert result['blocked'] == 1

    def test_calculates_completion_percentage(self, tmp_path):
        """Test that completion percentage is calculated correctly."""
        central_plan = tmp_path / "global_indices" / "central_plan.md"
        central_plan.parent.mkdir()
        central_plan.write_text('''
{
  "tasks": [
    {"id": 1, "status": "DONE"},
    {"id": 2, "status": "DONE"},
    {"id": 3, "status": "DONE"},
    {"id": 4, "status": "PENDING"}
  ]
}
''')

        result = get_task_progress_summary(blackboard_path=tmp_path)

        assert result['completion_percentage'] == 75.0

    def test_handles_zero_total_tasks(self, tmp_path):
        """Test that zero total tasks doesn't cause division error."""
        central_plan = tmp_path / "global_indices" / "central_plan.md"
        central_plan.parent.mkdir()
        central_plan.write_text('{"tasks": []}')

        result = get_task_progress_summary(blackboard_path=tmp_path)

        assert result['completion_percentage'] == 0.0

    def test_handles_missing_file_gracefully(self):
        """Test that missing file returns empty metrics."""
        result = get_task_progress_summary(blackboard_path=Path("/nonexistent"))

        assert result['total'] == 0
        assert result['completion_percentage'] == 0.0

class TestEstimateSessionCost:
    """Tests for estimate_session_cost function."""

    def test_returns_zero_when_no_cost_data(self):
        """Test that missing cost data returns zero."""
        with patch('backend.utils.agent_monitor._read_registry_json', return_value={}):
            result = estimate_session_cost()

        assert result['total_tokens'] == 0
        assert result['estimated_cost_usd'] == 0.0

    def test_aggregates_token_usage(self):
        """Test that token usage is aggregated across agents."""
        mock_registry = {
            'Developer1': {
                'pid': 12345,
                'role': 'Developer',
                'status': 'RUNNING',
                'cost_data': {
                    'input_tokens': 1000,
                    'output_tokens': 500
                }
            },
            'Tester': {
                'pid': 12346,
                'role': 'Tester',
                'status': 'RUNNING',
                'cost_data': {
                    'input_tokens': 2000,
                    'output_tokens': 1000
                }
            }
        }
        
        with patch('backend.utils.agent_monitor._read_registry_json', return_value=mock_registry):
            result = estimate_session_cost()

        assert result['total_tokens'] == 4500
        assert result['input_tokens'] == 3000
        assert result['output_tokens'] == 1500

    def test_calculates_cost_with_default_rates(self):
        """Test that cost is calculated with default rates."""
        mock_registry = {
            'Architect': {
                'pid': 11111,
                'role': 'Architect',
                'status': 'RUNNING',
                'cost_data': {
                    'input_tokens': 1000000,  # 1M input tokens
                    'output_tokens': 500000   # 500K output tokens
                }
            }
        }
        
        with patch('backend.utils.agent_monitor._read_registry_json', return_value=mock_registry):
            result = estimate_session_cost()

        # Default rates: $0.50 per 1M input, $1.50 per 1M output
        expected_cost = (1.0 * 0.50) + (0.5 * 1.50)  # $0.50 + $0.75 = $1.25
        assert result['estimated_cost_usd'] == expected_cost

    def test_handles_missing_cost_data_gracefully(self):
        """Test that agents without cost_data don't break aggregation."""
        mock_registry = {
            'Developer1': {
                'pid': 12345,
                'role': 'Developer',
                'status': 'RUNNING',
                # No cost_data key
            },
            'Tester': {
                'pid': 12346,
                'role': 'Tester',
                'status': 'RUNNING',
                'cost_data': {
                    'input_tokens': 1000,
                    'output_tokens': 500
                }
            }
        }
        
        with patch('backend.utils.agent_monitor._read_registry_json', return_value=mock_registry):
            result = estimate_session_cost()

        assert result['total_tokens'] == 1500
        assert result['input_tokens'] == 1000
        assert result['output_tokens'] == 500

    def test_custom_cost_rates(self):
        """Test that custom cost rates are used correctly."""
        mock_registry = {
            'Architect': {
                'pid': 11111,
                'role': 'Architect',
                'status': 'RUNNING',
                'cost_data': {
                    'input_tokens': 1000000,
                    'output_tokens': 1000000
                }
            }
        }
        
        with patch('backend.utils.agent_monitor._read_registry_json', return_value=mock_registry):
            # Custom rates: $1.00 per 1M input, $2.00 per 1M output
            result = estimate_session_cost(
                input_rate_per_million=1.00,
                output_rate_per_million=2.00
            )

            expected_cost = (1.0 * 1.00) + (1.0 * 2.00)  # $1.00 + $2.00 = $3.00
            assert result['estimated_cost_usd'] == expected_cost
