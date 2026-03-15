"""
Trace Capture Utility - Automatic trace recording for agent actions.

This module provides utilities for capturing and storing execution traces,
including tool calls, LLM interactions, and state changes.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class TraceCapture:
    """
    Captures and stores execution traces for agent actions.
    
    Traces include:
    - Tool calls (name, input, output, duration)
    - LLM interactions (model, messages, response, tokens, duration)
    - State changes (type, old value, new value, metadata)
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize a trace capture instance.
        
        Args:
            session_id: Optional session identifier. If not provided, a UUID is generated.
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.traces: list[dict[str, Any]] = []

    def record_tool_call(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        duration_ms: int
    ) -> None:
        """
        Record a tool call trace.
        
        Args:
            tool_name: Name of the tool that was called.
            input_data: Input parameters passed to the tool.
            output_data: Output data returned by the tool.
            duration_ms: Execution duration in milliseconds.
        """
        trace = {
            'type': 'tool_call',
            'tool_name': tool_name,
            'input': input_data,
            'output': output_data,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat()
        }
        self.traces.append(trace)

    def record_llm_interaction(
        self,
        model: str,
        input_messages: list[dict[str, str]],
        output_response: str,
        tokens_used: dict[str, int],
        duration_ms: int
    ) -> None:
        """
        Record an LLM interaction trace.
        
        Args:
            model: Name of the LLM model used.
            input_messages: List of input messages (role, content).
            output_response: The LLM's response.
            tokens_used: Dictionary with 'input' and 'output' token counts.
            duration_ms: Execution duration in milliseconds.
        """
        trace = {
            'type': 'llm_interaction',
            'model': model,
            'input_messages': input_messages,
            'output_response': output_response,
            'tokens_used': tokens_used,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat()
        }
        self.traces.append(trace)

    def record_state_change(
        self,
        state_type: str,
        old_value: Any,
        new_value: Any,
        metadata: dict[str, Any]
    ) -> None:
        """
        Record a state change trace.
        
        Args:
            state_type: Type of state that changed (e.g., 'task_status').
            old_value: Previous value of the state.
            new_value: New value of the state.
            metadata: Additional metadata about the change.
        """
        trace = {
            'type': 'state_change',
            'state_type': state_type,
            'old_value': old_value,
            'new_value': new_value,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
        self.traces.append(trace)

    def get_traces(
        self,
        trace_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get recorded traces, optionally filtered.
        
        Args:
            trace_type: Filter by trace type ('tool_call', 'llm_interaction', 'state_change').
            start_time: Filter traces after this ISO timestamp.
            end_time: Filter traces before this ISO timestamp.
            
        Returns:
            List of traces matching the filters.
        """
        result = self.traces
        
        if trace_type is not None:
            result = [t for t in result if t.get('type') == trace_type]
        
        if start_time is not None:
            result = [t for t in result if t.get('timestamp', '') >= start_time]
        
        if end_time is not None:
            result = [t for t in result if t.get('timestamp', '') <= end_time]
        
        return result

    def clear_traces(self) -> None:
        """Clear all recorded traces."""
        self.traces = []

    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of recorded traces.
        
        Returns:
            Dictionary with trace statistics.
        """
        tool_calls = sum(1 for t in self.traces if t.get('type') == 'tool_call')
        llm_interactions = sum(1 for t in self.traces if t.get('type') == 'llm_interaction')
        state_changes = sum(1 for t in self.traces if t.get('type') == 'state_change')
        total_duration = sum(t.get('duration_ms', 0) for t in self.traces)
        
        return {
            'total_traces': len(self.traces),
            'tool_calls': tool_calls,
            'llm_interactions': llm_interactions,
            'state_changes': state_changes,
            'total_duration_ms': total_duration
        }

    def export_traces(self, output_path: Path) -> None:
        """
        Export traces to a JSON file.
        
        Args:
            output_path: Path to the output JSON file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'session_id': self.session_id,
            'exported_at': datetime.now().isoformat(),
            'trace_count': len(self.traces),
            'traces': self.traces
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, file_path: Path) -> 'TraceCapture':
        """
        Load traces from a JSON file.
        
        Args:
            file_path: Path to the JSON file containing traces.
            
        Returns:
            A TraceCapture instance with loaded traces.
        """
        file_path = Path(file_path)
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        capture = cls(session_id=data.get('session_id'))
        capture.traces = data.get('traces', [])
        
        return capture
