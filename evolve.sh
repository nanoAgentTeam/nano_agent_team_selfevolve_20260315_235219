#!/bin/bash
# Self-Evolution Loop for nano_agent_team
# Usage: bash evolve.sh [max_rounds] [model] [--approve]
#   model: LLM provider/model key, e.g. qwen/qwen3-max (default), deepseek/deepseek-chat
#   --approve: auto-approve all security prompts (default: auto-deny)

MAX_ROUNDS=${1:-20}
EVOLUTION_MODEL=${2:-qwen/qwen3.5-plus}
APPROVE_FLAG=""
if [[ "$*" == *"--approve"* ]]; then
    APPROVE_FLAG="--evolution-approve"
    echo "[WARNING] --approve flag set: all security prompts will be auto-approved"
fi
export DISABLE_LANGFUSE=true
ROUND=1

# Resolve python: prefer .venv/bin/python, fall back to python3
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    echo "Error: cannot find python. Tried .venv/bin/python and python3."
    exit 1
fi

# Track the branch we started on (stay on it between rounds)
START_BRANCH=$(git branch --show-current)

mkdir -p evolution_reports

echo "╔════════════════════════════════════════╗"
echo "║   nano_agent_team Self-Evolution Loop  ║"
echo "║   Max Rounds: $MAX_ROUNDS                       ║"
echo "║   Model: $EVOLUTION_MODEL"
echo "╚════════════════════════════════════════╝"

PASS_COUNT=0
FAIL_COUNT=0

while [ $ROUND -le $MAX_ROUNDS ]; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Round $ROUND / $MAX_ROUNDS                        $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    ROUND_START=$(date +%s)

    # Ensure we start each round from the starting branch
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "$START_BRANCH" ]; then
        echo "[SAFETY] Not on $START_BRANCH (on $CURRENT_BRANCH). Switching back..."
        git checkout "$START_BRANCH" 2>/dev/null
    fi

    "$PYTHON" main.py --evolution $APPROVE_FLAG --model "$EVOLUTION_MODEL"
    EXIT_CODE=$?

    # Safety: always return to starting branch after each round
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "$START_BRANCH" ]; then
        git checkout "$START_BRANCH" 2>/dev/null
    fi

    ROUND_END=$(date +%s)
    DURATION=$(( ROUND_END - ROUND_START ))
    MINUTES=$(( DURATION / 60 ))
    SECONDS=$(( DURATION % 60 ))

    # Extract verdict from last line of evolution_history.jsonl
    VERDICT="?"
    if [ -f evolution_history.jsonl ]; then
        LAST_LINE=$(tail -1 evolution_history.jsonl 2>/dev/null)
        VERDICT=$(echo "$LAST_LINE" | grep -o '"verdict":"[^"]*"' | head -1 | cut -d'"' -f4)
        TITLE=$(echo "$LAST_LINE" | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)
    fi

    if [ "$VERDICT" = "PASS" ]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        echo "  >> PASS: $TITLE  (${MINUTES}m${SECONDS}s)"
    elif [ "$VERDICT" = "FAIL" ]; then
        FAIL_COUNT=$((FAIL_COUNT + 1))
        REASON=$(echo "$LAST_LINE" | grep -o '"reason":"[^"]*"' | head -1 | cut -d'"' -f4)
        echo "  >> FAIL: ${TITLE:-unknown}  (${MINUTES}m${SECONDS}s)"
        [ -n "$REASON" ] && echo "     Reason: $REASON"
    else
        echo "  >> Exit code $EXIT_CODE  (${MINUTES}m${SECONDS}s)"
    fi

    echo "  Score: $PASS_COUNT PASS / $FAIL_COUNT FAIL / $ROUND total"

    # Stop signal check
    if [ -f ".evolution_stop" ]; then
        echo ""
        echo "[STOP] Stop signal detected. Cleaning up."
        rm -f .evolution_stop
        break
    fi

    ROUND=$((ROUND + 1))
    sleep 5
done

echo ""
echo "════════════════════════════════════════"
echo "  Evolution complete."
echo "  Rounds: $((ROUND - 1))  |  PASS: $PASS_COUNT  |  FAIL: $FAIL_COUNT"
echo "  Reports: evolution_reports/"
echo "  Full logs: logs/evolution_r*_full.log"
echo "════════════════════════════════════════"
