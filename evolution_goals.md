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
