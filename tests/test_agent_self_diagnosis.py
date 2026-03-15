"""
Tests for Agent Self-Diagnosis & Recovery Skill
"""
import pytest
import sys
import os

# Add workspace to path
sys.path.insert(0, '/Users/zc/PycharmProjects/nano_agent_team_selfevolve_20260315_235219/.blackboard/resources/workspace')

from backend.utils.agent_diagnosis.diagnosis_engine import DiagnosisEngine, AgentHealthStatus
from backend.utils.agent_diagnosis.recovery_strategies import (
    RecoveryStrategy,
    RetryStrategy,
    FallbackStrategy,
    RecoveryManager
)


class TestDiagnosisEngine:
    """Test the diagnosis engine for agent health monitoring"""
    
    def test_diagnosis_engine_initializes(self):
        """RED: Test that DiagnosisEngine can be instantiated"""
        engine = DiagnosisEngine()
        assert engine is not None
    
    def test_diagnose_healthy_agent(self):
        """RED: Test diagnosing a healthy agent returns HEALTHY status"""
        engine = DiagnosisEngine()
        metrics = {
            'error_rate': 0.0,
            'response_time_avg': 1.5,
            'success_rate': 1.0,
            'memory_usage_mb': 256
        }
        result = engine.diagnose(metrics)
        assert result.status == AgentHealthStatus.HEALTHY
    
    def test_diagnose_unhealthy_agent_high_errors(self):
        """RED: Test diagnosing agent with high error rate returns UNHEALTHY"""
        engine = DiagnosisEngine()
        metrics = {
            'error_rate': 0.5,  # 50% error rate
            'response_time_avg': 1.5,
            'success_rate': 0.5,
            'memory_usage_mb': 256
        }
        result = engine.diagnose(metrics)
        assert result.status == AgentHealthStatus.UNHEALTHY
        assert 'high_error_rate' in result.issues
    
    def test_diagnose_degraded_agent_slow_response(self):
        """RED: Test diagnosing agent with slow response returns DEGRADED"""
        engine = DiagnosisEngine()
        metrics = {
            'error_rate': 0.1,
            'response_time_avg': 15.0,  # 15 seconds - slow
            'success_rate': 0.9,
            'memory_usage_mb': 256
        }
        result = engine.diagnose(metrics)
        assert result.status == AgentHealthStatus.DEGRADED
        assert 'slow_response' in result.issues
    
    def test_get_recommendations(self):
        """RED: Test that diagnosis provides actionable recommendations"""
        engine = DiagnosisEngine()
        metrics = {
            'error_rate': 0.5,
            'response_time_avg': 15.0,
            'success_rate': 0.5,
            'memory_usage_mb': 256
        }
        result = engine.diagnose(metrics)
        assert len(result.recommendations) > 0


class TestRecoveryStrategies:
    """Test recovery strategy implementations"""
    
    def test_retry_strategy_initializes(self):
        """RED: Test RetryStrategy can be instantiated"""
        strategy = RetryStrategy(max_retries=3, delay_seconds=1.0)
        assert strategy is not None
        assert strategy.max_retries == 3
    
    def test_retry_strategy_execute(self):
        """RED: Test RetryStrategy executes operation with retries"""
        strategy = RetryStrategy(max_retries=3, delay_seconds=0.01)
        
        attempt_count = 0
        def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = strategy.execute(flaky_operation)
        assert result == "success"
        assert attempt_count == 3
    
    def test_fallback_strategy_initializes(self):
        """RED: Test FallbackStrategy can be instantiated"""
        primary = lambda: None
        fallback = lambda: "fallback_result"
        strategy = FallbackStrategy(primary, fallback)
        assert strategy is not None
    
    def test_fallback_strategy_uses_fallback_on_failure(self):
        """RED: Test FallbackStrategy uses fallback when primary fails"""
        def failing_primary():
            raise Exception("Primary failed")
        
        def working_fallback():
            return "fallback_worked"
        
        strategy = FallbackStrategy(failing_primary, working_fallback)
        result = strategy.execute()
        assert result == "fallback_worked"
    
    def test_recovery_manager_registers_strategies(self):
        """RED: Test RecoveryManager can register and retrieve strategies"""
        manager = RecoveryManager()
        strategy = RetryStrategy(max_retries=3)
        manager.register_strategy('retry', strategy)
        
        retrieved = manager.get_strategy('retry')
        assert retrieved is strategy
    
    def test_recovery_manager_execute_strategy(self):
        """RED: Test RecoveryManager executes registered strategy"""
        manager = RecoveryManager()
        strategy = RetryStrategy(max_retries=2, delay_seconds=0.01)
        manager.register_strategy('retry', strategy)
        
        attempt_count = 0
        def flaky_op():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("fail")
            return "done"
        
        result = manager.execute_strategy('retry', flaky_op)
        assert result == "done"


class TestIntegration:
    """Integration tests for diagnosis and recovery workflow"""
    
    def test_diagnose_and_recover_workflow(self):
        """RED: Test full diagnose -> recommend -> recover workflow"""
        engine = DiagnosisEngine()
        manager = RecoveryManager()
        
        # Register a retry strategy
        manager.register_strategy('retry', RetryStrategy(max_retries=3, delay_seconds=0.01))
        
        # Simulate unhealthy agent
        metrics = {
            'error_rate': 0.5,
            'response_time_avg': 1.5,
            'success_rate': 0.5,
            'memory_usage_mb': 256
        }
        diagnosis = engine.diagnose(metrics)
        
        assert diagnosis.status == AgentHealthStatus.UNHEALTHY
        
        # Execute recovery
        attempt_count = 0
        def operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("transient error")
            return "recovered"
        
        recovery_result = manager.execute_strategy('retry', operation)
        assert recovery_result == "recovered"
