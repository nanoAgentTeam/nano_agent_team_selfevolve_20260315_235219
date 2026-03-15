"""
Agent Diagnosis Tool

Wraps the DiagnosisEngine to provide agent health diagnosis capabilities to LLM agents.
"""
from typing import Dict, Any, List

from backend.tools.base import BaseTool
from backend.utils.agent_diagnosis import DiagnosisEngine, DiagnosisResult, AgentHealthStatus


class AgentDiagnosisTool(BaseTool):
    """
    Tool for diagnosing agent health based on performance metrics.
    
    This tool wraps the DiagnosisEngine and provides a natural language interface
    for agents to diagnose health issues and get recommendations.
    """
    
    @property
    def name(self) -> str:
        return "agent_diagnosis"
    
    @property
    def description(self) -> str:
        return (
            "Diagnoses agent health based on performance metrics. "
            "Accepts metrics like error_rate, response_time_avg, success_rate, memory_usage_mb. "
            "Returns health status (healthy/degraded/unhealthy/critical), identified issues, "
            "and actionable recommendations for recovery."
        )
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "error_rate": {
                    "type": "number",
                    "description": "Error rate (0.0 to 1.0). Example: 0.15 means 15% errors",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "response_time_avg": {
                    "type": "number",
                    "description": "Average response time in seconds. Example: 5.2",
                    "minimum": 0.0
                },
                "success_rate": {
                    "type": "number",
                    "description": "Success rate (0.0 to 1.0). Example: 0.85 means 85% success",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "memory_usage_mb": {
                    "type": "number",
                    "description": "Memory usage in megabytes. Example: 512.0",
                    "minimum": 0.0
                }
            },
            "required": ["error_rate", "response_time_avg", "success_rate"],
            "additionalProperties": False
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the diagnosis tool.
        
        Args:
            error_rate: float (0.0 to 1.0)
            response_time_avg: float (seconds)
            success_rate: float (0.0 to 1.0)
            memory_usage_mb: float (optional, megabytes)
        
        Returns:
            Dictionary containing:
                - status: str (healthy|degraded|unhealthy|critical)
                - issues: List[str] (identified issues)
                - recommendations: List[str] (actionable recommendations)
                - summary: str (human-readable health summary)
        """
        # Build metrics dictionary
        metrics = {
            'error_rate': kwargs.get('error_rate', 0.0),
            'response_time_avg': kwargs.get('response_time_avg', 0.0),
            'success_rate': kwargs.get('success_rate', 1.0)
        }
        
        # Add optional memory usage
        if 'memory_usage_mb' in kwargs:
            metrics['memory_usage_mb'] = kwargs['memory_usage_mb']
        
        # Run diagnosis
        engine = DiagnosisEngine()
        result: DiagnosisResult = engine.diagnose(metrics)
        
        # Get human-readable summary
        summary = engine.get_health_summary(metrics)
        
        # Format result for LLM consumption
        return {
            "status": result.status.value,
            "issues": result.issues,
            "recommendations": result.recommendations,
            "summary": summary,
            "metrics": result.metrics
        }
