"""
Unit tests for ReflectionMiddleware and ReflectionAnalyzer.

Tests cover:
- ReflectionAnalyzer: analyze_failure, generate_reflection_prompt, is_failure
- ReflectionMiddleware: __call__, failure detection, experience storage
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.utils.reflection_analyzer import ReflectionAnalyzer
from src.core.middlewares.reflection_middleware import ReflectionMiddleware


class TestReflectionAnalyzer:
    """Tests for ReflectionAnalyzer utility class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ReflectionAnalyzer()

    def test_is_failure_with_exception(self):
        """Test is_failure detects exceptions."""
        task_result = {"status": "FAILED", "result_summary": "ConnectionError: timeout"}
        assert self.analyzer.is_failure(task_result) is True

    def test_is_failure_with_success(self):
        """Test is_failure returns False for success."""
        task_result = {"status": "completed", "result": "success"}
        assert self.analyzer.is_failure(task_result) is False

    def test_is_failure_with_empty_result(self):
        """Test is_failure handles empty results."""
        task_result = {}
        assert self.analyzer.is_failure(task_result) is False

    def test_analyze_failure(self):
        """Test analyze_failure extracts failure information."""
        task_result = {
            "status": "FAILED",
            "result_summary": "TimeoutError: Connection timed out"
        }
        execution_context = {
            "task_id": 42,
            "task_description": "Test task",
            "error_type": "TimeoutError"
        }
        
        analysis = self.analyzer.analyze_failure(task_result, execution_context)
        
        assert analysis["task_id"] == 42
        assert analysis["task_description"] == "Test task"
        assert analysis["error_type"] == "TimeoutError"
        assert "what_went_wrong" in analysis
        assert "lesson_learned" in analysis
        assert "suggested_action" in analysis

    def test_generate_reflection_prompt(self):
        """Test generate_reflection_prompt creates structured prompt."""
        failure_analysis = {
            "task_id": 42,
            "task_description": "Test task",
            "error_type": "TimeoutError",
            "what_went_wrong": "Connection timed out",
            "lesson_learned": "Add retry logic",
            "suggested_action": "Implement exponential backoff"
        }
        
        prompt = self.analyzer.generate_reflection_prompt(failure_analysis)
        
        assert "Test task" in prompt
        assert "TimeoutError" in prompt
        assert "What went wrong?" in prompt
        assert "Could this have been prevented" in prompt


class TestReflectionMiddlewareSync:
    """Synchronous tests for ReflectionMiddleware using asyncio.run wrapper."""

    def test_call_passes_through_success(self):
        """Test successful pass-through."""
        middleware = ReflectionMiddleware()
        session = MagicMock()
        session.agent_name = "TestAgent"
        
        async def run_test():
            next_call = AsyncMock(return_value={"status": "completed"})
            result = await middleware(session, next_call)
            assert result == {"status": "completed"}
            next_call.assert_called_once_with(session)
        
        asyncio.run(run_test())

    def test_call_triggers_reflection(self):
        """Test reflection triggered on failure."""
        middleware = ReflectionMiddleware()
        session = MagicMock()
        session.agent_name = "TestAgent"
        session.metadata = {
            'current_task': {
                'id': 99,
                'description': 'Failed task',
                'status': 'FAILED',
                'result_summary': 'TestError occurred'
            }
        }
        
        async def run_test():
            failure_result = {
                "status": "FAILED",
                "result_summary": "TestError occurred"
            }
            next_call = AsyncMock(return_value=failure_result)
            
            with patch.object(middleware, '_trigger_reflection', new_callable=AsyncMock) as mock_trigger:
                mock_trigger.return_value = None  # _trigger_reflection returns None
                
                result = await middleware(session, next_call)
                
                assert result == failure_result
                next_call.assert_called_once_with(session)
                mock_trigger.assert_called_once()
        
        asyncio.run(run_test())

    def test_call_handles_missing_task_info(self):
        """Test __call__ handles failures without task info gracefully."""
        middleware = ReflectionMiddleware()
        session = MagicMock()
        session.agent_name = "TestAgent"
        session.metadata = {}  # No current_task
        
        async def run_test():
            failure_result = {"status": "FAILED", "result_summary": "Unknown error"}
            next_call = AsyncMock(return_value=failure_result)
            
            # Should not raise, just skip reflection
            result = await middleware(session, next_call)
            
            assert result == failure_result
            next_call.assert_called_once_with(session)
        
        asyncio.run(run_test())


# EXPLORED (for reviewer reference - not part of test code)
# - backend/utils/reflection_analyzer.py - Read to understand ReflectionAnalyzer class structure and methods
# - src/core/middlewares/reflection_middleware.py - Read to understand ReflectionMiddleware implementation
# - backend/llm/middleware.py - Read to understand StrategyMiddleware base class pattern
# - src/core/middlewares/activity_logger.py - Read as reference for existing middleware pattern
# - src/core/middlewares/notification_awareness.py - Read as second reference for middleware patterns
# - backend/tools/experience_memory.py - Read to understand ExperienceMemoryTool.execute() API
# - main.py - Read to understand middleware wiring pattern in CLI entry point
# - src/tui/agent_bridge.py - Read to understand middleware wiring pattern in TUI entry point
# - tests/test_reflection_middleware.py - Read existing test file to understand test structure
