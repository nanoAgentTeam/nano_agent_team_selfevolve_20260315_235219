"""
Shared slash command handling logic for TUI
"""
from typing import Optional, Any
from textual.app import App
from textual.widgets import Static
from textual.containers import ScrollableContainer

from .state import state, AgentMode
from .screens.dashboard import AgentDashboardScreen
from .screens.session_replay import SessionReplayScreen

def handle_slash_command(app: App, command: str, source: str = "session", context: Any = None) -> bool:
    """
    Handle slash commands like /iterations, /status, /help
    
    Args:
        app: The TUI App instance (for notifications)
        command: The full command string
        source: Source of the command (typically "session")
        context: Optional context (e.g., SessionScreen instance for accessing chat area)
        
    Returns:
        bool: True if command was handled, False otherwise
    """
    if not command.startswith("/"):
        return False
        
    parts = command.split()
    cmd = parts[0].lower()
    args = parts[1:]
    
    if cmd == "/iterations":
        if not args:
            current = state.swarm_max_iterations
            app.notify(f"Current iterations: {current}", severity="information")
        else:
            try:
                val = int(args[0])
                state.swarm_max_iterations = val
                app.notify(f"Swarm iterations set to {state.swarm_max_iterations}", severity="information")
                
                # If in session, try to update running agent config
                if source == "session" and context and hasattr(context, "agent") and context.agent:
                     if context.agent.config:
                         context.agent.config.swarm_max_iterations = state.swarm_max_iterations
                         # Re-initialize swarm agent to pick up change if not running
                         if not context.agent.is_running:
                             context.agent._initialize_swarm_agent()
            except ValueError:
                app.notify("Invalid number for iterations", severity="error")
        return True
                
    elif cmd == "/status":
        mode = "Swarm" if state.agent_mode == AgentMode.SWARM else "Chat"
        iters = state.swarm_max_iterations
        model = state.get_model_key() or "Default"
        app.notify(f"Mode: {mode} | Model: {model} | Swarm Iterations: {iters}", severity="information")
        return True

    elif cmd == "/exit":
        app.notify("Exiting...", severity="information")
        app.exit()
        return True
        
    elif cmd == "/agents":
        # Open the agent dashboard screen
        app.push_screen(AgentDashboardScreen())
        return True

    elif cmd == "/replay":
        # Open the session replay screen to view execution traces
        # Optional: /replay <session_id> to view a specific session
        session_id = " ".join(args).strip() if args else (app.session.session_id if app.session else None)
        if session_id:
            screen = SessionReplayScreen()
            app.push_screen(screen)
            # Load the session after pushing the screen
            screen.load_session(session_id)
            return True
        else:
            if source == "session" and context:
                context["status_message"] = "No session available for replay"
                context["status_style"] = "error"
            return True

    elif cmd == "/help":
        help_text = """
Available commands:
/iterations <n> - Set max swarm iterations (10-1000)
/status - Show current configuration
/agents - Open agent dashboard
/replay [session_id] - Open session replay to view execution traces
/exit - Exit the application
/help - Show this help message
        """
        if source == "session" and context:
            # Display help as a system message in session
            try:
                chat_area = context.query_one("#chat-area", ScrollableContainer)
                chat_area.mount(Static(help_text, classes="system-message"))
                chat_area.scroll_end(animate=False)
            except Exception:
                app.notify("Available: /iterations <n>, /status", severity="information")
        else:
            # Use notifications as fallback
            app.notify("Available: /iterations <n>, /status", severity="information")
        return True
        
    else:
        app.notify(f"Unknown command: {cmd}", severity="error")
        return True
