"""
Session Replay Screen - Timeline visualization for agent execution traces
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Label, Button
from textual.containers import Vertical, Horizontal, VerticalScroll, Container
from textual.binding import Binding
from textual.reactive import reactive


class TimelineEvent(Static):
    """A single event in the timeline visualization"""

    def __init__(self, timestamp: str, agent: str, action: str, status: str = "success", **kwargs):
        """
        Initialize a timeline event.
        
        Args:
            timestamp: Time of the event
            agent: Agent name
            action: Action description
            status: "success", "failure", or "running"
        """
        super().__init__(**kwargs)
        self.timestamp = timestamp
        self.agent = agent
        self.action = action
        self.status = status

    def compose(self) -> ComposeResult:
        """Compose the timeline event widget"""
        status_icon = {"success": "✓", "failure": "✗", "running": "→"}.get(self.status, "•")
        status_class = f"status-{self.status}"
        yield Static(f"[{self.timestamp}] {status_icon} {self.agent}: {self.action}", classes=f"timeline-event {status_class}")


class SessionReplayScreen(Screen):
    """Screen for replaying and visualizing agent session execution traces"""

    TITLE = "Session Replay"
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("q", "app.pop_screen", "Quit", show=True),
        Binding("r", "refresh_timeline", "Refresh", show=True),
        Binding("f", "toggle_filter", "Filter", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Compose the session replay screen layout"""
        yield Header()
        with Vertical(id="main-container"):
            # Title and controls
            with Horizontal(id="controls-bar"):
                yield Label("Session Replay - Timeline Visualization", id="title-label")
                yield Button("Refresh", id="refresh-btn", variant="primary")
                yield Button("Filter", id="filter-btn", variant="default")
            
            # Timeline container
            with VerticalScroll(id="timeline-container"):
                yield Static("No session selected. Use /replay <session_id> to view.", id="timeline-placeholder")
            
            # Status bar
            yield Static("Events: 0 | Agents: 0 | Duration: 0s", id="status-bar")
        
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button.id == "refresh-btn":
            self.action_refresh_timeline()
        elif event.button.id == "filter-btn":
            self.action_toggle_filter()

    def action_refresh_timeline(self) -> None:
        """Refresh the timeline display"""
        self.notify("Timeline refreshed")

    def action_toggle_filter(self) -> None:
        """Toggle filter options"""
        self.notify("Filter options toggled")

    def load_session(self, session_id: str) -> None:
        """
        Load and display a session's execution trace.
        
        Args:
            session_id: The session identifier to load
        """
        # This will be wired to the SessionReplayTool in a future iteration
        self.notify(f"Loading session: {session_id}")
