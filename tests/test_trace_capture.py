"""
Tests for the trace_capture utility module.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
from datetime import datetime


class TestTraceCapture:
    """Tests for trace_capture utility functions."""

    def test_module_imports_successfully(self):
        """Test that the trace_capture module can be imported."""
        from backend.utils import trace_capture
        assert hasattr(trace_capture, 'TraceCapture')

    def test_trace_capture_initializes_with_session_id(self):
        """Test that TraceCapture initializes with a session ID."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session-123")

        assert capture.session_id == "test-session-123"
        assert capture.traces == []

    def test_trace_capture_generates_session_id_if_not_provided(self):
        """Test that TraceCapture generates a session ID if not provided."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture()

        assert capture.session_id is not None
        assert len(capture.session_id) > 0

    def test_record_tool_call_captures_trace(self):
        """Test that tool calls are recorded as traces."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session")
        
        capture.record_tool_call(
            tool_name="web_search",
            input_data={"query": "test query"},
            output_data={"results": ["result1", "result2"]},
            duration_ms=150
        )

        assert len(capture.traces) == 1
        trace = capture.traces[0]
        assert trace['type'] == 'tool_call'
        assert trace['tool_name'] == 'web_search'
        assert trace['input'] == {"query": "test query"}
        assert trace['output'] == {"results": ["result1", "result2"]}
        assert trace['duration_ms'] == 150
        assert 'timestamp' in trace

    def test_record_llm_interaction_captures_trace(self):
        """Test that LLM interactions are recorded as traces."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session")
        
        capture.record_llm_interaction(
            model="gpt-4",
            input_messages=[{"role": "user", "content": "Hello"}],
            output_response="Hi there!",
            tokens_used={"input": 10, "output": 5},
            duration_ms=500
        )

        assert len(capture.traces) == 1
        trace = capture.traces[0]
        assert trace['type'] == 'llm_interaction'
        assert trace['model'] == "gpt-4"
        assert trace['input_messages'] == [{"role": "user", "content": "Hello"}]
        assert trace['output_response'] == "Hi there!"
        assert trace['tokens_used'] == {"input": 10, "output": 5}
        assert trace['duration_ms'] == 500

    def test_record_state_change_captures_trace(self):
        """Test that state changes are recorded as traces."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session")
        
        capture.record_state_change(
            state_type="task_status",
            old_value="PENDING",
            new_value="IN_PROGRESS",
            metadata={"task_id": 5}
        )

        assert len(capture.traces) == 1
        trace = capture.traces[0]
        assert trace['type'] == 'state_change'
        assert trace['state_type'] == "task_status"
        assert trace['old_value'] == "PENDING"
        assert trace['new_value'] == "IN_PROGRESS"
        assert trace['metadata'] == {"task_id": 5}

    def test_get_traces_returns_all_traces(self):
        """Test that get_traces returns all recorded traces."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session")
        
        capture.record_tool_call("tool1", {}, {}, 100)
        capture.record_llm_interaction("model1", [], "response", {}, 200)
        capture.record_state_change("type1", "old", "new", {})

        traces = capture.get_traces()

        assert len(traces) == 3

    def test_get_traces_filtered_by_type(self):
        """Test that traces can be filtered by type."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session")
        
        capture.record_tool_call("tool1", {}, {}, 100)
        capture.record_llm_interaction("model1", [], "response", {}, 200)
        capture.record_tool_call("tool2", {}, {}, 150)

        tool_traces = capture.get_traces(trace_type="tool_call")

        assert len(tool_traces) == 2
        assert all(t['type'] == 'tool_call' for t in tool_traces)

    def test_get_traces_filtered_by_time_range(self):
        """Test that traces can be filtered by time range."""
        from backend.utils.trace_capture import TraceCapture
        import time

        capture = TraceCapture(session_id="test-session")
        
        capture.record_tool_call("tool1", {}, {}, 100)
        time.sleep(0.01)  # Small delay to ensure different timestamps
        mid_timestamp = datetime.now().isoformat()
        time.sleep(0.01)
        capture.record_tool_call("tool2", {}, {}, 150)

        # Get traces after the midpoint
        traces = capture.get_traces(start_time=mid_timestamp)

        assert len(traces) == 1
        assert traces[0]['tool_name'] == 'tool2'

    def test_export_traces_to_json(self, tmp_path):
        """Test that traces can be exported to JSON file."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session")
        capture.record_tool_call("tool1", {"key": "value"}, {"result": "data"}, 100)
        
        output_path = tmp_path / "traces.json"
        capture.export_traces(output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['session_id'] == "test-session"
        assert len(data['traces']) == 1
        assert data['traces'][0]['tool_name'] == 'tool1'

    def test_export_traces_includes_metadata(self, tmp_path):
        """Test that exported traces include metadata."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session")
        capture.record_tool_call("tool1", {}, {}, 100)
        
        output_path = tmp_path / "traces.json"
        capture.export_traces(output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'exported_at' in data
        assert 'trace_count' in data
        assert data['trace_count'] == 1

    def test_load_traces_from_json(self, tmp_path):
        """Test that traces can be loaded from JSON file."""
        from backend.utils.trace_capture import TraceCapture

        # Create a trace file
        trace_data = {
            'session_id': 'loaded-session',
            'traces': [
                {
                    'type': 'tool_call',
                    'tool_name': 'loaded_tool',
                    'input': {},
                    'output': {},
                    'duration_ms': 50,
                    'timestamp': datetime.now().isoformat()
                }
            ]
        }
        
        trace_file = tmp_path / "loaded_traces.json"
        with open(trace_file, 'w') as f:
            json.dump(trace_data, f)

        capture = TraceCapture.load_from_file(trace_file)

        assert capture.session_id == 'loaded-session'
        assert len(capture.traces) == 1
        assert capture.traces[0]['tool_name'] == 'loaded_tool'

    def test_clear_traces(self):
        """Test that traces can be cleared."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session")
        capture.record_tool_call("tool1", {}, {}, 100)
        capture.record_tool_call("tool2", {}, {}, 150)

        assert len(capture.traces) == 2

        capture.clear_traces()

        assert len(capture.traces) == 0

    def test_get_trace_summary(self):
        """Test that trace summary provides correct statistics."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session")
        capture.record_tool_call("tool1", {}, {}, 100)
        capture.record_tool_call("tool2", {}, {}, 200)
        capture.record_llm_interaction("model1", [], "response", {"input": 10, "output": 5}, 300)

        summary = capture.get_summary()

        assert summary['total_traces'] == 3
        assert summary['tool_calls'] == 2
        assert summary['llm_interactions'] == 1
        assert summary['state_changes'] == 0
        assert 'total_duration_ms' in summary


class TestTraceCaptureIntegration:
    """Integration tests for trace_capture with blackboard."""

    def test_auto_save_to_blackboard(self, tmp_path):
        """Test that traces can be auto-saved to blackboard resources."""
        from backend.utils.trace_capture import TraceCapture

        capture = TraceCapture(session_id="test-session")
        capture.record_tool_call("tool1", {}, {}, 100)
        
        # Export to blackboard resources directory
        resources_dir = tmp_path / "resources" / "traces"
        resources_dir.mkdir(parents=True)
        output_path = resources_dir / "test-session.json"
        
        capture.export_traces(output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data['session_id'] == 'test-session'
