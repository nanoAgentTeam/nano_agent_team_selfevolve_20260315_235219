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
SKIP_PUSH=false

# New repo will be created alongside the source repo
WORK_REPO="$(dirname "$SOURCE_DIR")/nano_agent_team_selfevolve_${TIMESTAMP}"
LOG_FILE="${WORK_REPO}/session.log"

# Claude Code CLI (non-interactive mode)
CLAUDE_CMD="claude -p --dangerously-skip-permissions --model sonnet"

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ─── Persistent Status Panel ─────────────────────────────
STATUS_HEIGHT=9
SESSION_START_TS=$(date +%s)
STATUS_UPDATER_PID=""

render_status_panel() {
    local phase="${1:-Initializing}"
    local cols=$(tput cols 2>/dev/null || echo 80)
    local inner=$((cols - 4))
    local now=$(date +%s)
    local elapsed=$(( now - SESSION_START_TS ))
    local h=$((elapsed / 3600))
    local m=$(( (elapsed % 3600) / 60 ))
    local s=$((elapsed % 60))
    local elapsed_str
    if [ $h -gt 0 ]; then elapsed_str="${h}h${m}m${s}s"
    else elapsed_str="${m}m${s}s"; fi

    # Parse evolution history from file
    local pass=0 fail=0 total=0 history=""
    local hist_file="evolution_history.jsonl"
    if [ -f "$hist_file" ]; then
        while IFS= read -r line; do
            total=$((total + 1))
            local v=$(echo "$line" | grep -o '"verdict":"[^"]*"' | cut -d'"' -f4)
            case "$v" in
                PASS) pass=$((pass + 1)); history="${history} R${total}:PASS" ;;
                FAIL) fail=$((fail + 1)); history="${history} R${total}:FAIL" ;;
                *)    history="${history} R${total}:?" ;;
            esac
        done < "$hist_file"
    fi

    local running=$((total + 1))
    [ "$running" -gt "$MAX_ROUNDS" ] && running=$MAX_ROUNDS

    # Save cursor, draw status at top, restore cursor
    tput sc
    tput cup 0 0

    local border=$(printf '═%.0s' $(seq 1 $((cols - 2))))
    printf "\e[44;97m╔%s╗\e[0m\n" "$border"
    printf "\e[44;97m║ %-${inner}s ║\e[0m\n" "  EVOLUTION SESSION: ${SESSION_NAME}"
    printf "\e[44;97m║ %-${inner}s ║\e[0m\n" "  Model: ${MODEL}  |  Round: ${running}/${MAX_ROUNDS}  |  Elapsed: ${elapsed_str}"
    printf "\e[44;97m║ %-${inner}s ║\e[0m\n" "  Phase: ${phase}"
    printf "\e[44;97m║ %-${inner}s ║\e[0m\n" "  Score: ${pass} PASS / ${fail} FAIL / ${total} completed"
    printf "\e[44;97m║ %-${inner}s ║\e[0m\n" "  History:${history:- (none yet)}"
    printf "\e[44;97m║ %-${inner}s ║\e[0m\n" "  Work: ${WORK_REPO}"
    printf "\e[44;97m╚%s╝\e[0m\n" "$border"

    tput rc
}

init_status_panel() {
    local rows=$(tput lines 2>/dev/null || echo 24)
    clear
    # Fix top STATUS_HEIGHT lines, scroll region below
    tput csr $STATUS_HEIGHT $((rows - 1))
    tput cup $STATUS_HEIGHT 0
    render_status_panel "Initializing"
}

write_status() {
    echo "$1" > .evolution_phase
}

start_status_updater() {
    (
        while true; do
            local phase="Initializing"
            [ -f .evolution_phase ] && phase=$(cat .evolution_phase 2>/dev/null)
            render_status_panel "$phase"
            sleep 5
        done
    ) &
    STATUS_UPDATER_PID=$!
}

