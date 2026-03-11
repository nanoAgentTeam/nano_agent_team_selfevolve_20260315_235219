# Evolution Goals — Product Vision

The evolution process should prioritize improvements that **users can see and feel**.

## Who uses this framework?

1. **TUI user** — interacts via `tui.py` terminal interface. Judges the product by what they can see, type, and get back.
2. **CLI user** — runs `main.py` with queries. Judges by output quality and feedback during execution.
3. **Evolve operator** — runs `evolve.sh`. Wants to see the framework get meaningfully better each round.

## What matters most?

- The TUI is the product's face. Improvements users can see in the TUI are worth more than internal refactoring.
- Agent capabilities expand what users can accomplish. New tools and smarter agent behaviors make the framework more useful.
- Observability helps users trust the system. If users can't tell what's happening or what it cost, they won't use it.

## What does NOT matter?

- Internal code cleanliness that changes zero user-visible behavior.
- Middleware or utilities that exist only to be "architecturally correct" but add no capability.
- Wrapping existing functionality in a new abstraction without enabling new use cases.

## Evolution Theme

Read `{{root_path}}/evolution_theme.md` for the **current evolution theme**. If set, research and proposals should align with the theme. This file is the user's steering mechanism for evolution direction.

## Evolution Surface Areas

The TUI (`src/tui/`) is now open for evolution. Consider the full surface:
- `src/tui/screens/` — what users see
- `src/tui/components/` — reusable UI elements
- `src/tui/slash_commands.py` — command system
- `src/tui/dialogs/` — user interactions
- `backend/tools/` — what agents can do
- `src/core/middlewares/` — how agents behave
- `backend/utils/` — shared infrastructure

Explore all of these. Don't default to the easiest one.

## Quality Red Lines (HARD CONSTRAINTS — violating any = automatic FAIL)

1. **No Duplication**: Before proposing ANY new module, grep the codebase for similar
   functionality. If an existing tool/middleware/utility already does 70%+ of the same
   thing, DO NOT create a new one — extend the existing module instead.

2. **No Dead Code**: Every new .py file MUST be reachable from a running code path.
   This framework has TWO entry points (main.py and src/tui/agent_bridge.py) — wire
   into BOTH, or explain why only one is needed.

3. **Read Before Write**: Do NOT create new tools/middleware without first reading the
   base class and at least one existing implementation in the same directory. Pattern
   violations (wrong base class, missing __call__, wrong method signature) are automatic FAIL.

4. **No Import Crashes**: Every new/modified .py file must be importable without
   optional dependencies. Guard third-party imports with try/except if the package
   may not be installed.

5. **No Hardcoded Paths**: Use {{blackboard}}, {{root_path}}, or config-based paths.
   Absolute paths to specific machines are forbidden.

6. **Protected Files Are Sacred**: Never modify files listed in the Protected Files
   section of the evolution protocol. No exceptions.
