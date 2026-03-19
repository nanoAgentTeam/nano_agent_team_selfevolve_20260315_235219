"""Test that SessionReplayTool is properly wired into both entry points."""
import pytest


def test_session_replay_tool_importable():
    """Verify SessionReplayTool can be imported."""
    from backend.tools.session_replay import SessionReplayTool
    assert SessionReplayTool is not None


def test_session_replay_tool_in_main_py():
    """Verify SessionReplayTool is registered in main.py via add_tool()."""
    # Read main.py and check for SessionReplayTool registration
    import os
    with open(os.path.join(os.path.dirname(__file__), '..', 'main.py'), 'r') as f:
        content = f.read()
    
    # Check for import
    assert 'from backend.tools.session_replay import SessionReplayTool' in content or 'SessionReplayTool' in content, \
        "SessionReplayTool should be imported in main.py"
    
    # Check for add_tool call
    assert 'add_tool(SessionReplayTool' in content or 'add_tool(SessionReplayTool())' in content, \
        "SessionReplayTool should be added via add_tool() in main.py"


def test_session_replay_tool_in_agent_bridge():
    """Verify SessionReplayTool is registered in agent_bridge.py."""
    # Read agent_bridge.py and check for SessionReplayTool registration
    import os
    with open(os.path.join(os.path.dirname(__file__), '..', 'src', 'tui', 'agent_bridge.py'), 'r') as f:
        content = f.read()
    
    # Check for import or reference
    assert 'SessionReplayTool' in content, \
        "SessionReplayTool should be referenced in agent_bridge.py"
    
    # Check for add_tool call in _initialize_swarm_agent or _initialize_chat_engine
    assert 'add_tool(SessionReplayTool' in content or 'add_tool(SessionReplayTool())' in content, \
        "SessionReplayTool should be added via add_tool() in agent_bridge.py"
