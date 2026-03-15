# nano_agent_team — Living System Design

> This document is maintained by the self-evolution process.
> Each PASS round appends to Evolution Changelog and updates the Component Map.
> Auditor agents read this first to avoid redundant scanning.

---

## Architecture Overview

nano_agent_team is a multi-agent swarm framework where:
- **Watchdog / Architect** — orchestrates the mission, spawns worker agents, monitors via blackboard
- **Worker agents** — spawned as separate processes, claim tasks from `central_plan.md`, execute and report
- **Blackboard** — shared state at `.blackboard/`: `global_indices/` (coordination), `resources/` (artifacts)
- **LLM Engine** — `backend/llm/engine.py`: streaming, middleware chain, tool dispatch, skill injection
- **Middlewares** — `src/core/middlewares/`: intercept LLM stream before/after each turn
- **Tools** — `backend/tools/`: registered in `tool_registry.py`, injected per agent role
- **Skills** — `.skills/<name>/SKILL.md`: activated on demand via `activate_skill` tool

### Request Flow
```
User mission
  → main.py (Watchdog + middleware chain)
    → AgentEngine.run() loop
      → LLM API (streaming)
        → StrategyMiddleware chain (WatchdogGuard, RequestMonitor, ...)
      → Tool dispatch (spawn_swarm_agent, blackboard, bash, ...)
        → Worker agent subprocess
          → AgentEngine.run() loop (sub-engine)
```

---

## Component Map

### Entry Points
| File | Purpose |
|------|---------|
| `main.py` | CLI entry: parses args, initializes Config, builds Watchdog + middleware chain |
| `evolve.sh` | Evolution loop: calls `main.py --evolution` repeatedly |
| `src/core/agent_wrapper.py` | SwarmAgent: wraps AgentEngine with blackboard, registry, tool setup |

### LLM Layer (`backend/llm/`)
| File | Purpose |
|------|---------|
| `engine.py` | Core LLM loop: streaming, tool call parsing, skill injection — **protected** |
| `providers.py` | LLMFactory: creates OpenAI/Anthropic/Gemini clients |
| `middleware.py` | StrategyMiddleware base class |
| `skill_registry.py` | Loads `.skills/*/SKILL.md`, exposes `get_skill(name)` |
| `tool_registry.py` | Registers all tools, creates per-agent tool instances |

### Middlewares (`src/core/middlewares/`)
| File | Wired Into | Purpose |
|------|-----------|---------|
| `watchdog_guard.py` | `main.py` (Watchdog only) | Enforces spawn/edit rules; injects persistence reminders |
| `request_monitor.py` | `main.py` (Watchdog only) | Tracks API request counts |
| `context_overflow.py` | `backend/llm/engine.py` | Handles context length overflow |
| `cost_tracker.py` | `main.py` (Watchdog only) | Monitors and reports token usage and estimated costs for LLM API calls |

### Tools (`backend/tools/`)
| File | Registered In | Used By |
|------|--------------|---------|
| `subagent.py` | `tool_registry.py` | Architect (legacy in-process subagent) |
| `activate_skill.py` | `tool_registry.py` | All agents |
| `evolution_workspace.py` | injected in `main.py` evolution block | Watchdog (evolution mode only) |
| `experience_memory.py` | `main.py`, `src/tui/agent_bridge.py` | All agents (persistent memory across sessions) |

### Source Tools (`src/tools/`)
| File | Purpose |
|------|---------|
| `spawn_tool.py` | `spawn_swarm_agent`: spawns agent subprocess, waits for RUNNING handshake |
| `blackboard_tool.py` | `blackboard`: create/read/update/append indices |
| `check_swarm_status_tool.py` | `check_swarm_status`: reads registry.json + process liveness |
| `wait_tool.py` | `wait`: sleep + optional new-message trigger |
| `finish_tool.py` | `finish`: terminates agent loop |

### Infrastructure (`backend/infra/`)
| File | Purpose |
|------|---------|
| `envs/local.py` | LocalEnvironment: bash, file ops, safety checks, auto_approve_patterns |
| `config.py` | Config: loads `llm_config.json`, `keys.json`, `tui_state.json` |
| `provider_registry.py` | Known providers and their API base URLs |

### Utilities (`backend/utils/`)
| File | Purpose |
|------|---------|
| `agent_diagnosis/diagnosis_engine.py` | DiagnosisEngine: monitors agent health metrics and diagnoses issues |
| `agent_diagnosis/recovery_strategies.py` | Recovery strategies: RetryStrategy, FallbackStrategy, CircuitBreakerStrategy, RecoveryManager |

