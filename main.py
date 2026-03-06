
import os
import sys
import argparse
import shutil
import json
import io


class EvolutionOutputFilter(io.TextIOBase):
    """
    Wraps sys.stdout during evolution mode.
    Full output is tee'd to a log file; terminal shows only key progress.
    """

    def __init__(self, terminal, log_file):
        self._terminal = terminal
        self._log = log_file
        self._buf = ""
        self._tool_batch = []
        self._shown_text = False

    def write(self, text):
        if self._log:
            self._log.write(text)
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self._handle(line)
        return len(text)

    def _out(self, tag, content):
        import datetime as _dt
        ts = _dt.datetime.now().strftime("%H:%M:%S")
        self._terminal.write(f"{ts} ── {tag:7s} ── {content}\n")
        self._terminal.flush()

    def _flush_tools(self):
        if self._tool_batch:
            self._out("tool", ", ".join(self._tool_batch))
            self._tool_batch = []

    def _handle(self, line):
        s = line.strip()
        if not s or all(c == "-" for c in s):
            return

        # Tool call -> collect just the tool name
        if "[Tool Call]" in line:
            self._shown_text = False
            try:
                name = line.split("[Tool Call] ", 1)[1].split("(", 1)[0]
                self._tool_batch.append(name)
            except Exception:
                pass
            return

        # Tool result -> suppress, flush pending tool batch
        if "[Tool Result]" in line:
            self._flush_tools()
            return

        # Lifecycle lines -> always show
        if any(m in line for m in (
            "[Launcher]", "[Evolution]",
            "Starting loop", "Detected 'finish'", "Agent loop completed",
            "WARNING:", "Interrupted", "Exception in agent",
            "Connection error", "Retrying engine", "Critical Error",
            "Registered in blackboard", "Blackboard:",
        )):
            self._flush_tools()
            if "Booting up with role:" in line:
                tag = line.split("]", 1)[0] + "]" if "]" in line else ""
                self._out("system", f"{tag} Booting up...")
            else:
                self._out("system", s)
            return

        # LLM text -> show first line per block, truncated
        if not self._shown_text and len(s) > 2:
            self._flush_tools()
            show = (s[:200] + "...") if len(s) > 200 else s
            self._out("message", show)
            self._shown_text = True

    def flush(self):
        self._flush_tools()
        if self._log:
            self._log.flush()
        self._terminal.flush()

    def fileno(self):
        return self._terminal.fileno()

    def isatty(self):
        return self._terminal.isatty()

    @property
    def encoding(self):
        return self._terminal.encoding


from src.core.agent_wrapper import SwarmAgent
from backend.infra.config import Config
from backend.tools.web_search import SearchTool
from backend.tools.web_reader import WebReaderTool
from src.core.middlewares import RequestMonitorMiddleware, ArchitectGuardMiddleware
from backend.infra.envs.local import LocalEnvironment
from backend.tools.bash import BashTool
from backend.tools.write_file import WriteFileTool
from backend.tools.read_file import ReadFileTool
from backend.tools.edit_file import EditFileTool
from backend.tools.grep import GrepTool
from backend.tools.glob import GlobTool
from backend.tools.evolution_workspace import EvolutionWorkspaceTool

# Ensure project root is in path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def setup_env(args):
    """
    Initialize environment.
    Default: Clean .blackboard (unless --keep-history is set).
    """
    blackboard_dir = os.path.join(project_root, ".blackboard")
    
    if args.keep_history:
        print(f"[Launcher] Keeping history at {blackboard_dir}")
        return

    if os.path.exists(blackboard_dir):
        print(f"[Launcher] Cleaning blackboard at {blackboard_dir}...")
        try:
            shutil.rmtree(blackboard_dir)
        except Exception as e:
            print(f"[Launcher] Warning: Failed to clean blackboard: {e}")

