"""ExperienceMemoryTool - Persistent storage for agent experiences and insights."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.tools.base import BaseTool
from backend.llm.decorators import schema_strict_validator


class ExperienceMemoryTool(BaseTool):
    """Tool for saving, retrieving, and searching agent experiences.
    
    Provides persistent storage for insights, lessons learned, and reusable knowledge
    that agents can accumulate across sessions.
    """
    
    name = "experience_memory"
    description = "Save, retrieve, search, and manage agent experiences and insights. Use this to accumulate knowledge across sessions."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Define the parameters schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["save", "get", "search", "list", "delete"],
                    "description": "The operation to perform: save, get, search, list, or delete"
                },
                "name": {
                    "type": "string",
                    "description": "Unique name/identifier for the experience (required for save, get, delete)"
                },
                "content": {
                    "type": "string",
                    "description": "The experience content/insight (required for save)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for categorization (optional, default: [])"
                },
                "query": {
                    "type": "string",
                    "description": "Text query to search in content (for search operation)"
                }
            },
            "required": ["operation"]
        }
    
    def __init__(self):
        """Initialize the tool with storage path."""
        super().__init__()
        # Use backend/data directory for storage
        self._storage_path = Path(__file__).parent.parent / "data" / "experience_memory.json"
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure the data directory and storage file exist."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._storage_path.exists():
            self._storage_path.write_text(json.dumps({"experiences": []}, indent=2))
    
    def _load_experiences(self) -> List[Dict[str, Any]]:
        """Load experiences from storage."""
        try:
            data = json.loads(self._storage_path.read_text())
            return data.get("experiences", [])
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_experiences(self, experiences: List[Dict[str, Any]]) -> None:
        """Save experiences to storage."""
        data = {"experiences": experiences}
        self._storage_path.write_text(json.dumps(data, indent=2))
    
    def _find_experience(self, name: str) -> Optional[int]:
        """Find experience index by name. Returns None if not found."""
        experiences = self._load_experiences()
        for i, exp in enumerate(experiences):
            if exp.get("name") == name:
                return i
        return None
    
    @schema_strict_validator
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the experience memory operation.
        
        Args:
            operation: One of save, get, search, list, delete
            name: Experience name (for save, get, delete)
            content: Experience content (for save)
            tags: List of tags (for save, optional)
            query: Search query (for search)
            
        Returns:
            Dict with success status and result data
        """
        operation = kwargs.get("operation")
        
        if operation == "save":
            return self._save_experience(kwargs)
        elif operation == "get":
            return self._get_experience(kwargs)
        elif operation == "search":
            return self._search_experiences(kwargs)
        elif operation == "list":
            return self._list_experiences()
        elif operation == "delete":
            return self._delete_experience(kwargs)
        else:
            return {
                "success": False,
                "message": f"Invalid operation: {operation}. Must be one of: save, get, search, list, delete"
            }
    
    def _save_experience(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Save a new experience."""
        name = kwargs.get("name")
        content = kwargs.get("content")
        tags = kwargs.get("tags", [])
        
        if not name:
            return {"success": False, "message": "Missing required parameter: name"}
        if not content:
            return {"success": False, "message": "Missing required parameter: content"}
        
        experiences = self._load_experiences()
        
        # Check if name already exists
        if self._find_experience(name) is not None:
            return {"success": False, "message": f"Experience with name '{name}' already exists. Use delete first to update."}
        
        # Create new experience
        experience = {
            "name": name,
            "content": content,
            "tags": tags if isinstance(tags, list) else [],
            "created_at": str(Path.cwd())  # Simple timestamp alternative
        }
        
        experiences.append(experience)
        self._save_experiences(experiences)
        
        return {
            "success": True,
            "message": f"Experience '{name}' saved successfully",
            "experience": experience
        }
    
    def _get_experience(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve an experience by name."""
        name = kwargs.get("name")
        
        if not name:
            return {"success": False, "message": "Missing required parameter: name"}
        
        experiences = self._load_experiences()
        for exp in experiences:
            if exp.get("name") == name:
                return {
                    "success": True,
                    "experience": exp
                }
        
        return {"success": False, "message": f"Experience '{name}' not found"}
    
    def _search_experiences(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Search experiences by query or tags."""
        query = kwargs.get("query", "").lower()
        tags = kwargs.get("tags", [])
        
        experiences = self._load_experiences()
        results = []
        
        for exp in experiences:
            match = False
            
            # Search in content
            if query and query in exp.get("content", "").lower():
                match = True
            
            # Search in tags
            if tags and any(tag in exp.get("tags", []) for tag in tags):
                match = True
            
            if match:
                results.append(exp)
        
        return {
            "success": True,
            "experiences": results,
            "count": len(results)
        }
    
    def _list_experiences(self) -> Dict[str, Any]:
        """List all experiences."""
        experiences = self._load_experiences()
        return {
            "success": True,
            "experiences": experiences,
            "count": len(experiences)
        }
    
    def _delete_experience(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an experience by name."""
        name = kwargs.get("name")
        
        if not name:
            return {"success": False, "message": "Missing required parameter: name"}
        
        experiences = self._load_experiences()
        index = self._find_experience(name)
        
        if index is None:
            return {"success": False, "message": f"Experience '{name}' not found"}
        
        experiences.pop(index)
        self._save_experiences(experiences)
        
        return {
            "success": True,
            "message": f"Experience '{name}' deleted successfully"
        }
