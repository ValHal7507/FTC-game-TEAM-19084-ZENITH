# AGENTS.md

## Run

```bash
cd "FTC game"
python main.py
```

No pip install needed — only dependency is `pygame` (stdlib + pygame).

## Build

PyInstaller with `FTC_DECODE_Simulator.spec`:

```bash
cd "FTC game"
pyinstaller FTC_DECODE_Simulator.spec
```

Output: `dist/FTC_DECODE_Simulator.exe`. Copy to `EXECUTABLE/`.

## File Ownership Rule (Strict)

This is the #1 source of bugs if violated:

- **Shared files** (`game_logic.py`, `drawing.py`, `input_handler.py`) — P1/shared code only. Never add P2 function bodies here.
- **P2/MP-only files** (`game_logic_p2.py`, `drawing_1v1.py`, `input_handler_p2.py`, `ai_controller.py`) — Never edit for solo work.
- **One-way dependency**: MP-only files may import from shared files. Shared files may re-export from MP-only files (as `game_logic.py` does with P2 functions) but must never contain P2 function bodies.

If you're adding a solo feature, only touch `mode_solo.py`, `game_logic.py`, `drawing.py`, `input_handler.py`, `config.py`, `game_state.py`.

If you're adding a 1v1/vs_ai feature, touch the `*_p2*` / `*_1v1*` / `ai_controller.py` files.

## Threading

Physics runs on a **daemon thread** at 60 Hz. Main thread renders at 144 Hz. All shared `GameState` mutations must go through `_physics_lock`. The mode files (`mode_solo.py`, `mode_1v1.py`, `mode_vs_ai.py`) acquire the lock for timer updates and drawing.

- Gate toggle (`_toggle_gate`) acquires the lock internally.
- Turret angle updates run on the main thread outside the lock (GIL-atomic float writes).
- Reset acquires the lock to prevent physics thread from reading mid-reset.

## Font Import Quirk

Fonts in `drawing.py` are `None` until `init_drawing()` runs after `pygame.init()`. Modules that import fonts (like `menu.py`, `drawing_1v1.py`) must use:

```python
import drawing as _drawing
_drawing.f_huge.render(...)  # OK — late binding
```

NOT:

```python
from drawing import f_huge  # WRONG — captures None at import time
```

## Virtual Canvas

All drawing targets a fixed `1050 × 778` virtual canvas (`config.py` → `VW`, `VH`). The window is resizable; `main.py` scales via `smoothscale` with letterboxing. Never draw directly to the screen surface in game code.

## Key Constants

- `config.py` → `CONFIG` dict holds all tunable values (speeds, sizes, physics).
- `config.py` → derived constants: `VW`, `VH`, `FX`, `FY`, `FS`, `HX`, `HW`.
- Colors are module-level constants in `config.py` (e.g., `ZENITH_PURPLE`, `ALLIANCE_BLUE`).
- Keybinds: `DEFAULT_KEYBINDS` (P1) and `DEFAULT_KEYBINDS_P2` in `config.py`. Saved to `keybinds.json` / `keybinds_p2.json` on rebinding. Skipped in 1v1 mode (always defaults).

## GameState Lifecycle

- `GameState.__init__()` calls `_setup()` which creates artifacts and rebuilds the obstacle cache.
- `GameState.reset()` saves `game_mode`, `p1_device`, `p2_device`, `keybinds_p2`, then calls `_setup()`, then restores them.
- In 1v1 mode, keybinds are always hardcoded defaults (no JSON loading).
- Timer does NOT auto-start on reset. Must press F6/Y to start.

## Context

`CONTEXT.md` in `FTC game/` is the full project reference — module breakdown, data structures, physics details, scoring rules. Consult it when you need deep understanding of any subsystem.
