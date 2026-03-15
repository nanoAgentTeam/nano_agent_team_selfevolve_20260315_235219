"""
Agent monitoring utility for the nano_agent_team framework.

Provides functions to monitor agent status, task progress, and cost estimation.
"""

import json
import re
from typing import Dict, List, Any
from pathlib import Path

# Default blackboard path
BLACKBOARD_PATH = Path(__file__).parent.parent.parent / ".blackboard"

def _read_index(filename: str, blackboard_path: Path = None) -> Dict[str, str]:
    """
    Read an index file from the blackboard.

    Args:
        filename: Name of the index file (e.g., 'central_plan.md')
        blackboard_path: Optional path to blackboard directory. Defaults to auto-detection.

    Returns:
        Dictionary with 'content' and 'checksum' keys.
    """
    if blackboard_path is None:
        blackboard_path = BLACKBOARD_PATH

    index_file = blackboard_path / "global_indices" / filename
    content = index_file.read_text()

    # Extract checksum from YAML frontmatter if present
    checksum = ""
    match = re.search(r'checksum:\s*([a-f0-9]+)', content)
    if match:
        checksum = match.group(1)

    return {'content': content, 'checksum': checksum}

def _read_registry_json(registry_path: Path = None) -> Dict[str, Any]:
    """
    Read the registry.json file containing all agent data.

    Args:
        registry_path: Optional path to registry.json file. Defaults to auto-detection.

    Returns:
        Dictionary containing all agent data, or empty dict if file doesn't exist.
    """
    if registry_path is None:
        registry_path = BLACKBOARD_PATH / "registry.json"

    if not registry_path.exists():
        return {}

    try:
        with open(registry_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def get_agent_status_summary(registry_path: Path = None) -> List[Dict[str, Any]]:
    """
    Get a structured summary of all agents in the registry.

    Args:
        registry_path: Optional path to registry.json file. Defaults to auto-detection.

    Returns:
        List of dictionaries containing agent information with keys:
        - name: Agent name
        - pid: Process ID
        - role: Agent role (truncated to first line)
        - status: Current status (RUNNING, DEAD, etc.)
        - verified_status: Verified status (ALIVE, DEAD)
        - start_time: When the agent started (if available)
    """
    registry_data = _read_registry_json(registry_path)

    if not registry_data:
        return []

    result = []
    for name, data in registry_data.items():
        # Extract first line of role (remove newlines and truncate)
        role = data.get('role', '')
        if role:
            role = role.split('\n')[0][:100]

        agent_info = {
            'name': name,
            'pid': data.get('pid'),
            'role': role,
            'status': data.get('status'),
            'verified_status': data.get('verified_status'),
            'start_time': data.get('start_time'),
        }
        result.append(agent_info)

    return result

def get_task_progress_summary(blackboard_path: Path = None) -> Dict[str, Any]:
    """
    Get a summary of task progress from the central plan.

    Args:
        blackboard_path: Optional path to blackboard directory. Defaults to auto-detection.

    Returns:
        Dictionary containing:
        - total: Total number of tasks
        - pending: Number of PENDING tasks
        - in_progress: Number of IN_PROGRESS tasks
        - done: Number of DONE tasks
        - blocked: Number of BLOCKED tasks
        - completion_percentage: Percentage of tasks completed (0-100)
    """
    if blackboard_path is None:
        blackboard_path = BLACKBOARD_PATH

    try:
        index_data = _read_index('central_plan.md', blackboard_path)
        content = index_data['content']

        # Extract JSON-like structure from the markdown file
        # Look for task status patterns
        status_counts = {
            'PENDING': 0,
            'IN_PROGRESS': 0,
            'DONE': 0,
            'BLOCKED': 0
        }

        for status in status_counts.keys():
            count = len(re.findall(rf'"status":\s*"{status}"', content))
            status_counts[status] = count

        total = sum(status_counts.values())
        done = status_counts['DONE']

        completion_percentage = (done / total * 100) if total > 0 else 0.0

        return {
            'total': total,
            'pending': status_counts['PENDING'],
            'in_progress': status_counts['IN_PROGRESS'],
            'done': done,
            'blocked': status_counts['BLOCKED'],
            'completion_percentage': round(completion_percentage, 2)
        }

    except Exception as e:
        # Return empty metrics on error
        return {
            'total': 0,
            'pending': 0,
            'in_progress': 0,
            'done': 0,
            'blocked': 0,
            'completion_percentage': 0.0
        }

def estimate_session_cost(
    input_rate_per_million: float = 0.50,
    output_rate_per_million: float = 1.50,
    registry_path: Path = None
) -> Dict[str, Any]:
    """
    Estimate the total session cost based on token usage from all agents.

    Args:
        input_rate_per_million: Cost per million input tokens (default: $0.50)
        output_rate_per_million: Cost per million output tokens (default: $1.50)
        registry_path: Optional path to registry.json file. Defaults to auto-detection.

    Returns:
        Dictionary containing:
        - total_tokens: Total tokens used
        - input_tokens: Total input tokens
        - output_tokens: Total output tokens
        - estimated_cost_usd: Estimated cost in USD
    """
    registry_data = _read_registry_json(registry_path)

    total_input = 0
    total_output = 0

    for name, data in registry_data.items():
        cost_data = data.get('cost_data', {})
        if cost_data:
            total_input += cost_data.get('input_tokens', 0)
            total_output += cost_data.get('output_tokens', 0)

    total_tokens = total_input + total_output

    # Calculate cost
    input_cost = (total_input / 1_000_000) * input_rate_per_million
    output_cost = (total_output / 1_000_000) * output_rate_per_million
    estimated_cost = input_cost + output_cost

    return {
        'total_tokens': total_tokens,
        'input_tokens': total_input,
        'output_tokens': total_output,
        'estimated_cost_usd': round(estimated_cost, 4)
    }
