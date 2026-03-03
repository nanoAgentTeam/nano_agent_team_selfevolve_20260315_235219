#!/bin/bash
# Clean up all evolution intermediate results
# Usage: bash clean_evolution.sh

set -e
cd "$(dirname "$0")"

echo "=== Evolution Cleanup ==="
echo ""
CLEANED=0

# 1. Kill running evolution processes
PIDS=$(ps aux | grep "main.py.*evolution" | grep -v grep | awk '{print $2}')
if [ -n "$PIDS" ]; then
    echo "Killed processes: $PIDS"
    echo "$PIDS" | xargs kill -9
    CLEANED=$((CLEANED + 1))
else
    echo "Processes: none running"
fi

# 2. Remove git worktrees (except main)
WORKTREES=$(git worktree list | grep -v "$(git rev-parse --show-toplevel) " | awk '{print $1}')
if [ -n "$WORKTREES" ]; then
    echo "$WORKTREES" | while read wt; do
        git worktree remove --force "$wt" 2>/dev/null && echo "Removed worktree: $wt"
    done
    git worktree prune
    CLEANED=$((CLEANED + 1))
else
    echo "Worktrees: none to remove"
fi

# 3. Delete evolution/* branches
BRANCHES=$(git branch | grep 'evolution/' | tr -d ' *')
if [ -n "$BRANCHES" ]; then
    echo "$BRANCHES" | while read b; do
        git branch -D "$b" && echo "Deleted branch: $b"
    done
    CLEANED=$((CLEANED + 1))
else
    echo "Branches: none to delete"
fi

# 4. Remove .blackboard directory
if [ -d ".blackboard" ]; then
    echo "Removed: .blackboard/"
    rm -rf .blackboard
    CLEANED=$((CLEANED + 1))
else
    echo "Blackboard: not present"
fi

# 5. Remove evolution_history.jsonl
if [ -f "evolution_history.jsonl" ]; then
    LINES=$(wc -l < evolution_history.jsonl)
    echo "Removed: evolution_history.jsonl ($LINES lines)"
    rm -f evolution_history.jsonl
    CLEANED=$((CLEANED + 1))
else
    echo "History: not present"
fi

# 6. Remove evolution reports
REPORTS=$(ls evolution_reports/*.md 2>/dev/null | wc -l)
if [ "$REPORTS" -gt 0 ]; then
    echo "Removed: $REPORTS report(s) in evolution_reports/"
    rm -f evolution_reports/*.md
    CLEANED=$((CLEANED + 1))
else
    echo "Reports: none to remove"
fi

# 7. Reset evolution_state.json
if [ -f "evolution_state.json" ]; then
    echo "Reset: evolution_state.json"
    echo '{"round": 0, "history": [], "failures": []}' > evolution_state.json
    CLEANED=$((CLEANED + 1))
else
    echo "State: not present"
fi

echo ""
echo "=== Done ($CLEANED item groups cleaned) ==="