stop_status_updater() {
    if [ -n "${STATUS_UPDATER_PID:-}" ] && kill -0 "$STATUS_UPDATER_PID" 2>/dev/null; then
        kill "$STATUS_UPDATER_PID" 2>/dev/null || true
        wait "$STATUS_UPDATER_PID" 2>/dev/null || true
    fi
    rm -f .evolution_phase
    # Reset scroll region to full terminal
    local rows=$(tput lines 2>/dev/null || echo 24)
    tput csr 0 $((rows - 1)) 2>/dev/null || true
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

# 1. Copy project excluding .venv (use symlink instead)
rsync -a --exclude='.venv' "$SOURCE_DIR/" "$WORK_REPO/"

# Now LOG_FILE is writable
log "PHASE 0: Created new repo at ${WORK_REPO}"

# 2. Enter the new repo — all subsequent work happens here
cd "$WORK_REPO"

# 3. Symlink .venv from source repo
if [ -d "$SOURCE_DIR/.venv" ]; then
    ln -s "$SOURCE_DIR/.venv" "$WORK_REPO/.venv"
    log "Symlinked .venv from source repo"
fi

# 4. Create a NEW GitHub repo and point origin to it
#    Try multiple methods in order: gh CLI → curl+gh-token → curl+url-token → SSH
SOURCE_REMOTE=$(git remote get-url origin 2>/dev/null || true)
GH_ORG=$(echo "$SOURCE_REMOTE" | sed -n 's|.*github.com[:/]\([^/]*\)/.*|\1|p' || true)
NEW_REPO_NAME="nano_agent_team_selfevolve_${TIMESTAMP}"
REPO_CREATED=false

# Helper: try creating repo via GitHub API with a given token
try_create_repo_api() {
    local token="$1"
    local org="$2"
    local repo="$3"
    local http_code

    # Try as org repo first
    if [ -n "$org" ]; then
        http_code=$(curl -s -o /tmp/gh_create_repo.json -w "%{http_code}" \
            -X POST "https://api.github.com/orgs/${org}/repos" \
            -H "Authorization: token ${token}" \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"${repo}\",\"private\":false,\"description\":\"Self-evolution session ${TIMESTAMP}\"}")
        if [ "$http_code" = "201" ]; then
            echo "${org}/${repo}"; return 0
        fi
    fi
    # Fallback: try as user repo
    http_code=$(curl -s -o /tmp/gh_create_repo.json -w "%{http_code}" \
        -X POST "https://api.github.com/user/repos" \
        -H "Authorization: token ${token}" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"${repo}\",\"private\":false,\"description\":\"Self-evolution session ${TIMESTAMP}\"}")
    if [ "$http_code" = "201" ]; then
        local owner=$(cat /tmp/gh_create_repo.json | grep -o '"full_name":"[^"]*"' | cut -d'"' -f4)
        echo "${owner:-${repo}}"; return 0
    fi
    return 1
}

# 5. Create 'original' branch from main (snapshot of pre-evolution state)
git checkout -b original
log "Created 'original' branch from main"

# 6. Clean previous evolution artifacts in the new repo
bash clean_evolution.sh 2>&1 | tee -a "$LOG_FILE"
log "Cleaned evolution artifacts"
echo ""

# ─── Initialize persistent status panel ──────────────────────
init_status_panel
start_status_updater
write_status "Phase 1: Screen Recording"

# ═══════════════════════════════════════════════════════════════
# PHASE 1: Start screen recording
# ═══════════════════════════════════════════════════════════════
log "PHASE 1: Starting screen recording..."
echo "────────────────────────────────────────────────────────────"
echo ">>> Click the terminal window you want to record <<<"

# Get window bounds via System Events (works with Ghostty and other terminals)
WINDOW_BOUNDS=$(osascript <<'APPLESCRIPT'
tell application "System Events"
    set frontApp to first application process whose frontmost is true
    set win to window 1 of frontApp
    set {x, y} to position of win
    set {w, h} to size of win
    return (x as text) & ":" & (y as text) & ":" & (w as text) & ":" & (h as text)
end tell
APPLESCRIPT
) || true

if [ -n "$WINDOW_BOUNDS" ]; then
    IFS=':' read -r WIN_X WIN_Y WIN_W WIN_H <<< "$WINDOW_BOUNDS"

    # Detect Retina scale factor: AppleScript returns logical points,
    # but ffmpeg avfoundation captures at rendered pixel resolution.
    SCALE_FACTOR=$(osascript -l JavaScript -e \
        'ObjC.import("AppKit"); Math.round($.NSScreen.mainScreen.backingScaleFactor)' 2>/dev/null || echo 0)
    if [ "$SCALE_FACTOR" -lt 1 ] 2>/dev/null; then
        SCALE_FACTOR=$( [ "$(uname -m)" = "arm64" ] && echo 2 || echo 1 )
    fi

    # Apply scale factor to convert logical points → physical pixels
    WIN_X=$(( WIN_X * SCALE_FACTOR ))
    WIN_Y=$(( WIN_Y * SCALE_FACTOR ))
    WIN_W=$(( WIN_W * SCALE_FACTOR ))
    WIN_H=$(( WIN_H * SCALE_FACTOR ))

    # Ensure dimensions are even (required by libx264)
    WIN_W=$(( (WIN_W / 2) * 2 ))
    WIN_H=$(( (WIN_H / 2) * 2 ))
    log "Recording window at (${WIN_X},${WIN_Y}) ${WIN_W}x${WIN_H} (scale=${SCALE_FACTOR}x)"

    ffmpeg -y -f avfoundation \
        -capture_cursor 1 -capture_mouse_clicks 1 \
        -framerate 30 -i "1:none" \
        -vf "crop=${WIN_W}:${WIN_H}:${WIN_X}:${WIN_Y}" \
        -c:v libx264 -b:v "$BITRATE" -pix_fmt yuv420p \
        "$RECORDING_FILE" </dev/null 2>>"${WORK_REPO}/ffmpeg.log" &
else
    log "WARNING: Could not get window bounds, recording full screen"
    ffmpeg -y -f avfoundation \
        -capture_cursor 1 -capture_mouse_clicks 1 \
        -framerate 30 -i "1:none" \
        -c:v libx264 -b:v "$BITRATE" -pix_fmt yuv420p \
        "$RECORDING_FILE" </dev/null 2>>"${WORK_REPO}/ffmpeg.log" &
fi
FFMPEG_PID=$!
sleep 2
# Verify ffmpeg actually started
if kill -0 "$FFMPEG_PID" 2>/dev/null; then
    log "Screen recording started (PID: $FFMPEG_PID) -> $RECORDING_FILE"
else
    log "WARNING: ffmpeg failed to start. Check ${WORK_REPO}/ffmpeg.log"
fi

# Ensure we stop recording on exit
stop_recording() {
    if kill -0 "$FFMPEG_PID" 2>/dev/null; then
        log "Stopping screen recording..."
        kill -INT "$FFMPEG_PID"
        # Wait up to 10 seconds for ffmpeg to finalize, then force kill
        for i in $(seq 1 10); do
            kill -0 "$FFMPEG_PID" 2>/dev/null || break
            sleep 1
        done
        if kill -0 "$FFMPEG_PID" 2>/dev/null; then
            log "WARNING: ffmpeg did not exit gracefully, force killing..."
            kill -9 "$FFMPEG_PID" 2>/dev/null || true
        fi
        wait "$FFMPEG_PID" 2>/dev/null || true
        log "Recording saved: $RECORDING_FILE"
    fi
}
cleanup_all() {
    stop_status_updater
    stop_recording
}
trap cleanup_all EXIT

# ═══════════════════════════════════════════════════════════════
# PHASE 2: Run evolution rounds (from 'original' branch)
# ═══════════════════════════════════════════════════════════════
write_status "Phase 2: Evolution (${MAX_ROUNDS} rounds with ${MODEL})"
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
    log "WARNING: No PASS rounds found. Skipping PHASE 3/4/5 (debug/README/push)."

    # Snapshot evolution artifacts even on failure
    SNAPSHOT_DIR="evolution_sessions/${SESSION_NAME}"
    mkdir -p "$SNAPSHOT_DIR"
    cp -f evolution_history.jsonl "$SNAPSHOT_DIR/" 2>/dev/null || true
    cp -f evolution_state.json "$SNAPSHOT_DIR/" 2>/dev/null || true
    cp -rf evolution_reports/ "$SNAPSHOT_DIR/" 2>/dev/null || true
    log "Artifacts saved to $SNAPSHOT_DIR"

    # stop_recording + stop_status_updater will be called by trap EXIT
    write_status "Complete (0 PASS)"
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║              Session Complete (0 PASS)                  ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  Work Repo:  ${WORK_REPO}"
    echo "║  Evolution:  ${MAX_ROUNDS} rounds with ${MODEL}"
    echo "║  Result:     No PASS rounds — main unchanged"
    echo "║  Recording:  ${RECORDING_FILE}"
    echo "║  Artifacts:  ${SNAPSHOT_DIR}/"
    echo "║  Log:        ${LOG_FILE}"
    echo "╚══════════════════════════════════════════════════════════╝"
    exit 0
fi

log "Last PASS branch: $LAST_PASS_BRANCH"

# 6. Merge last PASS branch into main (full overwrite with -X theirs)
git checkout main
git merge "$LAST_PASS_BRANCH" -X theirs --no-edit -m "merge: evolution session ${TIMESTAMP} - merge ${LAST_PASS_BRANCH} into main (full overwrite)"
log "Merged $LAST_PASS_BRANCH into main (full overwrite)"

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
write_status "Phase 3: Debug & Analysis"
log "PHASE 3: Analyzing evolution results & debugging..."
echo "────────────────────────────────────────────────────────────"

# Unset CLAUDECODE to avoid nested session detection
unset CLAUDECODE 2>/dev/null || true

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

# Run Claude Code for analysis & debug (don't exit on failure)
echo "$ANALYSIS_PROMPT" | $CLAUDE_CMD 2>&1 | tee -a "$LOG_FILE" || true
DEBUG_EXIT=$?

if [ $DEBUG_EXIT -ne 0 ]; then
    log "WARNING: Debug phase exited with code $DEBUG_EXIT"
fi

# ═══════════════════════════════════════════════════════════════
# PHASE 4: Write README.md & README_CN.md
# ═══════════════════════════════════════════════════════════════
write_status "Phase 4: Writing README"
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

echo "$README_PROMPT" | $CLAUDE_CMD 2>&1 | tee -a "$LOG_FILE" || true

# ═══════════════════════════════════════════════════════════════
# PHASE 5: Commit & Push to GitHub
# ═══════════════════════════════════════════════════════════════
write_status "Phase 5: Commit & Push"
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

# Create remote repo now (deferred until push time)
FULL_REPO="${GH_ORG:+${GH_ORG}/}${NEW_REPO_NAME}"

# ── Method 1: gh CLI ──
if [ "$REPO_CREATED" = "false" ] && command -v gh &>/dev/null && gh auth status &>/dev/null; then
    log "Trying GitHub repo creation via gh CLI..."
    if gh repo create "$FULL_REPO" --public \
        --description "Self-evolution session ${TIMESTAMP}" 2>>"$LOG_FILE"; then
        git remote set-url origin "https://github.com/${FULL_REPO}.git"
        log "✓ Created repo via gh CLI: ${FULL_REPO}"
        REPO_CREATED=true
    else
        log "✗ gh CLI repo creation failed, trying next method..."
    fi
fi

# ── Method 2: curl + token from gh auth ──
if [ "$REPO_CREATED" = "false" ] && command -v gh &>/dev/null; then
    GH_TOKEN_FROM_CLI=$(gh auth token 2>/dev/null || true)
    if [ -n "$GH_TOKEN_FROM_CLI" ]; then
        log "Trying GitHub repo creation via API (gh auth token)..."
        CREATED_REPO=$(try_create_repo_api "$GH_TOKEN_FROM_CLI" "$GH_ORG" "$NEW_REPO_NAME") && {
            git remote set-url origin "https://github.com/${CREATED_REPO}.git"
            log "✓ Created repo via API (gh token): ${CREATED_REPO}"
            FULL_REPO="$CREATED_REPO"
            REPO_CREATED=true
        } || log "✗ API creation with gh token failed, trying next method..."
    fi
fi

# ── Method 3: curl + token embedded in remote URL ──
if [ "$REPO_CREATED" = "false" ]; then
    GH_TOKEN_FROM_URL=$(echo "$SOURCE_REMOTE" | grep -o 'ghp_[^@]*' || true)
    if [ -n "$GH_TOKEN_FROM_URL" ]; then
        log "Trying GitHub repo creation via API (URL-embedded token)..."
        CREATED_REPO=$(try_create_repo_api "$GH_TOKEN_FROM_URL" "$GH_ORG" "$NEW_REPO_NAME") && {
            git remote set-url origin "https://${GH_TOKEN_FROM_URL}@github.com/${CREATED_REPO}.git"
            log "✓ Created repo via API (URL token): ${CREATED_REPO}"
            FULL_REPO="$CREATED_REPO"
            REPO_CREATED=true
        } || log "✗ API creation with URL token failed, trying next method..."
    fi
fi

# ── Method 4: curl + token from GITHUB_TOKEN env ──
if [ "$REPO_CREATED" = "false" ] && [ -n "${GITHUB_TOKEN:-}" ]; then
    log "Trying GitHub repo creation via API (GITHUB_TOKEN env)..."
    CREATED_REPO=$(try_create_repo_api "$GITHUB_TOKEN" "$GH_ORG" "$NEW_REPO_NAME") && {
        git remote set-url origin "https://github.com/${CREATED_REPO}.git"
        log "✓ Created repo via API (GITHUB_TOKEN): ${CREATED_REPO}"
        FULL_REPO="$CREATED_REPO"
        REPO_CREATED=true
    } || log "✗ API creation with GITHUB_TOKEN failed, trying next method..."
fi

# ── Method 5: SSH — no repo creation, push to existing org via SSH ──
if [ "$REPO_CREATED" = "false" ] && [ -n "$GH_ORG" ]; then
    SSH_REMOTE="git@github.com:${GH_ORG}/${NEW_REPO_NAME}.git"
    log "Trying SSH remote (requires repo to exist or manual creation): ${SSH_REMOTE}"
    git remote set-url origin "$SSH_REMOTE"
    # We can't create the repo via SSH, but maybe it already exists
    if git ls-remote "$SSH_REMOTE" &>/dev/null 2>&1; then
        log "✓ SSH remote accessible: ${SSH_REMOTE}"
        FULL_REPO="${GH_ORG}/${NEW_REPO_NAME}"
        REPO_CREATED=true
    else
        log "✗ SSH remote not accessible."
    fi
fi

if [ "$REPO_CREATED" = "false" ]; then
    log "WARNING: All GitHub repo creation methods failed. Push will be skipped."
    log "  To fix: run 'gh auth login' or set GITHUB_TOKEN env var."
    SKIP_PUSH=true
fi

# Push to new remote (all branches including evolution/*)
if [ "${SKIP_PUSH:-}" = "true" ]; then
    log "Skipping push (no remote repo created)."
else
    git push origin --all
    log "Pushed all branches to new GitHub repo."
fi

# ═══════════════════════════════════════════════════════════════
# PHASE 6: Stop recording (handled by trap EXIT → stop_recording)
# ═══════════════════════════════════════════════════════════════

# Close Bilibili client if running
if pgrep -f "哔哩哔哩" &>/dev/null; then
    log "Closing Bilibili client..."
    osascript -e 'quit app "哔哩哔哩"' 2>/dev/null || pkill -f "哔哩哔哩" 2>/dev/null || true
fi

# Update status panel one last time
write_status "Session Complete!"

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