### Skills (`.skills/`)
| Skill | Trigger | Used By |
|-------|---------|---------|
| `test-driven-development` | When implementing any feature/bugfix | Developer agent |
| `verification-before-completion` | Before claiming work is done | Tester agent |
| `systematic-debugging` | When encountering a bug or test failure | Developer agent |
| `dispatching-parallel-agents` | When multiple independent tasks exist | Architect |
| `executing-plans` | When executing a written plan | Worker agents |
| `brainstorming` | Before creative/feature work | Architect |
| `using-superpowers` | Start of any session | All agents |
| `agent-self-diagnosis` | When monitoring agent health or implementing fault tolerance | Developer, Architect |

---

## Known Gaps & Opportunities

*(Updated by Auditor each round. Remove entries once addressed.)*

- No persistent agent memory across rounds (each agent starts fresh)
- `evolution_workspace.py` commit message format is minimal
- No structured logging of tool call latencies

---

## Evolution Changelog

*(Each PASS round appends here. Newest at top.)*

### Round 1 — Cost Tracking Middleware (FEATURE)
**Changed**: src/core/middlewares/cost_tracker.py, src/core/middlewares/__init__.py, main.py, docs/system_design.md, tests/test_cost_tracker.py
**What it does**: Adds a middleware that monitors and reports token usage and estimated costs for LLM API calls
**Wired into**: main.py (Watchdog middleware chain) and documented in system_design.md

### Round 1 — Experience Memory Tool (FEATURE)
**Changed**: backend/tools/experience_memory.py, tests/test_experience_memory.py, main.py, src/tui/agent_bridge.py, docs/system_design.md
**What it does**: Provides agents with persistent memory capabilities to save, retrieve, search, and manage experiences across sessions
**Wired into**: main.py (Watchdog) and src/tui/agent_bridge.py (TUI)

<!-- rounds appended below by evolution process -->

### Round 5 — Agent Status Dashboard (FEATURE)
**Changed**: backend/utils/agent_monitor.py, backend/utils/__init__.py, src/tui/components/agent_status_table.py, src/tui/components/__init__.py, src/tui/screens/dashboard.py, src/tui/screens/__init__.py, src/tui/slash_commands.py, tests/test_agent_monitor.py, tests/test_agent_status_table.py, tests/test_dashboard_screen.py
**What it does**: Real-time dashboard showing agent status (RUNNING/DEAD/IDLE), PID, role, task, uptime with auto-refresh and /agents slash command.
**Wired into**: src/tui/slash_commands.py (dashboard screen), backend/utils/__init__.py (utilities exported)

### Round 2 — Code Health Analyzer Tool - new tool and utility for analyzing Python project code quality metrics (auto-logged 2026-03-15T16:28:03Z)
**Changed**: backend/llm/tool_registry.py, main.py, src/tui/agent_bridge.py, backend/tools/code_health_analyzer.py, backend/utils/code_metrics.py, tests/test_code_health_analyzer.py, tests/test_code_metrics.py
**What it does**: Code Health Analyzer Tool - new tool and utility for analyzing Python project code quality metrics
**Wired into**: (not documented — check Wire-in Checklist next round)

### Round 3 — Register ExperienceMemoryTool in tool_registry.py (INTEGRATION round) (auto-logged 2026-03-15T16:44:42Z)
**Changed**: backend/llm/tool_registry.py, tests/test_tool_registry.py
**What it does**: Register ExperienceMemoryTool in tool_registry.py (INTEGRATION round)
**Wired into**: (not documented — check Wire-in Checklist next round)

### Round 4 — Implement Agent Self-Reflection Middleware with ReflectionAnalyzer utility and ReflectionMiddleware (auto-logged 2026-03-15T17:16:17Z)
**Changed**: backend/data/experience_memory.json, backend/utils/__init__.py, main.py, src/core/middlewares/__init__.py, src/tui/agent_bridge.py, IMPLEMENTATION_SUMMARY.md, backend/utils/reflection_analyzer.py, src/core/middlewares/reflection_middleware.py, tests/test_reflection_middleware.py
**What it does**: Implement Agent Self-Reflection Middleware with ReflectionAnalyzer utility and ReflectionMiddleware
**Wired into**: (not documented — check Wire-in Checklist next round)

### Round 6 — Agent Self-Diagnosis & Recovery Skill (FEATURE)
**Changed**: backend/utils/agent_diagnosis/diagnosis_engine.py, backend/utils/agent_diagnosis/recovery_strategies.py, backend/utils/agent_diagnosis/__init__.py, .skills/agent_self_diagnosis/SKILL.md, tests/test_agent_self_diagnosis.py, docs/system_design.md
**What it does**: Provides agents with self-monitoring capabilities to diagnose health issues (error rates, response times, success rates) and execute recovery strategies (retry, fallback, circuit breaker)
**Wired into**: .skills/ directory (auto-discovered by skill_registry.py), documented in system_design.md
