# nano_agent_team_selfevolve

English (this page) | [中文文档](README_CN.md)

`nano_agent_team_selfevolve` is a secondary development branch based on [`nano_agent_team`](https://github.com/zczc/nano_agent_team), focused on **unattended self-evolution** -- a multi-agent team autonomously researches, designs, implements, tests, reviews, and ships new features without human intervention.

For full framework documentation (architecture, TUI/CLI details, tool system), refer to the [upstream README](https://github.com/zczc/nano_agent_team).

## What This Repo Adds

Compared with upstream `nano_agent_team`, this repo adds the self-evolution loop and an automated session orchestrator:

- `main.py --evolution`: launches an evolution architect flow.
- `evolve.sh`: round-based loop runner (`bash evolve.sh [max_rounds] [model]`).
- `evolve_session.sh`: full automated session (clean -> evolve -> screen-record -> debug -> README -> push).
- `src/prompts/evolution_architect.md`: prompt protocol for autonomous evolution rounds.
- `backend/tools/evolution_workspace.py`: evolution workspace/branch lifecycle tool.
- `evolution_state.json` + `evolution_history.jsonl` (generated): state tracking and append-only history log.
- `evolution_reports/`: per-round markdown reports.

## Latest Evolution Session

**Session:** `evo_session_20260315_235219`
**Model:** `qwen/qwen3.5-plus` | **Rounds:** 10 | **Result:** 10/10 PASS (0 FAIL)

| Round | Feature | Type | Description |
|-------|---------|------|-------------|
| R1 | **Experience Memory Tool** | FEATURE | Persistent cross-session memory for agents, backed by JSON store |
| R2 | **Code Health Analyzer Tool** | FEATURE | Python code quality metrics (complexity, coupling, size) via AST analysis |
| R3 | **ExperienceMemoryTool Registry** | INTEGRATION | Wired R1's tool into tool_registry.py for both entry points |
| R4 | **Agent Self-Reflection Middleware** | FEATURE | Automatic failure analysis with ReflectionAnalyzer, stores reflections to experience memory |
| R5 | **Agent Status Dashboard** | FEATURE | Real-time agent monitoring with TUI dashboard screen and `/agents` command |
| R6 | **Agent Self-Diagnosis & Recovery** | FEATURE | Diagnosis engine with recovery strategies (Retry, Fallback, CircuitBreaker) as a skill |
| R7 | **AgentMonitorTool Integration** | INTEGRATION | Exposed R5's monitoring as a callable tool for agents |
| R8 | **Session Replay Tool** | FEATURE | Trace capture + replay for debugging agent failures, with TUI `/replay` command |
| R9 | **Agent Diagnosis Tool Integration** | INTEGRATION | Wrapped R6's diagnosis engine as a callable tool |
| R10 | **Tool Explorer & 8-Tool Integration** | FEATURE | Wired 8 existing but unused tools into both entry points |

### Debug Results

- **152/152 tests pass** (2 wiring tests fixed post-evolution: hardcoded paths -> relative paths)
- `python main.py --help` runs cleanly
- All new modules import successfully
- Note: R10 reported creating `tool_explorer.py` (TUI screen) but the file was not committed to git. The 8-tool wiring in main.py and agent_bridge.py is intact.

## Quick Start

### 1. Install

```bash
git clone https://github.com/nanoAgentTeam/nano_agent_team_selfevolve.git
cd nano_agent_team_selfevolve
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure model and API key

Choose at least one provider in:
- `backend/llm_config.json`

Provide API keys via environment variables (recommended), for example:

```bash
export OPENAI_API_KEY="your_key"
export DASHSCOPE_API_KEY="your_key"
```

Or pass a custom key file path:

```bash
python main.py --keys /path/to/keys.json
```

### 3. Run normal mode

```bash
python main.py "Your mission"
```

Optional TUI:

```bash
python tui.py
```

## Self-Evolution Mode

### Start loop

```bash
bash evolve.sh
```

Examples:

```bash
# Run 5 rounds
bash evolve.sh 5

# Run 10 rounds with a specified model
bash evolve.sh 10 qwen/qwen-plus
```

### Full automated session

```bash
bash evolve_session.sh [rounds] [model]
```

This orchestrates the entire pipeline: repo setup -> screen recording -> evolution -> debug -> README -> GitHub push.

### Stop loop safely

```bash
touch .evolution_stop
```

The script checks this flag after each round, cleans it automatically, then exits.

## Outputs and State Files

- `evolution_reports/`: round reports.
- `evolution_state.json`: current summarized state.
- `evolution_history.jsonl`: append-only round history (created during evolution runs).
- `evolution_sessions/`: session snapshots with artifacts.
- `logs/`: archived runtime sessions.

## Project Structure

```
├── main.py                          # CLI entry point (normal + evolution mode)
├── tui.py                           # TUI entry point
├── evolve.sh                        # Evolution loop runner
├── evolve_session.sh                # Full session orchestrator
├── backend/
│   ├── llm/                         # LLM engine, tool registry, middlewares
│   ├── tools/                       # All tools (file ops, search, evolution, analysis...)
│   └── utils/                       # Agent monitor, code metrics, reflection, diagnosis
├── src/
│   ├── core/middlewares/             # Reflection middleware, token tracking, etc.
│   ├── prompts/                     # Role templates and evolution architect prompt
│   └── tui/                         # TUI app, screens, components, slash commands
├── tests/                           # Unit tests for all evolved features
└── evolution_reports/               # Per-round evolution reports
```

## License

See upstream [nano_agent_team](https://github.com/zczc/nano_agent_team) for license details.
