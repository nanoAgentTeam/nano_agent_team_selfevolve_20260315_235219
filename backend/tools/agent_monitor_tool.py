"""
Agent Monitor Tool - Exposes agent monitoring capabilities to LLM agents.

This tool wraps the backend/utils/agent_monitor.py functions to provide
agent status and health information to LLM agents.
"""

from typing import Any

from backend.tools.base import BaseTool
from backend.utils.agent_monitor import get_agent_status_summary


class AgentMonitorTool(BaseTool):
    """Tool for monitoring agent status and health."""

    @property
    def name(self) -> str:
        return "agent_monitor"

    @property
    def description(self) -> str:
        return (
            "Monitor the status of agents in the swarm. "
            "Use this to check which agents are running, their roles, and status. "
            "Action: 'get_status_summary' (list all agents with their status, role, PID, and verification status)."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The monitoring action to perform. Currently only 'get_status_summary' is supported.",
                    "enum": ["get_status_summary"],
                },
            },
            "required": ["action"],
        }

    def execute(self, action: str) -> dict[str, Any]:
        """
        Execute the monitoring action.

        Args:
            action: The monitoring action to perform

        Returns:
            Dictionary with success status and result data
        """
        try:
            if action == "get_status_summary":
                agents = get_agent_status_summary()
                return {
                    "success": True,
                    "agents": agents,
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}. Valid action: get_status_summary",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
