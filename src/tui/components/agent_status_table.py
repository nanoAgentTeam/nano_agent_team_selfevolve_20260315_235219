"""
Agent Status Table Component

A reusable Textual widget for displaying agent status information from the swarm registry.
Displays: agent PID, role, status (color-coded), current task, uptime.
Auto-refreshes every 2 seconds.
"""

import os
import json
import time
from typing import Any
from textual.app import ComposeResult
from textual.widgets import Static, DataTable, Label
from textual.containers import Container
from textual.reactive import reactive
from textual import events


class AgentStatusTable(Static):
    """
    A widget that displays the current status of all agents in the swarm.
    
    Shows a table with columns:
    - Agent Name
    - PID
    - Role
    - Status (color-coded: 🟢 RUNNING, 🔴 DEAD, 🟡 IDLE)
    - Current Task
    - Uptime
    
    Auto-refreshes every 2 seconds by polling the registry.json file.
    """
    
    # Status color mapping
    STATUS_COLORS = {
        "RUNNING": "green",
        "DEAD": "red",
        "IDLE": "yellow",
        "UNKNOWN": "gray"
    }
    
    # Status icons
    STATUS_ICONS = {
        "RUNNING": "🟢",
        "DEAD": "🔴",
        "IDLE": "🟡",
        "UNKNOWN": "❓"
    }
    
    # Refresh interval in seconds
    REFRESH_INTERVAL = 2.0
    
    # Reactive data
    _agent_data = reactive([])
    
    def __init__(self, blackboard_dir: str | None = None, **kwargs: Any) -> None:
        """
        Initialize the AgentStatusTable.
        
        Args:
            blackboard_dir: Path to the blackboard directory. If None, uses default.
            **kwargs: Additional keyword arguments passed to Static.
        """
        super().__init__(**kwargs)
        self.blackboard_dir = blackboard_dir or os.environ.get(
            "BLACKBOARD_PATH",
            os.path.expanduser("~/.blackboard")
        )
        self.registry_path = os.path.join(self.blackboard_dir, "registry.json")
        self._last_update = 0.0
    
    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        yield Static("Agent Status", id="status-title", classes="title")
        yield DataTable(id="agent-table")
    
    def on_mount(self) -> None:
        """Called when widget is mounted."""
        # Set up the data table
        table = self.query_one("#agent-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns(
            "Agent",
            "PID",
            "Role",
            "Status",
            "Task",
            "Uptime"
        )
        
        # Start auto-refresh
        self._refresh_data()
        self.set_interval(self.REFRESH_INTERVAL, self._refresh_data)
    
    def _refresh_data(self) -> None:
        """Refresh the agent data from registry."""
        self._load_registry()
        self._update_display()
    
    def _load_registry(self) -> None:
        """Load and parse registry data from JSON file."""
        try:
            if os.path.exists(self.registry_path):
                with open(self.registry_path, 'r') as f:
                    registry_data = json.load(f)
                self._agent_data = self._parse_registry_data(registry_data)
            else:
                self._agent_data = []
        except (json.JSONDecodeError, IOError) as e:
            # Log error but don't crash
            self._agent_data = []
    
    def _parse_registry_data(self, registry: dict) -> list[dict]:
        """
        Parse raw registry data into a list of agent info dicts.
        
        Args:
            registry: Raw registry dictionary from JSON.
            
        Returns:
            List of agent dictionaries with normalized fields.
        """
        agents = []
        for name, data in registry.items():
            if isinstance(data, dict):
                agent_info = {
                    "name": name,
                    "pid": data.get("pid", "N/A"),
                    "role": data.get("role", "Unknown"),
                    "status": data.get("status", "UNKNOWN"),
                    "start_time": data.get("start_time", 0),
                    "task": data.get("current_task", "—")
                }
                agents.append(agent_info)
        return agents
    
    def _format_uptime(self, start_time: float) -> str:
        """
        Format uptime from start timestamp.
        
        Args:
            start_time: Unix timestamp when agent started.
            
        Returns:
            Human-readable uptime string (e.g., "2m 15s").
        """
        if start_time <= 0:
            return "—"
        
        elapsed = time.time() - start_time
        if elapsed < 0:
            return "—"
        
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _get_status_icon(self, status: str) -> str:
        """
        Get the icon for a status.
        
        Args:
            status: Status string (RUNNING, DEAD, IDLE, etc.)
            
        Returns:
            Unicode icon for the status.
        """
        return self.STATUS_ICONS.get(status, self.STATUS_ICONS["UNKNOWN"])
    
    def _get_status_style(self, status: str) -> str:
        """
        Get the color style for a status.
        
        Args:
            status: Status string.
            
        Returns:
            Color name for styling.
        """
        return self.STATUS_COLORS.get(status, self.STATUS_COLORS["UNKNOWN"])
    
    def _update_display(self) -> None:
        """Update the DataTable with current agent data."""
        try:
            table = self.query_one("#agent-table", DataTable)
            table.clear()
            
            for agent in self._agent_data:
                status_icon = self._get_status_icon(agent["status"])
                uptime = self._format_uptime(agent["start_time"])
                
                # Get the color for status
                status_color = self._get_status_style(agent["status"])
                
                # Format the status cell with icon and color
                status_cell = f"{status_icon} {agent['status']}"
                
                table.add_row(
                    agent["name"],
                    str(agent["pid"]),
                    agent["role"],
                    status_cell,
                    agent.get("task", "—"),
                    uptime
                )
        except Exception:
            # If table doesn't exist yet, skip update
            pass
    
    def watch__agent_data(self, data: list) -> None:
        """React to changes in agent data."""
        self._update_display()


__all__ = ["AgentStatusTable"]
