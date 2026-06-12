# Agent Task: Split Game Modes into Separate Files

## Goal

Refactor the FTC DECODE Match Simulator so each of the three game modes has its own
dedicated Python file: `mode_solo.py`, `mode_1v1.py`, and `mode_vs_ai.py`.

Right now the game loop in `main.py` is one monolithic block with scattered
`if game_mode == "1v1":` branches. After this refactor, `main.py` becomes a thin
dispatcher, and each mode file owns its full frame loop.

---

## Target File Structure

```
FTC game/
├── main.py              # Thin entry point — init, menu routing, dispatch to mode files
├── mode_solo.py         # NEW — Solo game loop
├── mode_1v1.py          # NEW — 1v1 game loop
├── mode_vs_ai.py        # NEW — vs AI game loop (functional stub with simple AI)
├── config.py            # UNCHANGED
├── game_state.py        # UNCHANGED
├── drawing.py           # UNCHANGED
├── game_logic.py        # UNCHANGED
├── input_handler.py     # ONE CHANGE: expose _launch_held and _toggle_gate (see below)
├── menu.py              # ONE CHANGE: make vs AI selectable
├── keybinds.json
├── keybinds_p2.json
├── CONTROLS.md
└── CONTEXT.md           # Update at the end to reflect new structure
```

---

## Step 1 — Expose helpers in `input_handler.py`

The AI controller in `mode_vs_ai.py` needs to trigger launching and gate-toggling
programmatically. Both functions are currently private (`_launch_held`, `_toggle_gate`).

**Change:** Add two public aliases at the bottom of `input_handler.py`:

```python
# Public aliases for AI / mode files
launch_held  = _launch_held
toggle_gate  = _toggle_gate
```

Do NOT rename or modify the originals. Just add these two lines.

---

## Step 2 — Create `mode_solo.py`

This file owns the Solo game loop. Extract ALL solo-specific per-frame logic from
`main.py`. The file must expose one function:

```python
def run_solo(screen, canvas, clock, state) -> str:
    """
    Runs the Solo match loop.
    Returns:
      "menu"  — player chose 'Mode Select' from the pause menu
      "quit"  — player pressed Exit (Esc / gamepad B at match end, or F10)
    The physics thread is already running when this is called.
    """
```

### Frame loop body (in order):

1. `pygame.event.get()` — collect events once per frame, pass to everything that needs them
2. `handle_input(state, dt)` — P1 only; if it returns `True`, do `state.reset()` under
   `_physics_lock` (import lock from `game_logic`)
3. `update_turret_angle(state)` — P1 turret, runs outside the lock
4. Acquire `_physics_lock`:
   - `update_timer(state, dt)`
   - `draw_field(canvas, state)`
   - `draw_artifacts(canvas, state)`
   - `draw_robot(canvas, state)`
   - `draw_hud(canvas, state)`
   - `draw_match_end(canvas, state)` — only when `state.phase == "FINISHED"`
   - `draw_pause_menu(canvas, state)` — only when `not state.timer_running and state.phase != "FINISHED"`
5. Release lock
6. If `state.options_active`: `draw_options_screen(canvas, state)` (outside lock — same as current main.py)
7. Smoothscale `canvas` to `screen` preserving aspect ratio with black letterbox bars
8. `pygame.display.flip()`
9. `clock.tick_busy_loop(fps)` — fps from `config.CONFIG["fps"]`

### Return conditions to handle every frame:

- If pause menu "Mode Select" was selected (detect via `state.game_mode` being reset or
  add a flag — see note below): `return "menu"`
- If match end Exit button pressed (Esc / gamepad B): `return "quit"`
- If match end Restart pressed (Enter / gamepad A): `state.reset()` under lock, continue loop
- If `handle_end_game_input` (already in `main.py`) returns `"quit"`: `return "quit"`
- If `handle_end_game_input` returns `"restart"`: reset + continue

