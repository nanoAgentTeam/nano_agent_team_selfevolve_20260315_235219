"""
Unit tests for SessionReplayTool

Tests the capture, retrieval, and failure point detection functionality.
"""

import pytest
import time
from backend.tools.session_replay import SessionReplayTool


class TestSessionReplayTool:
    """Test suite for SessionReplayTool"""

    def setup_method(self):
        """Set up test fixtures"""
        self.tool = SessionReplayTool()
        self.test_session_id = "test_session_001"
        self.test_agent_name = "TestAgent"

    def teardown_method(self):
        """Clean up after each test"""
        # Clear any traces created during tests
        self.tool._traces.clear()

    def test_capture_trace_records_action(self):
        """Test that capture_trace records an action with all required fields"""
        action_details = {
            "tool": "web_search",
            "query": "test query",
            "result": "success"
        }
        timestamp = time.time()
        
        result = self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name=self.test_agent_name,
            action_type="tool_call",
            action_details=action_details,
            timestamp=timestamp
        )
        
        assert result["status"] == "recorded"
        assert result["session_id"] == self.test_session_id
        assert result["trace_id"] is not None

    def test_get_trace_returns_actions(self):
        """Test that get_trace retrieves recorded actions for a session"""
        # Record multiple actions
        self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name=self.test_agent_name,
            action_type="tool_call",
            action_details={"tool": "web_search", "query": "first"},
            timestamp=time.time()
        )
        self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name=self.test_agent_name,
            action_type="file_edit",
            action_details={"file": "test.py", "change": "added function"},
            timestamp=time.time()
        )
        
        # Retrieve trace
        trace = self.tool.get_trace(session_id=self.test_session_id)
        
        assert trace["session_id"] == self.test_session_id
        assert len(trace["actions"]) == 2
        assert trace["actions"][0]["action_type"] == "tool_call"
        assert trace["actions"][1]["action_type"] == "file_edit"

    def test_get_trace_filters_by_agent(self):
        """Test that get_trace can filter by agent name"""
        # Record actions from different agents
        self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name="Agent1",
            action_type="tool_call",
            action_details={"tool": "web_search"},
            timestamp=time.time()
        )
        self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name="Agent2",
            action_type="tool_call",
            action_details={"tool": "bash"},
            timestamp=time.time()
        )
        
        # Filter by Agent1
        trace = self.tool.get_trace(session_id=self.test_session_id, agent_name="Agent1")
        
        assert len(trace["actions"]) == 1
        assert trace["actions"][0]["agent_name"] == "Agent1"

    def test_get_trace_empty_session(self):
        """Test that get_trace handles non-existent sessions gracefully"""
        trace = self.tool.get_trace(session_id="non_existent_session")
        
        assert trace["session_id"] == "non_existent_session"
        assert len(trace["actions"]) == 0
        assert trace["message"] == "No actions recorded for this session"

    def test_get_failure_point_identifies_failure(self):
        """Test that get_failure_point finds the first failure in trace"""
        # Record a sequence with a failure
        self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name=self.test_agent_name,
            action_type="tool_call",
            action_details={"tool": "web_search", "status": "success"},
            timestamp=time.time()
        )
        self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name=self.test_agent_name,
            action_type="tool_call",
            action_details={"tool": "bash", "status": "failed", "error": "command not found"},
            timestamp=time.time()
        )
        self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name=self.test_agent_name,
            action_type="tool_call",
            action_details={"tool": "read_file", "status": "success"},
            timestamp=time.time()
        )
        
        failure = self.tool.get_failure_point(session_id=self.test_session_id)
        
        assert failure["found"] is True
        assert failure["action_type"] == "tool_call"
        assert failure["action_details"]["status"] == "failed"
        assert failure["action_details"]["error"] == "command not found"

    def test_get_failure_point_no_failure(self):
        """Test that get_failure_point handles sessions with no failures"""
        # Record only successful actions
        self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name=self.test_agent_name,
            action_type="tool_call",
            action_details={"tool": "web_search", "status": "success"},
            timestamp=time.time()
        )
        self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name=self.test_agent_name,
            action_type="file_edit",
            action_details={"file": "test.py", "status": "success"},
            timestamp=time.time()
        )
        
        failure = self.tool.get_failure_point(session_id=self.test_session_id)
        
        assert failure["found"] is False
        assert failure["message"] == "No failures detected in this session"

    def test_get_failure_point_empty_session(self):
        """Test that get_failure_point handles empty sessions"""
        failure = self.tool.get_failure_point(session_id="non_existent_session")
        
        assert failure["found"] is False
        assert "No actions recorded" in failure["message"]

    def test_capture_trace_with_status_field(self):
        """Test that capture_trace handles status field in action_details"""
        result = self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name=self.test_agent_name,
            action_type="tool_call",
            action_details={"tool": "test", "status": "failed", "error": "test error"},
            timestamp=time.time()
        )
        
        assert result["status"] == "recorded"
        
        # Verify the status is preserved in the trace
        trace = self.tool.get_trace(session_id=self.test_session_id)
        assert trace["actions"][0]["action_details"]["status"] == "failed"

    def test_trace_includes_timestamp(self):
        """Test that captured traces include timestamp information"""
        before_time = time.time()
        self.tool.capture_trace(
            session_id=self.test_session_id,
            agent_name=self.test_agent_name,
            action_type="tool_call",
            action_details={"tool": "test"},
            timestamp=before_time
        )
        after_time = time.time()
        
        trace = self.tool.get_trace(session_id=self.test_session_id)
        recorded_timestamp = trace["actions"][0]["timestamp"]
        
        assert before_time <= recorded_timestamp <= after_time

    def test_multiple_sessions_isolated(self):
        """Test that different sessions are kept separate"""
        session1 = "session_1"
        session2 = "session_2"
        
        self.tool.capture_trace(
            session_id=session1,
            agent_name=self.test_agent_name,
            action_type="tool_call",
            action_details={"tool": "web_search"},
            timestamp=time.time()
        )
        self.tool.capture_trace(
            session_id=session2,
            agent_name=self.test_agent_name,
            action_type="tool_call",
            action_details={"tool": "bash"},
            timestamp=time.time()
        )
        
        trace1 = self.tool.get_trace(session_id=session1)
        trace2 = self.tool.get_trace(session_id=session2)
        
        assert len(trace1["actions"]) == 1
        assert len(trace2["actions"]) == 1
        assert trace1["actions"][0]["action_details"]["tool"] == "web_search"
        assert trace2["actions"][0]["action_details"]["tool"] == "bash"
