#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  evolve_session.sh - Full Automated Evolution Session       ║
# ║  Clean → Evolve → Record → Debug → README → Push → Done    ║
# ║  Usage: bash evolve_session.sh [rounds] [model]             ║
# ╚══════════════════════════════════════════════════════════════╝

set -euo pipefail
cd "$(dirname "$0")"
SOURCE_DIR="$(pwd)"

# ─── Configuration ─────────────────────────────────────────────
MAX_ROUNDS=${1:-3}
MODEL=${2:-"qwen/qwen3.5-plus"}
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
SESSION_NAME="evo_session_${TIMESTAMP}"
RECORDING_FILE="$HOME/Desktop/${SESSION_NAME}.mp4"
BITRATE="1000k"

# New repo will be created alongside the source repo
WORK_REPO="$(dirname "$SOURCE_DIR")/nano_agent_team_selfevolve_${TIMESTAMP}"
LOG_FILE="${WORK_REPO}/session.log"

# Claude Code CLI (non-interactive mode)
CLAUDE_CMD="claude -p --dangerously-skip-permissions --model sonnet"

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ─── Pre-flight checks ────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║            Evolution Session: ${SESSION_NAME}           ║"
echo "║  Rounds: ${MAX_ROUNDS}  |  Model: ${MODEL}"
echo "║  Work Repo: ${WORK_REPO}"
echo "║  Recording: ${RECORDING_FILE}"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check dependencies
for cmd in ffmpeg claude git; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: '$cmd' not found. Please install it first."
        exit 1
    fi
done

# Ensure source is on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "WARNING: Not on main branch (on '$CURRENT_BRANCH'). Switching to main..."
    git checkout main
fi

# ═══════════════════════════════════════════════════════════════
# PHASE 0: Create new repo & prepare branches
# ═══════════════════════════════════════════════════════════════
echo "────────────────────────────────────────────────────────────"

# 1. Copy entire project (including .venv, .git, everything)
cp -R "$SOURCE_DIR" "$WORK_REPO"

# Now LOG_FILE is writable
log "PHASE 0: Created new repo at ${WORK_REPO}"

# 2. Enter the new repo — all subsequent work happens here
cd "$WORK_REPO"

# 3. Create 'original' branch from main (snapshot of pre-evolution state)
git checkout -b original
log "Created 'original' branch from main"

# 4. Clean previous evolution artifacts in the new repo
bash clean_evolution.sh 2>&1 | tee -a "$LOG_FILE"
log "Cleaned evolution artifacts"
echo ""

# ═══════════════════════════════════════════════════════════════
# PHASE 1: Start screen recording
# ═══════════════════════════════════════════════════════════════
log "PHASE 1: Starting screen recording..."
echo "────────────────────────────────────────────────────────────"

ffmpeg -y -f avfoundation \
    -capture_cursor 1 -capture_mouse_clicks 1 \
    -framerate 30 -i "1:none" \
    -c:v libx264 -b:v "$BITRATE" -pix_fmt yuv420p \
    "$RECORDING_FILE" </dev/null &>/dev/null &
FFMPEG_PID=$!
log "Screen recording started (PID: $FFMPEG_PID) -> $RECORDING_FILE"
sleep 2

# Ensure we stop recording on exit
cleanup_recording() {
    if kill -0 "$FFMPEG_PID" 2>/dev/null; then
        log "Stopping screen recording..."
        kill -INT "$FFMPEG_PID"
        wait "$FFMPEG_PID" 2>/dev/null || true
        log "Recording saved: $RECORDING_FILE"
    fi
}
trap cleanup_recording EXIT

# ═══════════════════════════════════════════════════════════════
# PHASE 2: Run evolution rounds (from 'original' branch)
# ═══════════════════════════════════════════════════════════════
log "PHASE 2: Running evolution ($MAX_ROUNDS rounds with $MODEL) from 'original' branch..."
echo "────────────────────────────────────────────────────────────"