> **Note on detecting "Mode Select":** The cleanest approach is to add a `pending_return`
> string field to `GameState` (default `None`). When the pause menu "Mode Select" button
> is executed in `_execute_pause_action` inside `input_handler.py`, set
> `state.pending_return = "menu"` instead of doing nothing. At the top of each mode's
> frame loop, check: `if state.pending_return: r = state.pending_return; state.pending_return = None; return r`.
> Add `pending_return: str = None` to `GameState.__init__` / `_setup()`, reset it there too.
> This is the one small addition to `game_state.py` permitted.

---

## Step 3 — Create `mode_1v1.py`

Same structure as `mode_solo.py` but with P2 logic included. Expose:

```python
def run_1v1(screen, canvas, clock, state) -> str:
    """Same return contract as run_solo."""
```

### Differences from Solo frame loop:

- After P1 input: `handle_input_p2(state, dt)` — if it returns `True`, reset under lock
- After P1 turret: `update_turret_angle_r(state, state.robot2)` — P2 turret
- Inside the lock, add after `draw_robot`: `draw_robot2(canvas, state)`
- Inside the lock, add after `draw_field`: `draw_field_1v1_extras(canvas, state)`
- `draw_match_end` already handles the 1v1 side-by-side layout internally — no change needed
- Reset must preserve `game_mode`, `p1_device`, `p2_device`, `keybinds_p2` — `state.reset()` already does this per the context, so just call it under lock

Everything else is identical to `mode_solo.py`.

---

## Step 4 — Create `mode_vs_ai.py`

This mode uses the 1v1 infrastructure (two robots, full physics) but replaces
`handle_input_p2` with an internal AI controller. Expose:

```python
def run_vs_ai(screen, canvas, clock, state) -> str:
    """Same return contract as run_solo."""
```

### AI controller — define `_update_ai(state, dt)` inside this file:

The AI controls `state.robot2` / `state.team2`. It is a simple rule-based bot:

```
PRIORITY 1 — Overheat guard:
  If state.intake_overheated2: intake_active2 = False (already blocked, just ensure it)

PRIORITY 2 — If robot2 is holding < 3 artifacts AND nearest artifact within 300px:
  - Set intake_active2 = True
  - Drive robot2 toward nearest artifact:
      dx, dy = artifact.x - robot2.x, artifact.y - robot2.y
      dist = sqrt(dx*dx + dy*dy)
      robot2.vx = (dx/dist) * robot_speed
      robot2.vy = (dy/dist) * robot_speed
      robot2.angle = atan2(dx, -dy)  # face movement direction

PRIORITY 3 — If robot2 holds >= 1 artifact AND is inside in_launch_zone2:
  - Call launch_held(state, state.robot2, robot=state.robot2, team="p2")
    (imported from input_handler: `from input_handler import launch_held`)
  - If team2.gate_open is False and len(team2.ramp filled slots) > 0:
      call toggle_gate(state, state.robot2)

PRIORITY 4 — If robot2 holds >= 1 artifact AND NOT in launch zone:
  - Drive toward P2's launch zone center:
      target = (state.loading_rect2().centerx, state.loading_rect2().centery)
      ... same movement math as above

PRIORITY 5 — Idle (no artifacts reachable, holding 0):
  - intake_active2 = True (keep trying)
  - robot2.vx = 0, robot2.vy = 0
```

Use `config.CONFIG["robot_speed"]` for AI movement speed.
Use `state.nearest_artifact(robot2.x, robot2.y, 300)` to find closest artifact.
Use `state.in_launch_zone2(robot2.x, robot2.y)` to check launch eligibility.

The AI does NOT pause, reset, or open options.

### Frame loop:

Same as `mode_1v1.py` except:
- Replace `handle_input_p2(state, dt)` with `_update_ai(state, dt)`
- Keep `update_turret_angle_r(state, state.robot2)` — turret still auto-tracks goal
- Keep `draw_robot2`, `draw_field_1v1_extras`, `_draw_hud_1v1` — all 1v1 rendering applies
- P2 reset from `handle_input_p2` no longer applies — AI cannot reset

