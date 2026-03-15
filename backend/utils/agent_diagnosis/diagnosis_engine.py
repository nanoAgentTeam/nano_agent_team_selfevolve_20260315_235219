"""
Agent Diagnosis Engine

Monitors agent health metrics and diagnoses issues.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any


class AgentHealthStatus(Enum):
    """Agent health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class DiagnosisResult:
    """Result of an agent health diagnosis"""
    status: AgentHealthStatus
    issues: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]
    
    def __init__(self, status: AgentHealthStatus, issues: List[str] = None, 
                 recommendations: List[str] = None, metrics: Dict[str, Any] = None):
        self.status = status
        self.issues = issues or []
        self.recommendations = recommendations or []
        self.metrics = metrics or {}


class DiagnosisEngine:
    """
    Engine for diagnosing agent health based on performance metrics.
    
    Monitors:
    - Error rates
    - Response times
    - Success rates
    - Memory usage
    
    Provides actionable recommendations for recovery.
    """
    
    # Thresholds for health status determination
    ERROR_RATE_HIGH = 0.3  # 30% error rate is unhealthy
    ERROR_RATE_WARNING = 0.1  # 10% error rate is degraded
    RESPONSE_TIME_SLOW = 10.0  # 10 seconds is slow
    RESPONSE_TIME_CRITICAL = 30.0  # 30 seconds is critical
    SUCCESS_RATE_LOW = 0.7  # 70% success rate is unhealthy
    SUCCESS_RATE_WARNING = 0.9  # 90% success rate is degraded
    
    def __init__(self):
        """Initialize the diagnosis engine"""
        pass
    
    def diagnose(self, metrics: Dict[str, Any]) -> DiagnosisResult:
        """
        Diagnose agent health based on provided metrics.
        
        Args:
            metrics: Dictionary containing:
                - error_rate: float (0.0 to 1.0)
                - response_time_avg: float (seconds)
                - success_rate: float (0.0 to 1.0)
                - memory_usage_mb: float (megabytes)
        
        Returns:
            DiagnosisResult with status, issues, and recommendations
        """
        issues = []
        recommendations = []
        
        # Extract metrics with defaults
        error_rate = metrics.get('error_rate', 0.0)
        response_time = metrics.get('response_time_avg', 0.0)
        success_rate = metrics.get('success_rate', 1.0)
        memory_usage = metrics.get('memory_usage_mb', 0.0)
        
        # Check error rate
        if error_rate >= self.ERROR_RATE_HIGH:
            issues.append('high_error_rate')
            recommendations.append('Enable retry strategy for transient errors')
            recommendations.append('Check external service dependencies')
        elif error_rate >= self.ERROR_RATE_WARNING:
            issues.append('elevated_error_rate')
            recommendations.append('Monitor error patterns')
        
        # Check response time
        if response_time >= self.RESPONSE_TIME_CRITICAL:
            issues.append('critical_slow_response')
            recommendations.append('Reduce request complexity')
            recommendations.append('Consider caching responses')
        elif response_time >= self.RESPONSE_TIME_SLOW:
            issues.append('slow_response')
            recommendations.append('Optimize prompt length')
            recommendations.append('Check network latency')
        
        # Check success rate
        if success_rate <= self.SUCCESS_RATE_LOW:
            issues.append('low_success_rate')
            recommendations.append('Review task complexity')
            recommendations.append('Enable fallback strategy')
        elif success_rate <= self.SUCCESS_RATE_WARNING:
            issues.append('reduced_success_rate')
            recommendations.append('Analyze failure patterns')
        
        # Determine overall status
        status = self._determine_status(issues)
        
        return DiagnosisResult(
            status=status,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics
        )
    
    def _determine_status(self, issues: List[str]) -> AgentHealthStatus:
        """Determine overall health status from issues"""
        critical_issues = {'critical_slow_response'}
        unhealthy_issues = {'high_error_rate', 'low_success_rate'}
        degraded_issues = {'elevated_error_rate', 'slow_response', 'reduced_success_rate'}
        
        if any(issue in critical_issues for issue in issues):
            return AgentHealthStatus.CRITICAL
        
        if any(issue in unhealthy_issues for issue in issues):
            return AgentHealthStatus.UNHEALTHY
        
        if any(issue in degraded_issues for issue in issues):
            return AgentHealthStatus.DEGRADED
        
        return AgentHealthStatus.HEALTHY
    
    def get_health_summary(self, metrics: Dict[str, Any]) -> str:
        """
        Get a human-readable health summary.
        
        Args:
            metrics: Same as diagnose()
        
        Returns:
            Formatted string summary
        """
        result = self.diagnose(metrics)
        
        status_emoji = {
            AgentHealthStatus.HEALTHY: "✓",
            AgentHealthStatus.DEGRADED: "⚠",
            AgentHealthStatus.UNHEALTHY: "✗",
            AgentHealthStatus.CRITICAL: "✖"
        }
        
        lines = [
            f"Agent Health: {status_emoji.get(result.status, '?')} {result.status.value.upper()}",
            f"Issues: {len(result.issues)}",
            f"Recommendations: {len(result.recommendations)}"
        ]
        
        if result.issues:
            lines.append("Issues:")
            for issue in result.issues:
                lines.append(f"  - {issue}")
        
        return "\n".join(lines)
