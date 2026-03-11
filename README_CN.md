# nano_agent_team_selfevolve

[English](README.md) | 中文文档（本页）

`nano_agent_team_selfevolve` 是基于 [`nano_agent_team`](https://github.com/zczc/nano_agent_team) 开发的轻量级二次开发分支，核心目标是新增无人值守的自进化工作流。

如需查看完整框架文档（架构、TUI/CLI 细节、工具系统），请参考[上游 README](https://github.com/zczc/nano_agent_team)。

## 本代码库新增内容

相较于上游 `nano_agent_team`，本代码库主要新增并对接了自进化循环逻辑：

- `main.py --evolution`：启动进化架构师流程。
- `evolve.sh`：轮次化循环运行脚本（使用方式：`bash evolve.sh [max_rounds] [model]`）。
- `src/prompts/evolution_architect.md`：自主进化轮次的提示词协议文件。
- `backend/tools/evolution_workspace.py`：进化工作区/分支生命周期管理工具。
- `evolution_state.json` + `evolution_history.jsonl`（自动生成）：状态追踪文件与仅追加式历史日志文件。
- `evolution_reports/`：各轮次的 markdown 格式报告目录。

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

需在以下文件中至少选择一个服务商进行配置：
- `backend/llm_config.json`

推荐通过环境变量配置 API 密钥，示例：

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

可选启动 TUI 交互界面：

```bash
python tui.py
```

## 自进化模式

### 启动循环

```bash
bash evolve.sh
```

使用示例：

```bash
# 运行 5 轮进化
bash evolve.sh 5

# 指定模型运行 10 轮进化
bash evolve.sh 10 qwen/qwen-plus
```

### 安全停止循环

```bash
touch .evolution_stop
```

脚本会在每轮结束后检查该标识文件，自动清理标识并退出。

## 输出文件与状态文件

- `evolution_reports/`：各轮次报告目录。
- `evolution_state.json`：当前汇总状态文件。
- `evolution_history.jsonl`：仅追加式轮次历史日志（进化运行时自动创建）。
- `logs/`：运行时会话归档目录。

## 注意事项

- 请在干净的 Git 工作分支中运行进化模式。
- 每轮进化成功后，通常会创建 `evolution/r<轮次>-<时间戳>` 格式的分支。
- 为保障安全，`evolve.sh` 脚本在每轮结束后会尝试自动切回初始分支。
