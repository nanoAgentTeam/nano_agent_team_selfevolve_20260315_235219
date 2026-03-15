"""Tests for the /replay slash command."""

import pytest
from unittest.mock import MagicMock, patch


class TestReplaySlashCommand:
    """Test suite for the /replay slash command functionality."""

    @patch('src.tui.slash_commands.SessionReplayScreen')
    def test_replay_command_exists_in_handler(self, mock_screen_class):
        """Test that /replay command is recognized by the slash command handler."""
        from src.tui.slash_commands import handle_slash_command
        
        mock_screen = MagicMock()
        mock_screen_class.return_value = mock_screen
        
        app = MagicMock()
        app.session = MagicMock()
        app.session.session_id = "test-session-123"
        
        # Test that /replay command is handled (returns True)
        result = handle_slash_command(app, "/replay", source="session")
        
        assert result is True, "/replay command should be handled and return True"
        assert mock_screen.load_session.called

    @patch('src.tui.slash_commands.SessionReplayScreen')
    def test_replay_command_pushes_session_replay_screen(self, mock_screen_class):
        """Test that /replay command pushes the SessionReplay screen."""
        from src.tui.slash_commands import handle_slash_command
        
        mock_screen = MagicMock()
        mock_screen_class.return_value = mock_screen
        
        app = MagicMock()
        app.session = MagicMock()
        app.session.session_id = "test-session-123"
        app.push_screen = MagicMock()
        
        handle_slash_command(app, "/replay", source="session")
        
        # Verify push_screen was called
        assert app.push_screen.called, "push_screen should be called for /replay command"
        assert app.push_screen.call_args[0][0] == mock_screen

    @patch('src.tui.slash_commands.SessionReplayScreen')
    def test_replay_command_with_session_id_argument(self, mock_screen_class):
        """Test that /replay command works with an optional session ID argument."""
        from src.tui.slash_commands import handle_slash_command
        
        mock_screen = MagicMock()
        mock_screen_class.return_value = mock_screen
        
        app = MagicMock()
        app.session = MagicMock()
        app.session.session_id = "current-session"
        app.push_screen = MagicMock()
        
        # Test with explicit session ID
        result = handle_slash_command(app, "/replay some-other-session", source="session")
        
        assert result is True, "/replay with session ID should be handled"
        # Verify load_session was called with the correct session ID
        mock_screen.load_session.assert_called_with("some-other-session")

    @patch('src.tui.slash_commands.SessionReplayScreen')
    def test_replay_command_uses_current_session_by_default(self, mock_screen_class):
        """Test that /replay uses current session ID when no argument provided."""
        from src.tui.slash_commands import handle_slash_command
        
        mock_screen = MagicMock()
        mock_screen_class.return_value = mock_screen
        
        app = MagicMock()
        app.session = MagicMock()
        app.session.session_id = "default-session-id"
        app.push_screen = MagicMock()
        
        handle_slash_command(app, "/replay", source="session")
        
        # Verify it was called - the screen should receive the session ID
        assert app.push_screen.called
        mock_screen.load_session.assert_called_with("default-session-id")