# evolve.sh reads START_BRANCH=$(git branch --show-current) → 'original'
# main.py uses current branch as base_branch when no PASS history
# So evolution branches will be: original → evolution/r1-... → evolution/r2-... → ...
EVOLVE_START=$(date +%s)
bash evolve.sh "$MAX_ROUNDS" "$MODEL" --approve 2>&1 | tee -a "$LOG_FILE"
EVOLVE_END=$(date +%s)
EVOLVE_DURATION=$(( EVOLVE_END - EVOLVE_START ))
log "Evolution completed in $(( EVOLVE_DURATION / 60 ))m$(( EVOLVE_DURATION % 60 ))s"

# 5. Find the last PASS branch from evolution_history.jsonl
LAST_PASS_BRANCH=""
if [ -f evolution_history.jsonl ]; then
    # Read all PASS entries, take the last one's branch
    LAST_PASS_BRANCH=$(grep '"verdict":"PASS"' evolution_history.jsonl | tail -1 | grep -o '"branch":"[^"]*"' | cut -d'"' -f4 || true)
fi

if [ -z "$LAST_PASS_BRANCH" ]; then
    log "WARNING: No PASS rounds found. main branch will remain unchanged."
else
    log "Last PASS branch: $LAST_PASS_BRANCH"

    # 6. Merge last PASS branch into main (full overwrite with -X theirs)
    git checkout main
    git merge "$LAST_PASS_BRANCH" -X theirs --no-edit -m "merge: evolution session ${TIMESTAMP} - merge ${LAST_PASS_BRANCH} into main (full overwrite)"
    log "Merged $LAST_PASS_BRANCH into main (full overwrite)"
fi

# Ensure we're on main for subsequent phases
git checkout main 2>/dev/null || true
log "Now on main branch — ready for debug/README/push phases"

# Snapshot evolution artifacts
SNAPSHOT_DIR="evolution_sessions/${SESSION_NAME}"
mkdir -p "$SNAPSHOT_DIR"
cp -f evolution_history.jsonl "$SNAPSHOT_DIR/" 2>/dev/null || true
cp -f evolution_state.json "$SNAPSHOT_DIR/" 2>/dev/null || true
cp -rf evolution_reports/ "$SNAPSHOT_DIR/" 2>/dev/null || true
log "Artifacts saved to $SNAPSHOT_DIR"

# ═══════════════════════════════════════════════════════════════
# PHASE 3: Analyze evolution results & Debug new features
# ═══════════════════════════════════════════════════════════════
log "PHASE 3: Analyzing evolution results & debugging..."
echo "────────────────────────────────────────────────────────────"

# Read evolution history for context
EVO_HISTORY=""
if [ -f evolution_history.jsonl ]; then
    EVO_HISTORY=$(cat evolution_history.jsonl)
fi