def archive_session():
    """
    Archive session.
    Copy .blackboard content to logs/session_<timestamp>.
    """
    import datetime
    
    blackboard_dir = os.path.join(project_root, ".blackboard")
    if not os.path.exists(blackboard_dir):
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(project_root, "logs", f"session_{timestamp}")
    
    print(f"\n[Launcher] Archiving session to {log_dir}...")
    try:
        shutil.copytree(blackboard_dir, log_dir)
        print(f"[Launcher] Session archived successfully.")
    except Exception as e:
        print(f"[Launcher] Error archiving session: {e}")

def main():
    parser = argparse.ArgumentParser(description="Nano Agent Team - Watchdog Launcher")
    parser.add_argument("query", nargs="?", help="The mission or query for the swarm")
    parser.add_argument("--role", default="Architect", help="Role of the main agent (default: Architect)")
    parser.add_argument("--name", default="Architect", help="Name of the main agent")
    # Changed: --clean is now default behavior, added --keep-history to inverse it
    parser.add_argument("--keep-history", action="store_true", help="Keep the previous blackboard state (do not clean)")
    parser.add_argument("--model", type=str, default=None, help="Model provider key (default: Use settings.json)")
    

    # Evolution mode
    parser.add_argument("--evolution", action="store_true", help="Run in self-evolution mode")
    parser.add_argument("--evolution-approve", action="store_true", help="Auto-approve all security prompts in evolution mode (default: auto-deny)")

    # Global flags
    parser.add_argument("--keys", type=str, default="keys.json", help="Path to keys.json (default: keys.json)")
    
    args = parser.parse_args()

    print("=== Nano Agent Team Launcher ===")

    # 1. Initialize Config
    Config.initialize(args.keys)

    # 2. Setup Environment (Clean Blackboard)
    setup_env(args)

    # 3. Load Prompt & Determine Mission
    if args.evolution:
        # Evolution mode: standalone prompt (no base architect concatenation)
        evo_prompt_path = os.path.join(project_root, "src/prompts/evolution_architect.md")
        if not os.path.exists(evo_prompt_path):
            print(f"Error: Evolution prompt not found at {evo_prompt_path}")
            return

        with open(evo_prompt_path, "r", encoding="utf-8") as f:
            architect_role_content = f.read()

        # Read evolution state from JSONL (source of truth)
        # evolution_history.jsonl — append-only log, one JSON object per line
        # evolution_state.json — generated by launcher for Architect to read (not written by Architect)
        state_path = os.path.join(project_root, "evolution_state.json")
        history_path = os.path.join(project_root, "evolution_history.jsonl")

        # Load history from JSONL file
        # Robust parser: handles concatenated JSON objects on the same line
        # (e.g. when the agent forgets to add \n between entries)
        history_entries = []
        if os.path.exists(history_path):
            with open(history_path, "r", encoding="utf-8") as f:
                content = f.read()
            decoder = json.JSONDecoder()
            pos = 0
            while pos < len(content):
                while pos < len(content) and content[pos] in " \t\n\r":
                    pos += 1
                if pos >= len(content):
                    break
                try:
                    obj, end = decoder.raw_decode(content, pos)
                    history_entries.append(obj)
                    pos = end
                except json.JSONDecodeError as e:
                    print(f"[Evolution] Warning: Skipping unparseable content at pos {pos}: {e}")
                    # Skip to next newline to avoid infinite loop
                    next_nl = content.find("\n", pos)
                    pos = next_nl + 1 if next_nl != -1 else len(content)

        # Derive round number from history
        if history_entries:
            last_round = max(e.get("round", 0) for e in history_entries)
            round_num = last_round + 1
        else:
            round_num = 1

        # Build state from history
        last_pass = next((h for h in reversed(history_entries) if h.get("verdict") == "PASS"), None)
        evo_state = {
            "round": round_num - 1,
            "history": history_entries,
            "failures": [e for e in history_entries if e.get("verdict") == "FAIL"],
            "last_suggestion": (last_pass or {}).get("next_suggestion", ""),
        }

        # Write current_round, unique branch name, and base_branch into state.
        # - current_branch: unique name for this round's new branch (timestamp avoids conflicts)
        # - base_branch: where to branch FROM (last PASS branch for serial accumulation,
        #   or the starting git branch if no PASS history yet — dev/self_evolve never moves)
        import datetime as _dt
        import subprocess as _sp
        _ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        evo_state["current_round"] = round_num
        evo_state["current_branch"] = f"evolution/r{round_num}-{_ts}"

        # Serial accumulation: find last PASS branch to branch from
        if last_pass:
            evo_state["base_branch"] = last_pass["branch"]
        else:
            # No PASS yet — branch from current HEAD (the fixed starting branch)
            _r = _sp.run(["git", "branch", "--show-current"],
                         capture_output=True, text=True, cwd=project_root)
            evo_state["base_branch"] = _r.stdout.strip() or "HEAD"

        with open(state_path, "w") as f:
            json.dump(evo_state, f, indent=2)

        # Ensure evolution_reports directory exists
        os.makedirs(os.path.join(project_root, "evolution_reports"), exist_ok=True)

        # ── Auto-create git worktree for this round ──────────────────────────
        blackboard_dir = os.path.join(project_root, ".blackboard")
        workspace = os.path.join(blackboard_dir, "resources", "workspace")
        _branch = evo_state["current_branch"]
        _base = evo_state["base_branch"]

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(workspace), exist_ok=True)

        # Clean up any leftover workspace directory (orphaned from previous run)
        if os.path.exists(workspace):
            print(f"[Evolution] Cleaning up leftover workspace at {workspace}")
            # If it's a valid worktree, remove it properly first
            if os.path.isfile(os.path.join(workspace, ".git")):
                _sp.run(["git", "-C", project_root, "worktree", "remove", workspace, "--force"],
                        capture_output=True, text=True)
            else:
                shutil.rmtree(workspace, ignore_errors=True)
            # Prune stale worktree references
            _sp.run(["git", "-C", project_root, "worktree", "prune"],
                    capture_output=True, text=True)

        # Try creating worktree with new branch
        wt_result = _sp.run(
            ["git", "-C", project_root, "worktree", "add", "-b", _branch, workspace, _base],
            capture_output=True, text=True
        )

        if wt_result.returncode != 0:
            # Branch may already exist (e.g. from a previous failed round)
            print(f"[Evolution] Worktree add -b failed: {wt_result.stderr.strip()}")
            print(f"[Evolution] Retrying without -b (branch may already exist)...")
            # Clean directory if it was partially created
            if os.path.exists(workspace):
                shutil.rmtree(workspace, ignore_errors=True)
            wt_result = _sp.run(
                ["git", "-C", project_root, "worktree", "add", workspace, _branch],
                capture_output=True, text=True
            )

        if wt_result.returncode != 0:
            print(f"[Evolution] ERROR: Failed to create worktree: {wt_result.stderr.strip()}")
            print(f"[Evolution] The round will proceed but workspace may not be properly set up.")
        else:
            # Verify worktree was created successfully
            if os.path.isfile(os.path.join(workspace, ".git")):
                print(f"[Evolution] Worktree created at {workspace} (branch: {_branch})")
            else:
                print(f"[Evolution] WARNING: Worktree directory exists but .git marker not found!")

        mission = (
            f"Self-Evolution Round {round_num}.\n\n"
            f"Evolution History (last 5 rounds):\n"
            f"{json.dumps(evo_state.get('history', [])[-5:], indent=2, ensure_ascii=False)}\n\n"
            f"Past Failures to Avoid:\n"
            f"{json.dumps(evo_state.get('failures', [])[-10:], indent=2, ensure_ascii=False)}\n\n"
            f"Analyze the framework, find an improvement, implement it, test it, "
            f"and write a report to evolution_reports/."
        )
        print(f"\n[Evolution] ══════════════════════════════════════")
        print(f"[Evolution] Round     : {round_num}")
        print(f"[Evolution] Branch    : {evo_state['current_branch']}")
        print(f"[Evolution] Base from : {evo_state['base_branch']}")
        print(f"[Evolution] History   : {len(evo_state.get('history', []))} rounds recorded")
        print(f"[Evolution] ══════════════════════════════════════")
    else:
        # Normal mode: use architect prompt
        prompt_path = os.path.join(project_root, "src/prompts/architect.md")
        if not os.path.exists(prompt_path):
            print(f"Error: Prompt file not found at {prompt_path}")
            return

        with open(prompt_path, "r", encoding="utf-8") as f:
            architect_role_content = f.read()

        # 4. Determine Mission
        mission = args.query
        if not mission:
            print("\nPlease enter the Swarm Mission:")
            mission = input("> ").strip()

        if not mission:
            print("No mission provided. Exiting.")
            return

    blackboard_dir = os.path.join(project_root, ".blackboard")

    try:
        # 5. Initialize Watchdog Agent
        # Log Watchdog start for status tracking
        watchdog_log = os.path.join(blackboard_dir, "logs", f"{args.name}.log")
        os.makedirs(os.path.dirname(watchdog_log), exist_ok=True)
        with open(watchdog_log, "w", encoding="utf-8") as f:
            f.write(f"[{os.getpid()}] Watchdog Started\n")
            f.write(f"PID: {os.getpid()}\n")
            f.write(f"Mission: {mission}\n")
        
        # Initialize Middleware
        request_monitor = RequestMonitorMiddleware(blackboard_dir)
        watchdog_guard = ArchitectGuardMiddleware(
            agent_name=args.name,
            blackboard_dir=blackboard_dir,
            skip_user_verification=args.evolution
        )

        # The Watchdog uses the Architect role to design and spawn other agents.
        watchdog = SwarmAgent(
            role=architect_role_content,
            name=args.name,
            blackboard_dir=blackboard_dir,
            model=args.model,
            max_iterations=200,  # Increased Budget for Watchdog
            extra_strategies=[request_monitor, watchdog_guard],
            is_architect=True
        )
        
        # 6. Add Research Capabilities (Requested by User)
        watchdog.add_tool(SearchTool())
        watchdog.add_tool(WebReaderTool())

        env = LocalEnvironment(
            workspace_root=project_root,
            blackboard_dir=blackboard_dir,
            agent_name=args.name,
            evolution_mode=args.evolution,
            evolution_auto_approve=args.evolution_approve
        )
        watchdog.add_tool(BashTool(env=env))
        watchdog.add_tool(WriteFileTool(env=env))
        watchdog.add_tool(ReadFileTool(env=env))
        watchdog.add_tool(EditFileTool(env=env))
        watchdog.add_tool(GrepTool())
        watchdog.add_tool(GlobTool())

        # Evolution mode: add workspace commit/cleanup tool
        # finish_tool will BLOCK if this hasn't been called first
        if args.evolution:
            watchdog.add_tool(EvolutionWorkspaceTool())
            os.environ["NANO_EVOLUTION_MODE"] = "1"
            if args.evolution_approve:
                os.environ["NANO_EVOLUTION_AUTO_APPROVE"] = "1"

        print(f"\n[Launcher] Starting {args.name} ({args.role})")
        print(f"[Launcher] Mission: {mission}\n")
        
        if args.evolution:
            # Filtered output: full log to file, concise progress to terminal
            evo_log_path = os.path.join(project_root, "logs", f"evolution_r{evo_state['current_round']}_full.log")
            os.makedirs(os.path.dirname(evo_log_path), exist_ok=True)
            _evo_log_f = open(evo_log_path, "w", encoding="utf-8")
            _original_stdout = sys.stdout
            sys.stdout = EvolutionOutputFilter(_original_stdout, _evo_log_f)
            try:
                watchdog.run(
                    goal=f"The Evolution Mission is:\n{mission}",
                    scenario="You are the Evolution Architect. Follow the evolution protocol strictly."
                )
            finally:
                sys.stdout.flush()
                sys.stdout = _original_stdout
                _evo_log_f.close()
                print(f"[Launcher] Full log: {evo_log_path}")
        else:
            watchdog.run(
                goal=f"The User's Mission is: {mission}",
                scenario="You are the Root Architect. Analyze the mission, design the blackboard indices, and spawn agents to execute it.",
            )
    except KeyboardInterrupt:
        print("\n[Launcher] Interrupted by user.")
    finally:
        # 7. Archive Session
        archive_session()

if __name__ == "__main__":
    main()
