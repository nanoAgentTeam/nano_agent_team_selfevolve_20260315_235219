"""Tests for ExperienceMemoryTool - TDD approach."""
import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path


class TestExperienceMemoryTool:
    """Test suite for ExperienceMemoryTool following TDD."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def tool(self, temp_data_dir):
        """Create an ExperienceMemoryTool instance with temp storage."""
        # This will fail initially since the tool doesn't exist yet
        from backend.tools.experience_memory import ExperienceMemoryTool
        tool = ExperienceMemoryTool()
        # Override the storage path to use temp directory
        tool._storage_path = Path(temp_data_dir) / "experience_memory.json"
        return tool

    def test_save_experience(self, tool):
        """RED Test 1: Should save an experience with name, content, and tags."""
        result = tool.execute(
            operation="save",
            name="test_insight",
            content="This is a test insight",
            tags=["test", "example"]
        )
        assert result["success"] is True
        assert "saved" in result["message"].lower()

    def test_get_experience(self, tool):
        """RED Test 2: Should retrieve a saved experience by name."""
        # First save
        tool.execute(
            operation="save",
            name="retrieval_test",
            content="Content to retrieve",
            tags=["retrieval"]
        )
        # Then get
        result = tool.execute(operation="get", name="retrieval_test")
        assert result["success"] is True
        assert result["experience"]["name"] == "retrieval_test"
        assert result["experience"]["content"] == "Content to retrieve"
        assert "retrieval" in result["experience"]["tags"]

    def test_get_nonexistent_experience(self, tool):
        """RED Test 3: Should handle getting a non-existent experience."""
        result = tool.execute(operation="get", name="does_not_exist")
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_search_experiences_by_query(self, tool):
        """RED Test 4: Should search experiences by text query."""
        # Save multiple experiences
        tool.execute(operation="save", name="first", content="Python programming tip", tags=["python"])
        tool.execute(operation="save", name="second", content="JavaScript best practice", tags=["javascript"])
        tool.execute(operation="save", name="third", content="Advanced Python techniques", tags=["python", "advanced"])
        
        # Search for "python"
        result = tool.execute(operation="search", query="python")
        assert result["success"] is True
        assert len(result["experiences"]) == 2
        names = [exp["name"] for exp in result["experiences"]]
        assert "first" in names
        assert "third" in names

    def test_search_experiences_by_tags(self, tool):
        """RED Test 5: Should search experiences by tags."""
        tool.execute(operation="save", name="tagged1", content="Content 1", tags=["python", "web"])
        tool.execute(operation="save", name="tagged2", content="Content 2", tags=["python", "api"])
        tool.execute(operation="save", name="tagged3", content="Content 3", tags=["javascript"])
        
        # Search by tag
        result = tool.execute(operation="search", tags=["python"])
        assert result["success"] is True
        assert len(result["experiences"]) == 2

    def test_list_experiences(self, tool):
        """RED Test 6: Should list all saved experiences."""
        tool.execute(operation="save", name="list1", content="First", tags=[])
        tool.execute(operation="save", name="list2", content="Second", tags=[])
        
        result = tool.execute(operation="list")
        assert result["success"] is True
        assert len(result["experiences"]) == 2

    def test_delete_experience(self, tool):
        """RED Test 7: Should delete an experience."""
        # Save then delete
        tool.execute(operation="save", name="to_delete", content="Will be deleted", tags=[])
        result = tool.execute(operation="delete", name="to_delete")
        assert result["success"] is True
        assert "deleted" in result["message"].lower()
        
        # Verify it's gone
        get_result = tool.execute(operation="get", name="to_delete")
        assert get_result["success"] is False

    def test_delete_nonexistent_experience(self, tool):
        """RED Test 8: Should handle deleting non-existent experience."""
        result = tool.execute(operation="delete", name="never_existed")
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_persistence_across_instances(self, temp_data_dir):
        """RED Test 9: Should persist experiences across tool instances."""
        storage_path = Path(temp_data_dir) / "experience_memory.json"
        
        # Create first tool instance and save
        from backend.tools.experience_memory import ExperienceMemoryTool
        tool1 = ExperienceMemoryTool()
        tool1._storage_path = storage_path
        tool1.execute(operation="save", name="persistent", content="Persistent data", tags=["test"])
        
        # Create second tool instance (simulating restart)
        tool2 = ExperienceMemoryTool()
        tool2._storage_path = storage_path
        
        # Should retrieve the saved experience
        result = tool2.execute(operation="get", name="persistent")
        assert result["success"] is True
        assert result["experience"]["content"] == "Persistent data"

    def test_invalid_operation(self, tool):
        """RED Test 10: Should reject invalid operations."""
        result = tool.execute(operation="invalid_op")
        assert result["success"] is False
        assert "Invalid operation" in result["message"]

    def test_save_requires_name(self, tool):
        """RED Test 11: Save operation requires name parameter."""
        result = tool.execute(operation="save", content="No name")
        assert result["success"] is False
        assert "name" in result["message"].lower()

    def test_save_requires_content(self, tool):
        """RED Test 12: Save operation requires content parameter."""
        result = tool.execute(operation="save", name="no_content")
        assert result["success"] is False
        assert "content" in result["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
