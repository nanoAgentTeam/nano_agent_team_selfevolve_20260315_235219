# nano_agent_team_selfevolve

[English](README.md) | 中文文档（本页）

`nano_agent_team_selfevolve` 是基于 [`nano_agent_team`](https://github.com/zczc/nano_agent_team) 的二次开发分支，核心能力是**无人值守的自我演化** -- 多 Agent 团队自主完成调研、设计、开发、测试、审查和发布新功能，全程无需人类干预。

如需查看完整框架文档（架构、TUI/CLI 细节、工具系统），请参考[上游 README](https://github.com/zczc/nano_agent_team)。

## 本代码库新增内容

相较于上游 `nano_agent_team`，本代码库主要新增了自进化循环和自动化会话编排：

- `main.py --evolution`：启动进化架构师流程。
- `evolve.sh`：轮次化循环运行脚本（`bash evolve.sh [max_rounds] [model]`）。
- `evolve_session.sh`：完整自动化会话（清理 -> 演化 -> 录屏 -> 调试 -> README -> 推送）。
- `src/prompts/evolution_architect.md`：自主进化轮次的提示词协议。
- `backend/tools/evolution_workspace.py`：进化工作区/分支生命周期管理工具。
- `evolution_state.json` + `evolution_history.jsonl`（自动生成）：状态追踪与仅追加式历史日志。
- `evolution_reports/`：各轮次 Markdown 报告。

## 最近一次演化会话

**会话：** `evo_session_20260315_235219`
**模型：** `qwen/qwen3.5-plus` | **轮次：** 10 | **结果：** 10/10 PASS（0 FAIL）

| 轮次 | 功能 | 类型 | 说明 |
|------|------|------|------|
| R1 | **Experience Memory Tool** | 功能 | Agent 跨会话持久化记忆，JSON 存储后端 |
| R2 | **Code Health Analyzer Tool** | 功能 | 基于 AST 的 Python 代码质量分析（复杂度、耦合度、规模） |
| R3 | **ExperienceMemoryTool 注册** | 集成 | 将 R1 的工具接入 tool_registry，双入口可用 |
| R4 | **Agent Self-Reflection Middleware** | 功能 | 自动失败分析 + ReflectionAnalyzer，反思结果写入经验记忆 |
| R5 | **Agent Status Dashboard** | 功能 | 实时 Agent 监控，TUI 仪表盘 + `/agents` 命令 |
| R6 | **Agent Self-Diagnosis & Recovery** | 功能 | 诊断引擎 + 恢复策略（Retry/Fallback/CircuitBreaker），以 Skill 形式提供 |
| R7 | **AgentMonitorTool 集成** | 集成 | 将 R5 的监控能力包装为 Agent 可调用的工具 |
| R8 | **Session Replay Tool** | 功能 | 调试用的 Trace 捕获 + 回放，TUI `/replay` 命令 |
| R9 | **Agent Diagnosis Tool 集成** | 集成 | 将 R6 的诊断引擎包装为可调用工具 |
| R10 | **Tool Explorer & 8 工具集成** | 功能 | 将 8 个已有但未接入的工具接入双入口 |

### 调试结果

- **152/152 测试通过**（2 个 wiring 测试修复：硬编码路径改为相对路径）
- `python main.py --help` 正常运行
- 所有新模块导入成功
- 注意：R10 报告创建了 `tool_explorer.py`（TUI 界面），但该文件未实际提交到 git。8 个工具在 main.py 和 agent_bridge.py 中的接入完好。

## 快速开始

### 1. 安装

```bash
git clone https://github.com/nanoAgentTeam/nano_agent_team_selfevolve.git
cd nano_agent_team_selfevolve
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置模型与 API 密钥

在以下文件中至少选择一个服务商：
- `backend/llm_config.json`

推荐通过环境变量配置 API 密钥：

```bash
export OPENAI_API_KEY="你的密钥"
export DASHSCOPE_API_KEY="你的密钥"
```

也可传入自定义密钥文件路径：

```bash
python main.py --keys /path/to/keys.json
```

### 3. 运行普通模式

```bash
python main.py "你的任务指令"
```

可选 TUI 交互界面：

```bash
python tui.py
```

## 自进化模式

### 启动循环

```bash
bash evolve.sh
```

示例：

```bash
# 运行 5 轮进化
bash evolve.sh 5

# 指定模型运行 10 轮
bash evolve.sh 10 qwen/qwen-plus
```

### 完整自动化会话

```bash
bash evolve_session.sh [rounds] [model]
```

编排完整流水线：仓库准备 -> 录屏 -> 演化 -> 调试 -> README -> GitHub 推送。

### 安全停止

```bash
touch .evolution_stop
```

脚本在每轮结束后检查该标识，自动清理并退出。

## 输出文件与状态文件

- `evolution_reports/`：各轮次报告。
- `evolution_state.json`：当前汇总状态。
- `evolution_history.jsonl`：仅追加式轮次历史日志。
- `evolution_sessions/`：会话快照与工件。
- `logs/`：运行时会话归档。

## 项目结构

```
├── main.py                          # CLI 入口（普通模式 + 演化模式）
├── tui.py                           # TUI 入口
├── evolve.sh                        # 演化循环运行脚本
├── evolve_session.sh                # 完整会话编排脚本
├── backend/
│   ├── llm/                         # LLM 引擎、工具注册表、中间件
│   ├── tools/                       # 所有工具（文件操作、搜索、演化、分析...）
│   └── utils/                       # Agent 监控、代码指标、反思、诊断
├── src/
│   ├── core/middlewares/             # 反思中间件、Token 追踪等
│   ├── prompts/                     # 角色模板和演化架构师提示词
│   └── tui/                         # TUI 应用、屏幕、组件、斜杠命令
├── tests/                           # 所有演化功能的单元测试
└── evolution_reports/               # 各轮次演化报告
```

## License

License 详情请参考上游 [nano_agent_team](https://github.com/zczc/nano_agent_team)。
