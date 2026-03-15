"""
Agent Self-Reflection Middleware

This middleware monitors task execution and triggers reflection when failures are detected.
It works in conjunction with the ExperienceMemoryTool to store and retrieve learning insights.
"""

from typing import Any, Callable, Dict, Optional
from backend.llm.middleware import StrategyMiddleware
from backend.utils.reflection_analyzer import ReflectionAnalyzer
from backend.tools.experience_memory import ExperienceMemoryTool


class ReflectionMiddleware(StrategyMiddleware):
    """
    Middleware that enables agent self-reflection on task failures.
    
    This middleware intercepts task completion events and:
    1. Detects failures from task result_summary
    2. Analyzes the failure using ReflectionAnalyzer
    3. Saves the reflection insight to ExperienceMemoryTool
    4. Allows the agent to learn from past mistakes
    """
    
    def __init__(self, experience_memory: Optional[ExperienceMemoryTool] = None):
        """
        Initialize the reflection middleware.
        
        Args:
            experience_memory: Optional ExperienceMemoryTool instance. If not provided,
                              a new instance will be created.
        """
        self.analyzer = ReflectionAnalyzer()
        self.experience_memory = experience_memory or ExperienceMemoryTool()
    
    async def __call__(
        self,
        session: Any,
        next_call: Callable
    ) -> Any:
        """
        Process the request and trigger reflection on failures.
        
        Args:
            session: The agent session containing metadata
            next_call: The next middleware/LLM call in the chain
            
        Returns:
            The response from the next call in the chain
        """
        # Call the next middleware/LLM in the chain
        response = await next_call(session)
        
        # Check if current task completed with failure
        current_task = session.metadata.get('current_task', {})
        if current_task:
            task_result = {
                'status': current_task.get('status', ''),
                'result_summary': current_task.get('result_summary', '')
            }
            
            # Check if this looks like a failure
            if self._is_task_failure(task_result):
                # Trigger reflection
                await self._trigger_reflection(session, current_task)
        
        return response
    
    def _is_task_failure(self, task_result: Dict[str, Any]) -> bool:
        """
        Determine if a task result indicates a failure.
        
        Args:
            task_result: Dictionary with status and result_summary
            
        Returns:
            True if the task appears to have failed
        """
        status = task_result.get('status', '')
        result_summary = task_result.get('result_summary', '').lower()
        
        # Explicit failure status
        if status == 'FAILED':
            return True
        
        # Check for failure keywords
        failure_keywords = ['failed', 'error', 'exception', 'timeout', 
                          'connection', 'retry', 'unable', 'could not', 
                          'cannot', 'blocked']
        
        for keyword in failure_keywords:
            if keyword in result_summary:
                return True
        
        return False
    
    async def _trigger_reflection(
        self,
        session: Any,
        current_task: Dict[str, Any]
    ) -> None:
        """
        Trigger reflection on a failed task and save to experience memory.
        
        Args:
            session: The agent session
            current_task: The current task dictionary
        """
        task_id = current_task.get('id', 'unknown')
        task_description = current_task.get('description', 'Unknown task')
        result_summary = current_task.get('result_summary', '')
        
        # Determine error type from result_summary
        error_type = self._extract_error_type(result_summary)
        
        # Prepare execution context
        execution_context = {
            'task_id': task_id,
            'task_description': task_description,
            'error_type': error_type
        }
        
        # Analyze the failure
        task_result = {
            'status': current_task.get('status', ''),
            'result_summary': result_summary
        }
        
        insight = self.analyzer.analyze_failure(task_result, execution_context)
        
        # Format the insight for storage
        insight_text = self._format_insight_for_storage(insight)
        
        # Save to experience memory
        try:
            # Use the tool's execute method with operation="save"
            import uuid
            experience_name = f"reflection_task_{task_id}_{uuid.uuid4().hex[:8]}"
            result = self.experience_memory.execute(
                operation='save',
                name=experience_name,
                content=insight_text,
                tags=['failure', 'learning', 'reflection']
            )
            if not result.get('success'):
                print(f"ReflectionMiddleware: Failed to save experience: {result.get('message')}")
        except Exception as e:
            # Log but don't fail the middleware
            print(f"ReflectionMiddleware: Failed to save experience: {e}")
    
    def _extract_error_type(self, result_summary: str) -> str:
        """
        Extract the error type from a result summary.
        
        Args:
            result_summary: The task result summary string
            
        Returns:
            The extracted error type or 'Unknown'
        """
        import re
        
        # Common error patterns
        error_patterns = [
            (r'TimeoutError', 'TimeoutError'),
            (r'ConnectionError', 'ConnectionError'),
            (r'PermissionError', 'PermissionError'),
            (r'ValueError', 'ValueError'),
            (r'KeyError', 'KeyError'),
            (r'IndexError', 'IndexError'),
            (r'AttributeError', 'AttributeError'),
            (r'ImportError', 'ImportError'),
            (r'FileNotFoundError', 'FileNotFoundError'),
            (r'timeout', 'TimeoutError'),
            (r'connection', 'ConnectionError'),
            (r'permission|auth', 'PermissionError'),
            (r'invalid', 'ValueError'),
        ]
        
        for pattern, error_type in error_patterns:
            if re.search(pattern, result_summary, re.IGNORECASE):
                return error_type
        
        return 'Unknown'
    
    def _format_insight_for_storage(self, insight: Dict[str, Any]) -> str:
        """
        Format a reflection insight for storage in experience memory.
        
        Args:
            insight: The structured insight dictionary
            
        Returns:
            A formatted string for storage
        """
        return (
            f"REFLECTION - Task #{insight['task_id']}: {insight['task_description']}\n"
            f"Error: {insight['error_type']}\n"
            f"What went wrong: {insight['what_went_wrong']}\n"
            f"Lesson: {insight['lesson_learned']}\n"
            f"Next time: {insight['suggested_action']}"
        )
