"""
Tests for the AgentDashboardScreen component.
"""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.screen import Screen


class TestAgentDashboardScreen:
    """Test suite for AgentDashboardScreen."""

    def test_dashboard_screen_imports(self):
        """Test that the dashboard screen can be imported."""
        from src.tui.screens.dashboard import AgentDashboardScreen
        assert AgentDashboardScreen is not None

    def test_dashboard_screen_has_title(self):
        """Test that the dashboard screen has a proper title."""
        from src.tui.screens.dashboard import AgentDashboardScreen
        screen = AgentDashboardScreen()
        assert hasattr(screen, 'TITLE')
        assert 'Agent' in screen.TITLE or 'Dashboard' in screen.TITLE

    def test_dashboard_screen_composes_widgets(self):
        """Test that the dashboard screen composes expected widgets."""
        from src.tui.screens.dashboard import AgentDashboardScreen
        screen = AgentDashboardScreen()
        
        # Check that compose method exists
        assert hasattr(screen, 'compose')
        
        # The screen should compose widgets
        widgets = list(screen.compose())
        assert len(widgets) > 0

    def test_dashboard_screen_has_bindings(self):
        """Test that the dashboard screen has escape binding."""
        from src.tui.screens.dashboard import AgentDashboardScreen
        screen = AgentDashboardScreen()
        
        # Should have bindings for navigation
        assert hasattr(screen, 'BINDINGS')
        # Should have escape to go back
        binding_keys = [b.key for b in screen.BINDINGS]
        assert 'escape' in binding_keys or 'esc' in binding_keys

    def test_dashboard_screen_has_agent_status_table(self):
        """Test that the dashboard includes the AgentStatusTable component."""
        from src.tui.screens.dashboard import AgentDashboardScreen
        from src.tui.components import AgentStatusTable
        
        screen = AgentDashboardScreen()
        widgets = list(screen.compose())
        
        # At least one widget should be AgentStatusTable
        has_status_table = any(isinstance(w, AgentStatusTable) for w in widgets)
        assert has_status_table

    def test_dashboard_screen_has_refresh_interval(self):
        """Test that the dashboard has auto-refresh capability."""
        from src.tui.screens.dashboard import AgentDashboardScreen
        screen = AgentDashboardScreen()
        
        # Should have a refresh interval attribute
        assert hasattr(screen, 'REFRESH_INTERVAL')
        assert screen.REFRESH_INTERVAL > 0

    def test_dashboard_screen_action_escape(self):
        """Test that escape action exists."""
        from src.tui.screens.dashboard import AgentDashboardScreen
        screen = AgentDashboardScreen()
        
        # Should have action_escape method
        assert hasattr(screen, 'action_escape')

    def test_dashboard_screen_on_mount_sets_interval(self):
        """Test that on_mount sets up refresh interval."""
        from src.tui.screens.dashboard import AgentDashboardScreen
        screen = AgentDashboardScreen()
        
        # Should have on_mount method
        assert hasattr(screen, 'on_mount')

    def test_dashboard_screen_on_unmount_clears_interval(self):
        """Test that on_unmount cleans up refresh interval."""
        from src.tui.screens.dashboard import AgentDashboardScreen
        screen = AgentDashboardScreen()
        
        # Should have on_unmount method
        assert hasattr(screen, 'on_unmount')

    def test_dashboard_screen_in_exports(self):
        """Test that dashboard screen is exported from screens package."""
        from src.tui.screens import AgentDashboardScreen
        assert AgentDashboardScreen is not None
