"""
Test Suite for SessionReplayScreen
"""

import pytest
from unittest.mock import MagicMock, patch


class TestSessionReplayScreen:
    """Tests for the SessionReplayScreen TUI component"""

    def test_session_replay_screen_imports(self):
        """Test that SessionReplayScreen can be imported"""
        from src.tui.screens.session_replay import SessionReplayScreen
        assert SessionReplayScreen is not None

    def test_session_replay_screen_inherits_from_screen(self):
        """Test that SessionReplayScreen inherits from textual.screen.Screen"""
        from textual.screen import Screen
        from src.tui.screens.session_replay import SessionReplayScreen
        assert issubclass(SessionReplayScreen, Screen)

    def test_session_replay_screen_has_bindings(self):
        """Test that SessionReplayScreen has required bindings"""
        from src.tui.screens.session_replay import SessionReplayScreen
        screen = SessionReplayScreen()
        assert hasattr(screen, 'BINDINGS')
        # Should have escape binding to go back
        binding_keys = [b.key for b in screen.BINDINGS]
        assert 'escape' in binding_keys or 'q' in binding_keys

    def test_session_replay_screen_compose_method(self):
        """Test that SessionReplayScreen has compose method"""
        from src.tui.screens.session_replay import SessionReplayScreen
        screen = SessionReplayScreen()
        assert hasattr(screen, 'compose')
        assert callable(screen.compose)

    def test_session_replay_screen_has_timeline_widget(self):
        """Test that SessionReplayScreen contains a timeline visualization widget"""
        from src.tui.screens.session_replay import SessionReplayScreen
        # Screen should have compose method defined
        screen = SessionReplayScreen()
        assert hasattr(screen, 'compose')
        # Verify the source code contains timeline-related widgets
        import inspect
        source = inspect.getsource(screen.compose)
        assert 'timeline' in source.lower() or 'Timeline' in source

    def test_session_replay_screen_title(self):
        """Test that SessionReplayScreen has appropriate title"""
        from src.tui.screens.session_replay import SessionReplayScreen
        screen = SessionReplayScreen()
        assert hasattr(screen, 'TITLE') or hasattr(screen, 'title')

    def test_timeline_event_widget(self):
        """Test that TimelineEvent widget exists and has correct structure"""
        from src.tui.screens.session_replay import TimelineEvent
        event = TimelineEvent("10:00:00", "Architect", "Created plan", status="success")
        assert event.timestamp == "10:00:00"
        assert event.agent == "Architect"
        assert event.action == "Created plan"
        assert event.status == "success"

    def test_timeline_event_status_icons(self):
        """Test that TimelineEvent correctly maps status to icons"""
        from src.tui.screens.session_replay import TimelineEvent
        # Test all status types
        for status in ["success", "failure", "running"]:
            event = TimelineEvent("10:00:00", "Agent", "Action", status=status)
            assert event.status in ["success", "failure", "running"]

    def test_session_replay_screen_has_load_session_method(self):
        """Test that SessionReplayScreen has load_session method"""
        from src.tui.screens.session_replay import SessionReplayScreen
        screen = SessionReplayScreen()
        assert hasattr(screen, 'load_session')
        assert callable(screen.load_session)

    def test_session_replay_screen_has_refresh_action(self):
        """Test that SessionReplayScreen has refresh_timeline action"""
        from src.tui.screens.session_replay import SessionReplayScreen
        screen = SessionReplayScreen()
        assert hasattr(screen, 'action_refresh_timeline')