# Build analysis & debug prompt
ANALYSIS_PROMPT=$(cat <<'PROMPT_EOF'
你现在在 nano_agent_team_selfevolve 项目的 main 分支下。

## 背景
刚刚完成了一轮自动演化（self-evolution），演化过程会在 evolution/* 分支上开发新功能，
通过质量门控后 merge 回 main。

## 你的任务

### 1. 分析演化结果
- 读取 evolution_history.jsonl 了解每轮演化做了什么
- 读取 evolution_reports/ 下的报告了解详细变更
- 汇总新增了哪些功能、修改了哪些文件

### 2. Debug 新功能
对每个 PASS 的演化轮次新增的功能：
- 检查相关代码是否有语法错误、导入错误
- 尝试运行 `python main.py --help` 确认基本启动无报错
- 如果有 tests/ 相关测试，运行相关测试
- 修复发现的任何问题（直接修改代码）

### 3. 输出分析报告
在最后输出一份结构化的分析报告（纯文本），包括：
- 每轮演化的功能概述
- 发现的 bug 及修复情况
- 当前功能可用性状态

请直接开始工作，不要问我问题。
PROMPT_EOF
)

# Run Claude Code for analysis & debug
echo "$ANALYSIS_PROMPT" | $CLAUDE_CMD 2>&1 | tee -a "$LOG_FILE"
DEBUG_EXIT=$?

if [ $DEBUG_EXIT -ne 0 ]; then
    log "WARNING: Debug phase exited with code $DEBUG_EXIT"
fi

# ═══════════════════════════════════════════════════════════════
# PHASE 4: Write README.md & README_CN.md
# ═══════════════════════════════════════════════════════════════
log "PHASE 4: Writing README files..."
echo "────────────────────────────────────────────────────────────"

README_PROMPT=$(cat <<PROMPT_EOF
你现在在 nano_agent_team_selfevolve 项目的 main 分支下。

## 任务
请覆盖更新 README.md（英文）和 README_CN.md（中文），两份内容对应但语言不同。

## README 应包含以下内容

### i. 项目背景
- nano_agent_team_selfevolve 是基于 nano_agent_team 的二次开发分支
- 核心能力：无人值守的自我演化工作流（self-evolution workflow）
- 多 agent 团队（Architect, Developer, Tester, Auditor, Reviewer 等）协作完成自主改进
- 支持多种 LLM 提供商（Qwen, OpenAI, DeepSeek, Step, Moonshot 等）

### ii. 本次运行设置
- 演化轮次: ${MAX_ROUNDS} 轮
- 使用模型: ${MODEL}
- 运行时间戳: ${TIMESTAMP}
- 运行脚本: evolve_session.sh (自动清理 → 演化 → 录屏 → 调试 → 文档 → 推送)

### iii. 运行结果
- 读取 evolution_history.jsonl 获取每轮的结果（PASS/FAIL、功能标题、类型等）
- 读取 evolution_reports/ 下的报告获取详细变更
- 列出新增功能和修改的文件

### iv. Debug 结果
- 读取前一阶段的分析结果（查看最近修改的文件）
- 说明发现了哪些问题，修复了什么
- 当前功能可用性总结

### 其他要求
- 保留 Quick Start 安装说明（更新为通用路径）
- 保留项目结构说明
- 包含 License 说明
- README.md 顶部添加 English | 中文 双语切换链接
- 写得简洁专业，像一个正式的开源项目 README

请直接修改 README.md 和 README_CN.md 文件，不要问我问题。
PROMPT_EOF
)

echo "$README_PROMPT" | $CLAUDE_CMD 2>&1 | tee -a "$LOG_FILE"

# ═══════════════════════════════════════════════════════════════
# PHASE 5: Commit & Push to GitHub
# ═══════════════════════════════════════════════════════════════
log "PHASE 5: Committing and pushing to GitHub..."
echo "────────────────────────────────────────────────────────────"

# We're in WORK_REPO on main branch
# Stage debug fixes + README changes
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    log "No changes to commit."
else
    git commit -m "$(cat <<'COMMIT_DELIM'
feat: post-evolution debug fixes and README update

- Debugged and verified new features on main branch
- Updated README.md and README_CN.md with session results
COMMIT_DELIM
)"
    log "Changes committed."
fi

# Push main branch to remote
git push origin main
log "Pushed main to GitHub."

# ═══════════════════════════════════════════════════════════════
# PHASE 6: Stop recording
# ═══════════════════════════════════════════════════════════════
log "PHASE 6: Stopping screen recording..."
echo "────────────────────────────────────────────────────────────"

# Stop ffmpeg gracefully (SIGINT = finalize file, same as pressing 'q')
if kill -0 "$FFMPEG_PID" 2>/dev/null; then
    kill -INT "$FFMPEG_PID"
    wait "$FFMPEG_PID" 2>/dev/null || true
    trap - EXIT
    log "Recording saved: $RECORDING_FILE"
fi

# Close Bilibili client if running
if pgrep -f "哔哩哔哩" &>/dev/null; then
    log "Closing Bilibili client..."
    osascript -e 'quit app "哔哩哔哩"' 2>/dev/null || pkill -f "哔哩哔哩" 2>/dev/null || true
fi

# Final summary
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              Session Complete!                          ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Work Repo:  ${WORK_REPO}"
echo "║  Evolution:  ${MAX_ROUNDS} rounds with ${MODEL}"
echo "║  Recording:  ${RECORDING_FILE}"
echo "║  Artifacts:  ${SNAPSHOT_DIR}/"
echo "║  Log:        ${LOG_FILE}"
echo "╚══════════════════════════════════════════════════════════╝"
