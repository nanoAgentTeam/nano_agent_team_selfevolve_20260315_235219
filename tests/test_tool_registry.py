"""Integration tests for tool registry - verifies tools are properly registered."""
import pytest


class TestToolRegistryIntegration:
    """Test suite for verifying tool registry integration."""

    def test_tool_registry_imports_successfully(self):
        """RED Test 1: Tool registry module should import without errors."""
        from backend.llm.tool_registry import ToolRegistry
        assert ToolRegistry is not None

    def test_experience_memory_tool_imports_successfully(self):
        """RED Test 2: ExperienceMemoryTool should import without errors."""
        from backend.tools.experience_memory import ExperienceMemoryTool
        assert ExperienceMemoryTool is not None

    def test_experience_memory_tool_inherits_base_tool(self):
        """RED Test 3: ExperienceMemoryTool should inherit from BaseTool."""
        from backend.tools.experience_memory import ExperienceMemoryTool
        from backend.tools.base import BaseTool
        assert issubclass(ExperienceMemoryTool, BaseTool)

    def test_experience_memory_tool_has_required_properties(self):
        """RED Test 4: ExperienceMemoryTool should have required properties."""
        from backend.tools.experience_memory import ExperienceMemoryTool
        tool = ExperienceMemoryTool()
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'description')
        assert hasattr(tool, 'parameters_schema')
        assert hasattr(tool, 'execute')
        assert callable(tool.execute)
        assert tool.name == "experience_memory"

    def test_tool_registry_has_register_tool_class_method(self):
        """RED Test 5: ToolRegistry should have register_tool_class method."""
        from backend.llm.tool_registry import ToolRegistry
        registry = ToolRegistry()
        assert hasattr(registry, 'register_tool_class')
        assert callable(registry.register_tool_class)

    def test_tool_registry_has_get_all_tool_names(self):
        """RED Test 6: ToolRegistry should have get_all_tool_names method."""
        from backend.llm.tool_registry import ToolRegistry
        registry = ToolRegistry()
        assert hasattr(registry, 'get_all_tool_names')
        assert callable(registry.get_all_tool_names)

    def test_tool_registry_has_create_tool(self):
        """RED Test 7: ToolRegistry should have create_tool method."""
        from backend.llm.tool_registry import ToolRegistry
        registry = ToolRegistry()
        assert hasattr(registry, 'create_tool')
        assert callable(registry.create_tool)

    def test_experience_memory_tool_can_be_manually_registered(self):
        """RED Test 8: ExperienceMemoryTool can be registered in registry."""
        from backend.llm.tool_registry import ToolRegistry
        from backend.tools.experience_memory import ExperienceMemoryTool
        
        registry = ToolRegistry()
        registry.register_tool_class("experience_memory", ExperienceMemoryTool)
        
        # Check that experience_memory is in the registry
        assert "experience_memory" in registry.get_all_tool_names()

    def test_experience_memory_tool_can_be_created_from_registry(self):
        """RED Test 9: ExperienceMemoryTool can be created from registry."""
        from backend.llm.tool_registry import ToolRegistry
        from backend.tools.experience_memory import ExperienceMemoryTool
        
        registry = ToolRegistry()
        registry.register_tool_class("experience_memory", ExperienceMemoryTool)
        
        # Create an instance from registry
        tool_instance = registry.create_tool("experience_memory")
        assert tool_instance is not None
        assert isinstance(tool_instance, ExperienceMemoryTool)

    def test_code_health_analyzer_can_also_be_registered(self):
        """RED Test 10: CodeHealthAnalyzerTool can also be registered (sanity check)."""
        from backend.llm.tool_registry import ToolRegistry
        from backend.tools.code_health_analyzer import CodeHealthAnalyzerTool
        
        registry = ToolRegistry()
        registry.register_tool_class("code_health_analyzer", CodeHealthAnalyzerTool)
        
        assert "code_health_analyzer" in registry.get_all_tool_names()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
