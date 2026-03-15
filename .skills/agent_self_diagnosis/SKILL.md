---
name: "agent-self-diagnosis"
description: "Enables agents to self-monitor health metrics, diagnose issues, and execute recovery strategies for improved reliability."
usage_policy: "Activate when experiencing repeated failures, performance degradation, or when building fault-tolerant agent workflows."
---
# Agent Self-Diagnosis & Recovery Skill

## Overview

This skill enables agents to monitor their own health, diagnose performance issues, and automatically execute recovery strategies. It provides a systematic approach to maintaining agent reliability and resilience.

## When to Activate

Activate this skill when:
- You notice repeated failures in your operations
- Response times are degrading
- You need to implement fault tolerance in a critical workflow
- You want to proactively monitor agent health metrics
- External services your agent depends on are unreliable

## How to Use

### 1. Import the Module

```python
from backend.utils.agent_diagnosis import (
    DiagnosisEngine,
    AgentHealthStatus,
    RecoveryManager,
    RetryStrategy,
    FallbackStrategy
)
```

### 2. Diagnose Agent Health

```python
# Initialize the diagnosis engine
engine = DiagnosisEngine()

# Collect your agent's metrics
metrics = {
    'error_rate': 0.15,        # 15% of operations failing
    'response_time_avg': 12.5, # Average 12.5 seconds per operation
    'success_rate': 0.85,      # 85% success rate
    'memory_usage_mb': 512     # Memory usage in MB
}

# Get diagnosis
result = engine.diagnose(metrics)

print(f"Status: {result.status.value}")
print(f"Issues: {result.issues}")
print(f"Recommendations: {result.recommendations}")
```

### 3. Execute Recovery Strategies

```python
# Initialize recovery manager
recovery = RecoveryManager()

# Define recovery strategies
def retry_operation():
    # Your retry logic here
    return True

def fallback_operation():
    # Your fallback logic here  
    return True

# Register strategies
recovery.register_strategy('retry', RetryStrategy(retry_operation, max_attempts=3))
recovery.register_strategy('fallback', FallbackStrategy(fallback_operation))

# Execute recovery based on diagnosis
if result.status == AgentHealthStatus.DEGRADED:
    success = recovery.execute('retry')
    if not success:
        success = recovery.execute('fallback')
```

### 4. Monitor Health Continuously

```python
# Check health before critical operations
metrics = collect_current_metrics()
diagnosis = engine.diagnose(metrics)

if diagnosis.status == AgentHealthStatus.CRITICAL:
    # Trigger circuit breaker or alert
    activate_circuit_breaker()
    send_alert("Agent health critical")
elif diagnosis.status == AgentHealthStatus.DEGRADED:
    # Apply recovery strategies
    recovery.execute('retry')
```

## Diagnosis Thresholds

The diagnosis engine uses these thresholds:

| Metric | Healthy | Degraded | Critical |
|--------|---------|----------|----------|
| Error Rate | < 10% | 10-25% | > 25% |
| Response Time (avg) | < 5s | 5-15s | > 15s |
| Success Rate | > 90% | 75-90% | < 75% |

## Recovery Strategies

### RetryStrategy
- Automatically retries failed operations
- Configurable max attempts (default: 3)
- Exponential backoff between retries

### FallbackStrategy
- Switches to alternative implementation
- Used when primary operation consistently fails
- Maintains service availability

### CircuitBreakerStrategy
- Prevents cascading failures
- Opens circuit after threshold failures
- Auto-closes after recovery period

## Example: Building a Resilient Tool

```python
from backend.tools.base import BaseTool
from backend.utils.agent_diagnosis import DiagnosisEngine, RecoveryManager

class ResilientWebSearch(BaseTool):
    name = "resilient_web_search"
    description = "Web search with automatic health monitoring and recovery"
    
    def __init__(self):
        super().__init__()
        self.diagnosis_engine = DiagnosisEngine()
        self.recovery_manager = RecoveryManager()
        self.metrics = {'error_count': 0, 'total_calls': 0, 'total_time': 0}
    
    def execute(self, query: str) -> dict:
        import time
        start = time.time()
        
        try:
            self.metrics['total_calls'] += 1
            result = self._perform_search(query)
            self.metrics['total_time'] += (time.time() - start)
            return result
            
        except Exception as e:
            self.metrics['error_count'] += 1
            
            # Check health and recover
            health = self._check_health()
            if health.status != AgentHealthStatus.HEALTHY:
                return self._recover(e)
            raise
    
    def _check_health(self):
        error_rate = self.metrics['error_count'] / max(self.metrics['total_calls'], 1)
        avg_time = self.metrics['total_time'] / max(self.metrics['total_calls'], 1)
        
        return self.diagnosis_engine.diagnose({
            'error_rate': error_rate,
            'response_time_avg': avg_time,
            'success_rate': 1 - error_rate
        })
    
    def _recover(self, error):
        # Try fallback strategies
        return self.recovery_manager.execute('fallback')
```

## Integration with Agent Workflows

This skill integrates with the nano_agent_team framework by:
1. Providing health metrics to the agent's monitoring middleware
2. Enabling automatic recovery without human intervention
3. Logging diagnosis results for post-mortem analysis
4. Supporting circuit breaker patterns for external service calls

## Best Practices

1. **Monitor Continuously**: Check health metrics before and after critical operations
2. **Set Appropriate Thresholds**: Adjust thresholds based on your use case
3. **Log Everything**: Record all diagnoses and recovery attempts for analysis
4. **Test Recovery**: Regularly test your recovery strategies in production-like environments
5. **Combine with Reflection**: Use self-reflection to improve recovery strategies over time
