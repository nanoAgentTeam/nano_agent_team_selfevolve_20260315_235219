"""
SessionReplayTool - Capture and replay agent execution traces for debugging.

This tool allows agents to record their actions during execution and later
retrieve those traces to understand what happened, especially when failures occur.
"""

import time
from typing import Any, Dict, List, Optional
from backend.tools.base import BaseTool


class SessionReplayTool(BaseTool):
    """
    Tool for capturing and retrieving agent execution traces.
    
    Enables debugging by recording all agent actions and identifying
    where failures occurred in a session.
    """
    
    name = "session_replay"
    description = """
    Capture and retrieve agent execution traces for debugging purposes.
    
    Use this tool to:
    1. Record actions during agent execution (capture_trace)
    2. Retrieve the full trace of a session (get_trace)
    3. Find where a failure occurred (get_failure_point)
    
    Essential for understanding agent behavior and debugging failures.
    """
    
    # In-memory storage for traces (session_id -> list of actions)
    _traces: Dict[str, List[Dict[str, Any]]] = {}
    
    def __init__(self):
        super().__init__()
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """
        Define the tool's parameters based on the method being called.
        """
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["capture_trace", "get_trace", "get_failure_point"],
                    "description": "The method to call"
                },
                "session_id": {
                    "type": "string",
                    "description": "Unique identifier for the session"
                },
                "agent_name": {
                    "type": "string",
                    "description": "Name of the agent performing the action (for capture_trace)"
                },
                "action_type": {
                    "type": "string",
                    "description": "Type of action (e.g., 'tool_call', 'file_edit', 'decision') (for capture_trace)"
                },
                "action_details": {
                    "type": "object",
                    "description": "Details about the action (for capture_trace)"
                },
                "timestamp": {
                    "type": "number",
                    "description": "Unix timestamp of the action (for capture_trace)"
                }
            },
            "required": ["method", "session_id"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool based on the method parameter.
        
        Args:
            method: The method to call (capture_trace, get_trace, get_failure_point)
            session_id: Unique identifier for the session
            **kwargs: Additional parameters based on method
            
        Returns:
            Dict containing the result of the operation
        """
        method = kwargs.get("method")
        session_id = kwargs.get("session_id")
        
        if method == "capture_trace":
            return self.capture_trace(
                session_id=session_id,
                agent_name=kwargs.get("agent_name", "unknown"),
                action_type=kwargs.get("action_type", "unknown"),
                action_details=kwargs.get("action_details", {}),
                timestamp=kwargs.get("timestamp", time.time())
            )
        elif method == "get_trace":
            return self.get_trace(
                session_id=session_id,
                agent_name=kwargs.get("agent_name")
            )
        elif method == "get_failure_point":
            return self.get_failure_point(
                session_id=session_id,
                agent_name=kwargs.get("agent_name")
            )
        else:
            return {
                "status": "error",
                "message": f"Unknown method: {method}. Valid methods: capture_trace, get_trace, get_failure_point"
            }
    
    def capture_trace(
        self,
        session_id: str,
        agent_name: str,
        action_type: str,
        action_details: Dict[str, Any],
        timestamp: float
    ) -> Dict[str, Any]:
        """
        Record an action in the session trace.
        
        Args:
            session_id: Unique identifier for the session
            agent_name: Name of the agent performing the action
            action_type: Type of action (e.g., 'tool_call', 'file_edit', 'decision')
            action_details: Details about the action
            timestamp: Unix timestamp of the action
            
        Returns:
            Dict with status and trace_id
        """
        if session_id not in self._traces:
            self._traces[session_id] = []
        
        trace_entry = {
            "trace_id": f"{session_id}_{len(self._traces[session_id])}",
            "session_id": session_id,
            "agent_name": agent_name,
            "action_type": action_type,
            "action_details": action_details,
            "timestamp": timestamp
        }
        
        self._traces[session_id].append(trace_entry)
        
        return {
            "status": "recorded",
            "session_id": session_id,
            "trace_id": trace_entry["trace_id"]
        }
    
    def get_trace(
        self,
        session_id: str,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve the full trace of actions for a session.
        
        Args:
            session_id: Unique identifier for the session
            agent_name: Optional filter by agent name
            
        Returns:
            Dict containing session_id and list of actions
        """
        if session_id not in self._traces:
            return {
                "session_id": session_id,
                "actions": [],
                "message": "No actions recorded for this session"
            }
        
        actions = self._traces[session_id]
        
        # Filter by agent_name if provided
        if agent_name:
            actions = [a for a in actions if a["agent_name"] == agent_name]
        
        return {
            "session_id": session_id,
            "actions": actions,
            "total_actions": len(actions)
        }
    
    def get_failure_point(
        self,
        session_id: str,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find the first failure point in a session trace.
        
        Searches through the trace to find actions with status='failed'
        or action_details containing error information.
        
        Args:
            session_id: Unique identifier for the session
            agent_name: Optional filter by agent name
            
        Returns:
            Dict containing failure information or message if no failure found
        """
        if session_id not in self._traces:
            return {
                "found": False,
                "message": "No actions recorded for this session"
            }
        
        actions = self._traces[session_id]
        
        # Filter by agent_name if provided
        if agent_name:
            actions = [a for a in actions if a["agent_name"] == agent_name]
        
        # Search for failure
        for action in actions:
            action_details = action.get("action_details", {})
            
            # Check for explicit failure status
            if action_details.get("status") == "failed":
                return {
                    "found": True,
                    "trace_id": action["trace_id"],
                    "action_type": action["action_type"],
                    "agent_name": action["agent_name"],
                    "action_details": action_details,
                    "timestamp": action["timestamp"]
                }
            
            # Check for error field
            if "error" in action_details:
                return {
                    "found": True,
                    "trace_id": action["trace_id"],
                    "action_type": action["action_type"],
                    "agent_name": action["agent_name"],
                    "action_details": action_details,
                    "timestamp": action["timestamp"]
                }
        
        return {
            "found": False,
            "message": "No failures detected in this session"
        }
