"""Tests for CodeHealthAnalyzerTool - TDD approach."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch


class TestCodeHealthAnalyzerTool:
    """Test suite for CodeHealthAnalyzerTool following TDD."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary Python project for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def tool(self):
        """Create a CodeHealthAnalyzerTool instance."""
        from backend.tools.code_health_analyzer import CodeHealthAnalyzerTool
        return CodeHealthAnalyzerTool()

    def test_tool_has_required_properties(self, tool):
        """RED Test 1: Tool should have name, description, parameters_schema."""
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'description')
        assert hasattr(tool, 'parameters_schema')
        assert tool.name == "code_health_analyzer"
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
        assert isinstance(tool.parameters_schema, dict)

    def test_tool_has_execute_method(self, tool):
        """RED Test 2: Tool should have execute method."""
        assert hasattr(tool, 'execute')
        assert callable(tool.execute)

    def test_execute_analyzes_directory(self, tool, temp_project):
        """RED Test 3: Execute should analyze a directory and return metrics."""
        # Create a simple Python file
        test_file = temp_project / "test.py"
        test_file.write_text("""
def hello():
    print("Hello")

class MyClass:
    pass
""")
        
        # Mock the session
        session = Mock()
        session.agent_state = {"workspace": str(temp_project)}
        
        # Execute the tool
        import asyncio
        result = asyncio.run(tool.execute(session, str(temp_project)))
        
        assert result["success"] is True
        assert "analysis" in result
        assert "summary" in result["analysis"]
        assert result["analysis"]["summary"]["total_files"] >= 1

    def test_execute_handles_nonexistent_path(self, tool):
        """RED Test 4: Execute should handle non-existent paths gracefully."""
        session = Mock()
        session.agent_state = {"workspace": "/tmp"}
        
        import asyncio
        result = asyncio.run(tool.execute(session, "/nonexistent/path"))
        
        assert result["success"] is False
        assert "error" in result

    def test_execute_with_custom_thresholds(self, tool, temp_project):
        """RED Test 5: Execute should accept custom thresholds."""
        # Create a file with a long function
        test_file = temp_project / "long.py"
        lines = ["def very_long_function():\n"]
        for i in range(100):
            lines.append(f"    print({i})\n")
        test_file.write_text("".join(lines))
        
        session = Mock()
        session.agent_state = {"workspace": str(temp_project)}
        
        import asyncio
        result = asyncio.run(tool.execute(
            session, 
            str(temp_project),
            max_function_lines=20,
            max_nesting_depth=3,
            max_parameters=5
        ))
        
        assert result["success"] is True
        assert "smells" in result["analysis"]
        assert len(result["analysis"]["smells"]["long_functions"]) >= 1

    def test_execute_returns_readable_output(self, tool, temp_project):
        """RED Test 6: Execute should return human-readable output."""
        test_file = temp_project / "simple.py"
        test_file.write_text("x = 1\n")
        
        session = Mock()
        session.agent_state = {"workspace": str(temp_project)}
        
        import asyncio
        result = asyncio.run(tool.execute(session, str(temp_project)))
        
        # Check that output is structured and readable
        assert "markdown_output" in result or "text_output" in result
        assert len(result.get("markdown_output", result.get("text_output", ""))) > 0

    def test_tool_inherits_from_base(self, tool):
        """RED Test 7: Tool should inherit from BaseTool."""
        from backend.tools.base import BaseTool
        assert isinstance(tool, BaseTool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
