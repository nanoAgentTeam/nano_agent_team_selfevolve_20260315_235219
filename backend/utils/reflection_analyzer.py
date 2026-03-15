"""
Reflection Analyzer - Analyzes task failures and generates structured insights for agent learning.
"""

import re
from typing import Dict, Any, Optional


class ReflectionAnalyzer:
    """
    Analyzes task execution results to extract learning insights.
    
    This utility examines failed tasks and generates structured reflections
    that can be stored in experience memory for future reference.
    """
    
    # Keywords that indicate failure patterns
    FAILURE_KEYWORDS = [
        'failed', 'error', 'exception', 'timeout', 'connection',
        'retry', 'unable', 'could not', 'cannot', 'blocked'
    ]
    
    # Common error types and their suggested actions
    ERROR_PATTERNS = {
        r'timeout': 'Consider increasing timeout or implementing exponential backoff',
        r'connection|connect': 'Verify network connectivity and endpoint availability',
        r'permission|auth': 'Check credentials and access permissions',
        r'not found|404': 'Verify the resource exists before accessing',
        r'rate.limit|too many': 'Implement rate limiting or request throttling',
        r'invalid|validation': 'Validate inputs before sending requests',
        r'memory|oom': 'Process data in smaller chunks',
        r'disk|space': 'Clean up temporary files or increase storage',
    }
    
    def analyze_failure(
        self,
        task_result: Dict[str, Any],
        execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a failed task and generate structured insight.
        
        Args:
            task_result: The task result dictionary with status and result_summary
            execution_context: Context about the task execution including task_id, description, error_type
            
        Returns:
            A dictionary containing structured reflection insight
        """
        result_summary = task_result.get('result_summary', '')
        task_id = execution_context.get('task_id', 'unknown')
        task_description = execution_context.get('task_description', 'Unknown task')
        error_type = execution_context.get('error_type', 'Unknown')
        
        # Analyze what went wrong
        what_went_wrong = self._extract_failure_description(result_summary, error_type)
        
        # Extract lesson learned
        lesson_learned = self._generate_lesson(what_went_wrong, task_description)
        
        # Suggest action for future
        suggested_action = self._suggest_action(what_went_wrong)
        
        return {
            'task_id': task_id,
            'task_description': task_description,
            'error_type': error_type,
            'what_went_wrong': what_went_wrong,
            'lesson_learned': lesson_learned,
            'suggested_action': suggested_action,
            'original_summary': result_summary
        }
    
    def _extract_failure_description(
        self,
        result_summary: str,
        error_type: str
    ) -> str:
        """Extract a concise description of what went wrong."""
        # Try to extract specific error message
        error_match = re.search(r'(?:error|exception|failed):\s*(.+?)(?:\.|$)', result_summary, re.IGNORECASE)
        if error_match:
            return error_match.group(1).strip()
        
        # Fall back to error type + snippet
        if error_type != 'Unknown':
            return f"{error_type}: {result_summary[:100]}"
        
        return result_summary[:150] if len(result_summary) > 150 else result_summary
    
    def _generate_lesson(self, what_went_wrong: str, task_description: str) -> str:
        """Generate a lesson learned from the failure."""
        lessons = []
        
        # Check for timeout issues
        if 'timeout' in what_went_wrong.lower():
            lessons.append("Long-running operations need timeout handling and progress reporting")
        
        # Check for connection issues
        if 'connection' in what_went_wrong.lower() or 'connect' in what_went_wrong.lower():
            lessons.append("External dependencies should have fallback strategies")
        
        # Check for validation issues
        if 'invalid' in what_went_wrong.lower() or 'validation' in what_went_wrong.lower():
            lessons.append("Input validation should happen before execution")
        
        # Check for permission issues
        if 'permission' in what_went_wrong.lower() or 'auth' in what_went_wrong.lower():
            lessons.append("Credentials and permissions must be verified upfront")
        
        # Default lesson if no specific pattern matched
        if not lessons:
            lessons.append("Failures provide opportunities to improve error handling")
        
        return "; ".join(lessons)
    
    def _suggest_action(self, what_went_wrong: str) -> str:
        """Suggest a concrete action to prevent similar failures."""
        what_went_wrong_lower = what_went_wrong.lower()
        
        for pattern, action in self.ERROR_PATTERNS.items():
            if re.search(pattern, what_went_wrong_lower):
                return action
        
        return "Review error handling and add appropriate retry/fallback logic"
    
    def generate_reflection_prompt(self, failure_info: Dict[str, Any]) -> str:
        """
        Generate a reflection prompt for the agent to contemplate.
        
        Args:
            failure_info: Dictionary containing task description, error_type, result_summary
            
        Returns:
            A string prompt for agent reflection
        """
        task_desc = failure_info.get('task_description', 'Unknown task')
        error_type = failure_info.get('error_type', 'Unknown')
        summary = failure_info.get('result_summary', 'No details')
        
        prompt = f"""
=== REFLECTION PROMPT ===

Task: {task_desc}
Error Type: {error_type}
Result Summary: {summary}

Questions to consider:
1. What went wrong?
2. Could this have been prevented with better planning?
3. What should be done differently next time?
4. Is there a pattern here that applies to other tasks?

========================
"""
        return prompt.strip()
    
    def is_failure(self, task_result: Dict[str, Any]) -> bool:
        """
        Determine if a task result indicates a failure.
        
        Args:
            task_result: The task result dictionary
            
        Returns:
            True if the task appears to have failed
        """
        status = task_result.get('status', '')
        result_summary = task_result.get('result_summary', '').lower()
        
        # Explicit failure status
        if status == 'FAILED':
            return True
        
        # Check for failure keywords in result_summary
        for keyword in self.FAILURE_KEYWORDS:
            if keyword in result_summary:
                return True
        
        return False
