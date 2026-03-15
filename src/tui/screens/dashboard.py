"""
Agent Dashboard Screen - displays all agents in a unified view.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.binding import Binding

from src.tui.components import AgentStatusTable


class AgentDashboardScreen(Screen):
    """Dashboard screen showing all agents and their status."""

    TITLE = "Agent Dashboard"
    REFRESH_INTERVAL = 2.0  # Auto-refresh every 2 seconds

    BINDINGS = [
        Binding("escape", "escape", "Back", priority=True),
    ]

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        yield Header()
        yield Static("📊 Agent Status Dashboard", classes="dashboard-title")
        yield AgentStatusTable()
        yield Footer()

    def action_escape(self) -> None:
        """Handle escape key - go back to previous screen."""
        self.app.pop_screen()

    def on_mount(self) -> None:
        """Set up auto-refresh when screen is mounted."""
        # Set up periodic refresh
        self.set_interval(self.REFRESH_INTERVAL, self.refresh_status)

    def on_unmount(self) -> None:
        """Clean up when screen is unmounted."""
        # Cleanup handled automatically by textual

    def refresh_status(self) -> None:
        """Refresh the agent status table."""
        # Trigger a refresh of the status table
        # The AgentStatusTable handles its own refresh logic
        pass