---

## Step 5 — Refactor `main.py`

Replace the large `while app_screen == "game":` block with a dispatcher:

```python
import mode_solo
import mode_1v1
import mode_vs_ai

# ... existing init, pygame.init(), joystick init, font init, state init, physics thread start ...

while True:
    # Menu loop (existing code — unchanged)
    while app_screen == "menu":
        # ... existing menu loop ...
        # When menu sets app_screen = "game", break

    if app_screen != "game":
        break  # quit

    # Dispatch to mode
    if state.game_mode == "solo":
        result = mode_solo.run_solo(screen, canvas, clock, state)
    elif state.game_mode == "1v1":
        result = mode_1v1.run_1v1(screen, canvas, clock, state)
    elif state.game_mode == "vs_ai":
        result = mode_vs_ai.run_vs_ai(screen, canvas, clock, state)
    else:
        result = "quit"

    if result == "quit":
        break
    elif result == "menu":
        app_screen = "menu"
        # loop continues back to menu

stop_physics_thread()
pygame.quit()
sys.exit()
```

Remove all per-frame logic that was extracted into the mode files. Keep in `main.py`:
- `pygame.init()`, window creation, canvas creation
- `init_drawing()`, `init_joysticks()`
- `GameState` instantiation
- `start_physics_thread(state)` call
- The menu loop (unchanged)
- The top-level `while True` dispatcher above
- `stop_physics_thread()` + `pygame.quit()` + `sys.exit()`

---

## Step 6 — Update `menu.py`

In `draw_mode_select()`, the vs AI button is currently stubbed out (not selectable).
Make it selectable:

- Remove the "not selectable" guard/grey-out for vs AI
- When vs AI is selected:
  - Set `state.game_mode = "vs_ai"`
  - Set `state.p1_device` via the existing controller-assign screen (P1 only — AI controls P2, no P2 device assignment needed)
  - Set `state.p2_device = ("ai",)` as a sentinel (so the rest of the code can distinguish)
  - Return from the menu to start the game

In `draw_controller_assign()`, skip the P2 assign phase when `state.game_mode == "vs_ai"`.

---

## Hard Constraints

1. Do NOT modify `config.py`, `drawing.py`, or `game_logic.py`.
2. The only permitted change to `game_state.py` is adding `pending_return: str = None`
   to `__init__` / `_setup()` and clearing it in `reset()`.
3. The only permitted change to `input_handler.py` is adding the two public alias lines
   at the bottom. Do not rename or touch any existing function.
4. `_physics_lock` must be acquired before any draw + timer update call, released after —
   identical pattern to the current `main.py`. Never hold the lock across frame boundaries.
5. `start_physics_thread()` and `stop_physics_thread()` stay in `main.py` only.
6. All existing keybind, pause menu, and options screen behavior must be preserved
   byte-for-byte in solo and 1v1 modes.
7. Each mode file must import only what it uses. No wildcard imports.
8. After the refactor, the project must run identically for solo and 1v1 modes.
   vs AI must launch without crashing (stub AI is acceptable behavior).

---

## Deliverable Checklist

- [ ] `mode_solo.py` created with `run_solo()`
- [ ] `mode_1v1.py` created with `run_1v1()`
- [ ] `mode_vs_ai.py` created with `run_vs_ai()` and `_update_ai()`
- [ ] `main.py` refactored to thin dispatcher
- [ ] `menu.py` updated — vs AI selectable, P2 assign skipped for vs AI
- [ ] `input_handler.py` updated — `launch_held` and `toggle_gate` aliases added
- [ ] `game_state.py` updated — `pending_return` field added
- [ ] `CONTEXT.md` updated — new file structure and mode file descriptions added
- [ ] Solo mode: plays identically to before
- [ ] 1v1 mode: plays identically to before
- [ ] vs AI mode: launches, P2 robot moves autonomously, no crash
