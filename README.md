# nano_agent_team_selfevolve

English (this page) | [中文文档](README_CN.md)

`nano_agent_team_selfevolve` is a lightweight secondary development branch based on [`nano_agent_team`](https://github.com/zczc/nano_agent_team), focused on adding an unattended self-evolution workflow.

For full framework documentation (architecture, TUI/CLI details, tool system), refer to the [upstream README](https://github.com/zczc/nano_agent_team).

## What This Repo Adds

Compared with upstream `nano_agent_team`, this repo mainly adds and wires the self-evolution loop:

- `main.py --evolution`: launches an evolution architect flow.
- `evolve.sh`: round-based loop runner (`bash evolve.sh [max_rounds] [model]`).
- `src/prompts/evolution_architect.md`: prompt protocol for autonomous evolution rounds.
- `backend/tools/evolution_workspace.py`: evolution workspace/branch lifecycle tool.
- `evolution_state.json` + `evolution_history.jsonl` (generated): state tracking and append-only history log.
- `evolution_reports/`: per-round markdown reports.

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

### Stop loop safely

```bash
touch .evolution_stop
```

The script checks this flag after each round, cleans it automatically, then exits.

## Outputs and State Files

- `evolution_reports/`: round reports.
- `evolution_state.json`: current summarized state.
- `evolution_history.jsonl`: append-only round history (created during evolution runs).
- `logs/`: archived runtime sessions.

## Notes

- Run evolution mode from a clean Git working branch.
- Each successful round typically creates an `evolution/r<round>-<timestamp>` branch.
- `evolve.sh` always tries to return to the starting branch after each round for safety.
