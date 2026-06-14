# FTC DECODE Match Simulator — Project Context

A 2D match simulator for the FIRST Tech Challenge 2025–2026 game "DECODE," supporting **Solo** and **1v1 local multiplayer** modes, built with **Python 3 + Pygame**.

---

## Project Structure

```
FTC game/
├── main.py              # [SHARED] Entry point, app-level screen routing, thin dispatcher to mode files
├── menu.py              # [SHARED] Mode-select screen, controller-assignment screen
├── config.py            # [SHARED] Colors, CONFIG dict, layout constants, math helpers, keybinds
├── game_state.py        # [SHARED] Data classes: Artifact, FlyingArtifact, Robot, TeamState, GameState
│
├── mode_solo.py         # [SOLO ONLY] Solo game loop (single player)
├── mode_1v1.py          # [MP ONLY] 1v1 local multiplayer game loop
│
├── game_logic.py        # [SHARED] Timer, scoring, P1 physics — re-imports P2 functions from game_logic_p2
├── game_logic_p2.py     # [MP ONLY] P2 physics, scoring, robot constraints
│
├── drawing.py           # [SHARED] Field, artifacts, P1 robot, HUD, match-end overlay, pause menu
├── drawing_1v1.py       # [MP ONLY] P2 robot rendering, 1v1 field extras
│
├── input_handler.py     # [SHARED] P1 input, pause/start/reset controls, public aliases
├── input_handler_p2.py  # [MP ONLY] P2 input handling
├── ai_controller.py     # [1v1 ONLY] AI logic for P2 robot (used when P2 is assigned AI) — wired into mode_1v1.py (vs AI now functional)
│
├── keybinds.json        # Saved custom keybinds (P1, created on first rebinding, loaded on startup; skipped in 1v1)
├── keybinds_p2.json     # Saved custom keybinds (P2, created on first rebinding; skipped in 1v1)
├── CONTROLS.md          # User-facing controls guide (Romanian)
└── CONTEXT.md           # This file
```

No external dependencies beyond Python stdlib and `pygame`.

**File ownership rule (enforced from refactoring onward):**
- `game_logic_p2.py` → ALL P2 physics. Never edited for solo work.
- `drawing_1v1.py` → ALL P2/1v1 rendering. Never edited for solo work.
- `input_handler_p2.py` → ALL P2 input. Never edited for solo work.
- `ai_controller.py` → ALL AI logic. Used by `mode_1v1.py` when P2 is assigned AI. Never edited for anything else.
- `game_logic.py` → Shared physics only (no P2 function bodies).
- `drawing.py` → Shared rendering only (no P2 function bodies).
- `input_handler.py` → P1 and shared input only (no handle_input_p2).

---

## Module Breakdown

### `main.py` — Entry Point

- Initializes Pygame, creates a **resizable window** (`pygame.RESIZABLE`) titled `"FTC DECODE — Robot simulator by TEAM ZENITH 19084"`
- Creates a fixed-size **virtual canvas** (`1050 × 778`) that all drawing targets
- **App-level screen routing**: Three top-level screens — Mode Select, Controller Assign, Game Loop. `app_screen` variable (`"mode_select"`, `"controller_assign"`, `"game"`) controls which loop runs.
- **Mode-select mini-loop**: Runs before any match. User picks Solo or 1v1. On Solo, creates `GameState` and enters game directly. On 1v1, proceeds to controller-assign screen.
- **Controller-assign screen**: Defaults are set automatically based on detected gamepads: 2+ gamepads → P1 = Gamepad 1, P2 = Gamepad 2; 1 gamepad → P1 = Gamepad 1, P2 = AI; 0 gamepads → P1 = Gamepad 1 (not found), P2 = AI. User can change selections. P1 picks Gamepad 1 or Gamepad 2. P2 picks Gamepad 1, Gamepad 2, or AI. Same gamepad ID is blocked.
- **Dispatcher**: After menu selection, dispatches to `mode_solo.run_solo()` or `mode_1v1.run_1v1()`. Each mode file owns its full frame loop and physics thread lifecycle.
- Uses `clock.tick_busy_loop(fps)` for precise frame pacing
- Calls `init_drawing()` after `pygame.init()` to initialize fonts (must happen after pygame init)
- Detects and initializes joysticks on startup via `input_handler.init_joysticks()`
- On return from mode (result `"menu"`), loops back to mode-select screen

**Functions:**
| Function | Signature | Behavior |
|---|---|---|
| `_blit_scaled` | `(canvas, screen)` | Scale virtual canvas to window with letterboxing (aspect-ratio preservation) |
| `main` | `()` | Full app lifecycle: init → menu loop → dispatch → cleanup |

### `mode_solo.py` — Solo Game Loop

- Owns the full Solo match frame loop
- Exposes `run_solo(screen, canvas, clock, state) -> str` returning `"menu"` or `"quit"`
- Starts and stops the physics thread internally
- Frame loop: check pending_return → collect events → handle QUIT/RESIZE → FINISHED-phase end-game navigation → normal gameplay (handle_input → turret update → lock → timer + render → unlock → blit → flip)
- Checks `state.pending_return` at top of loop for Mode Select from pause menu
- Handles match-end button navigation (Restart/Exit) via keyboard only

**Functions:**
| Function | Signature | Behavior |
|---|---|---|
| `_blit_scaled` | `(canvas, screen)` | Scale virtual canvas to window with letterboxing |
| `run_solo` | `(screen, canvas, clock, state) -> str` | Main solo game loop. Returns `"menu"` or `"quit"`. Starts/stops physics thread. |

### `mode_1v1.py` — 1v1 Local Multiplayer Game Loop

- Owns the full 1v1 match frame loop
- Exposes `run_1v1(screen, canvas, clock, state) -> str` returning `"menu"` or `"quit"`
- Same frame structure as `mode_solo.py` but adds P2 logic:
   - After P1 input: `handle_input_p2(state, dt, events)` — if `state.p2_device == "ai"`, P2 input is skipped (robot does nothing; AI IS now wired)
  - After P1 turret: `update_turret_angle_r(state, state.robot2)` — P2 turret
  - Inside lock: `draw_field_1v1_extras()`, `draw_robot2()` for P2 rendering
- `draw_match_end` handles side-by-side 1v1 scores internally
- Reset preserves `game_mode`, `p1_device`, `p2_device`

**Functions:**
| Function | Signature | Behavior |
|---|---|---|
| `_blit_scaled` | `(canvas, screen)` | Scale virtual canvas to window with letterboxing |
| `run_1v1` | `(screen, canvas, clock, state) -> str` | Main 1v1 game loop. Returns `"menu"` or `"quit"`. Starts/stops physics thread. |

### `menu.py` — Mode-Select and Controller-Assign Screens

- **`draw_mode_select(screen, selected_index)`**: Renders the mode-select overlay with buttons. Navigation via Up/Down arrows or Numpad 8/2. Selection via Enter/Space.
   - Modes: `"SOLO PRACTICE"` and `"1v1 LOCAL"` (vs AI now functional)
  - ZENITH branding and team tagline displayed
- **`handle_mode_select(events, keys, selected_index)`**: Returns `(new_selected_index, chosen_mode | None)`. Chosen mode is `"solo"` or `"1v1"`.
- **`draw_controller_assign(screen, selected_p1, selected_p2, num_joysticks, conflict, game_mode)`**: Two-column screen for 1v1 mode:
  - P1 column (BLUE): Gamepad 1, Gamepad 2
  - P2 column (RED): Gamepad 1, Gamepad 2, AI
  - On same-gamepad conflict: shows warning message
  - Navigation: Left/Right to switch columns, Up/Down to select device
  - Device format: plain strings — `"gamepad0"`, `"gamepad1"`, or `"ai"`
- **`handle_controller_assign(events, keys, selected_p1, selected_p2, focused_col, num_joysticks, game_mode)`**: Returns `(new_p1, new_p2, new_focused_col, result)`. Result is `None` | `"back"` | `(p1_device_str, p2_device_str)`.
- Font access: uses `import drawing as _drawing` then `_drawing.f_huge.render(...)` (not `from drawing import f_huge`) to avoid `None` before `init_drawing()` runs

### `config.py` — Constants

**Color palette** (all RGB/RGBA tuples):
| Constant | Value | Usage |
|---|---|---|
| `BLACK` | `(0, 0, 0)` | Basic black |
| `WHITE` | `(255, 255, 255)` | Basic white |
| `GRAY` | `(140, 140, 150)` | Basic gray |
| `DARK_GRAY` | `(35, 35, 40)` | Grid lines, field background elements |
| `BG_DARK` | `(22, 22, 28)` | App background, HUD panel |
| `CHARCOAL` | `(50, 50, 56)` | Field background fill |
| `LIGHT_GRAY` | `(190, 190, 200)` | Light text and highlights |
| `SOFT_WHITE` | `(220, 220, 230)` | Zone outlines, labels |
| `ROBOT_PURPLE` | `(69, 23, 163)` | Robot fill, base zone outline (ZENITH brand) |
| `ROBOT_DARK` | `(100, 20, 160)` | Robot dark shade |
| `GLOW_PURPLE` | `(160, 100, 255)` | Brighter glow variant of team purple |
| `ZENITH_PURPLE` | `(69, 23, 163)` | Official team primary color (#4517a3) |
| `ZENITH_ACCENT` | `(180, 140, 255)` | Soft lavender — light text on dark bg |
| `ZENITH_DARK` | `(25, 8, 60)` | Near-black deep purple — header bg |
| `ZENITH_LABEL` | `"ZENITH  19084"` | Full display string |
| `ZENITH_TAG` | `"Visions above ground"` | Team tagline |
| `GOAL_GOLD` | `(210, 170, 60)` | Goal outline |
| `GOAL_DARK` | `(140, 110, 30)` | Goal fill |
| `RAMP_DARK` | `(60, 55, 50)` | Ramp background |
| `SLOT_EMPTY` | `(45, 42, 38)` | Empty ramp slot |
| `SLOT_BORDER` | `(70, 65, 58)` | Ramp slot border |
| `GATE_COLOR` | `(200, 170, 60)` | Gate closed state |
| `GATE_OPEN_COLOR` | `(60, 200, 80)` | Gate open state |
| `PURPLE` | `(165, 40, 235)` | Artifact color "P" |
| `GREEN` | `(55, 210, 85)` | Artifact color "G" |
| `PURPLE_DIM` | `(100, 25, 140)` | Dimmed purple artifact |
| `GREEN_DIM` | `(35, 130, 55)` | Dimmed green artifact |
| `GOLD` | `(255, 210, 40)` | UI text, highlights |
| `ORANGE` | `(255, 150, 20)` | UI text, ENDGAME phase |
| `YELLOW_ACCENT` | `(255, 240, 120)` | Available for general use |
| `RED_ACCENT` | `(240, 70, 70)` | Match-end overlay (not parked), duplicate warning |
| `TEAL_ACCENT` | `(40, 200, 210)` | Available for general use |
| `PARK_GREEN` | `(80, 220, 100)` | Parking status indicator (full park) |
| `HEAT_GREEN` | `(60, 200, 80)` | Intake heat bar: cool (low heat) |
| `HEAT_YELLOW` | `(230, 200, 40)` | Intake heat bar: warm (mid heat) |
| `HEAT_ORANGE` | `(240, 140, 30)` | Intake heat bar: hot (high heat) |
| `HEAT_RED` | `(220, 50, 40)` | Intake heat bar: critical / cooldown text |
| `PAUSE_OVERLAY` | `(0, 0, 0, 180)` | Semi-transparent black overlay for pause menu |
| `MENU_BG` | `(30, 30, 36)` | Pause menu panel background |
| `MENU_BORDER` | `(69, 23, 163)` | Pause menu panel border (ZENITH_PURPLE) |
| `MENU_HIGHLIGHT_BG` | `(40, 18, 95)` | Pause menu highlighted button background |
| `MENU_HIGHLIGHT_BORDER` | `(180, 140, 255)` | Pause menu highlighted button border (ZENITH_ACCENT) |
| `MENU_TEXT` | `(220, 220, 230)` | Pause menu button text |
| `MENU_TITLE` | `(180, 140, 255)` | Pause menu "PAUSED" title text (ZENITH_ACCENT) |
| `OPTIONS_REBIND` | `(255, 100, 60)` | Options screen rebinding pulse color |
| `OPTIONS_BIND` | `(100, 200, 140)` | Options screen selected binding color |
| `ALLIANCE_BLUE` | `(60, 130, 220)` | P1 robot alliance (1v1) — primary blue |
| `ALLIANCE_BLUE_DIM` | `(30, 70, 120)` | P1 robot alliance (1v1) — dimmed blue (idle LED) |
| `ALLIANCE_RED` | `(220, 50, 50)` | P2 robot alliance (1v1) — primary red |
| `ALLIANCE_RED_DIM` | `(120, 30, 30)` | P2 robot alliance (1v1) — dimmed red (idle LED) |

**`CONFIG` dict** — All tunable magic numbers:
| Key | Value | Purpose |
|---|---|---|
| `field_size_px` | 720 | Field side length in pixels (144" at 5 px/in) |
| `fps` | 144 | Target frames per second |
| `teleop_time` | 120 | Match duration in seconds |
| `endgame_time` | 20 | Last N seconds where phase shows "ENDGAME" |
| `robot_speed` | 280 | Robot movement speed (px/s) |
| `robot_size` | 60 | Robot square side length (px) |
| `flying_speed` | 350 | Launched artifact travel speed (px/s) |
| `pickup_radius` | 45 | Max distance to pick up an artifact |
| `pickup_cone_angle` | 120 | Front cone for pickup (degrees) |
| `rotation_speed` | 300 | Robot rotation speed (deg/s) |
| `gate_range` | 45 | Max distance to interact with gate |
| `gate_open_duration` | 2.0 | Seconds before gate auto-closes |
| `spike_mark_count` | 3 | Number of spike marks per player side |
| `ramp_slots` | 9 | Number of classifier slots per ramp |
| `max_hold` | 3 | Max artifacts robot can carry |
| `respawn_delay` | 5.0 | Artifact respawn delay (unused) |
| `artifact_friction` | 0.08 | Exponential drag per frame (v *= f^dt) |
| `artifact_bounce` | 0.45 | Wall/structure restitution |
| `artifact_robot_bounce` | 0.90 | Robot-artifact collision restitution |
| `artifact_artifact_bounce` | 0.50 | Artifact-artifact restitution |
| `artifact_min_speed` | 4.0 | Speed below which artifacts stop |
| `robot_push_force` | 600.0 | Push force when robot contacts artifact |
| `artifact_radius` | 7 | Radius of artifact circles |
| `goal_w` | 130 | Goal rectangle width |
| `goal_h` | 142 | Goal rectangle height |
| `loading_zone_size` | 100 | Loading zone square size |
| `base_size` | 80 | Base zone square size |
| `shooting_zone_size` | 220 | Shooting zone triangle hypotenuse width (px) |
| `spike_cols` | 1 | Spike mark columns per player side |
| `spike_rows` | 3 | Spike mark rows |
| `ramp_h` | 14 | Ramp rectangle height (px) |
| `depot_h` | 20 | Depot rectangle height (px) |
| `field_margin_left` | 5 | Left margin between field and canvas edge |
| `field_margin_top` | 5 | Top margin between field and canvas edge |
| `hud_width` | 320 | HUD panel width |
| `hud_margin` | 5 | Gap between field and HUD panel |
| `intake_heat_time` | 10.0 | Seconds for intake to overheat when running |
| `intake_cool_time` | 4.0 | Seconds to cool from partial heat (intake off, heat < 1.0) |
| `intake_cooldown_time` | 10.0 | Seconds blocked after full overheat (bar drains during cooldown) |

**Derived layout constants** (computed from CONFIG):
| Constant | Value | Meaning |
|---|---|---|
| `VW`, `VH` | 1050, 778 | Virtual canvas dimensions (`VW` = field + margins + HUD; `VH` = field + margin + 5 + 48) |
| `FX`, `FY` | 5, 5 | Field top-left corner on canvas |
| `FS` | 720 | Field size (alias for `field_size_px`) |
| `HX`, `HW` | 730, 320 | HUD panel left edge and width |

**Helpers**: `dist(a, b)`, `clamp(v, lo, hi)`, `lerp(a, b, t)`

**Backward-compatible aliases**: `W, H = VW, VH` (used by drawing.py, menu.py)

**Global render state**: `scale_factor = 1.0`, `render_surf = None` (set by main.py)

**Keybind constants:**
- `GAMEPAD_NAMES` — dict mapping `("button", N)` / `("axis", N)` tuples to human-readable names (e.g., `"A"`, `"LT (axis 4)"`)
- `KEYBIND_ACTIONS_KEYBOARD` — list of 10 keyboard action names: Move Forward, Move Backward, Strafe Left, Strafe Right, Rotate Left, Rotate Right, Toggle Intake, Launch Artifacts, Toggle Gate, Drive Mode
- `KEYBIND_ACTIONS_GAMEPAD` — list of 5 gamepad action names: Launch, Intake, Gate, Pause, Drive Mode
- `DEFAULT_KEYBINDS` — dict with `"keyboard"` and `"gamepad"` sub-dicts mapping action names to binding tuples like `("key", pygame.K_w)` or `("axis", 4)`
- `DEFAULT_KEYBINDS_P2` — P2 keyboard defaults: `I` (fwd), `K` (back), `J` (left), `L` (right), `U` (rot left), `O` (rot right), `P` (intake), `;` (launch), `.` (gate), `M` (drive mode)
- `LOCKED_KEYBINDS` — dict of actions that cannot be rebound: `{"keyboard": set(), "gamepad": {"Reset"}}`
- `save_keybinds(keybinds)` — writes P1 keybinds to `keybinds.json` (JSON, tuples→lists). Never raises.
- `save_keybinds_p2(keybinds)` — writes P2 keybinds to `keybinds_p2.json` (JSON, tuples→lists). Never raises.
- `load_keybinds()` → `dict | None` — reads `keybinds.json`, converts lists→tuples. Returns `None` on any error. **Not called in 1v1 mode** — keybinds always use `DEFAULT_KEYBINDS`.
- `load_keybinds_p2()` → `dict | None` — reads `keybinds_p2.json`, converts lists→tuples. Returns `None` on any error. **Not called in 1v1 mode** — keybinds always use `DEFAULT_KEYBINDS_P2`.

---

### `game_state.py` — Data Classes

**Module-level helpers:**
- `_sign(p1, p2, p3)` — Signed area of triangle (p1, p2, p3). Used for point-in-triangle test.
- `_point_in_triangle(pt, v1, v2, v3)` — Return True if pt is inside triangle defined by v1, v2, v3 (sign-of-cross-product method).

#### `Artifact`
| Field | Type | Default | Description |
|---|---|---|---|
| `x` | `float` | — | Position on canvas |
| `y` | `float` | — | Position on canvas |
| `color` | `str` | — | `"P"` (purple) or `"G"` (green) |
| `vx` | `float` | `0.0` | 2D velocity for physics integration |
| `vy` | `float` | `0.0` | 2D velocity for physics integration |
| `on_field` | `bool` | `True` | `True` if available for pickup |
| `zone` | `str` | `"spike"` | `"spike"`, `"loading"`, or `"alliance"` |
| `respawn_timer` | `float` | `0.0` | Unused (no respawning) |
| `index` | `int` | `0` | Position within spike zone |

#### `FlyingArtifact`
| Field | Type | Default | Description |
|---|---|---|---|
| `x` | `float` | — | Current position (animated toward target) |
| `y` | `float` | — | Current position |
| `target_x` | `float` | — | Goal center X |
| `target_y` | `float` | — | Goal center Y |
| `color` | `str` | — | Artifact color |
| `speed` | `float` | `CONFIG["flying_speed"]` | Travel speed |
| `active` | `bool` | `True` | Whether artifact is in flight |
| `trail` | `List[Tuple]` | `[]` | Recent positions for trail rendering (capped at `MAX_TRAIL`) |
| `scoring` | `bool` | `True` | `True` if launched from launch zone |
| `full_set` | `bool` | `False` | `True` if robot held 3 artifacts at launch |
| `team` | `str` | `"p1"` | `"p1"` or `"p2"` — determines which `TeamState` scores |
| `MAX_TRAIL` | `ClassVar[int]` | `18` | Max trail length (class variable) |

#### `GateClearAnim`
| Field | Type | Default | Description |
|---|---|---|---|
| `x` | `float` | — | Animation start X |
| `y` | `float` | — | Animation start Y |
| `target_x` | `float` | — | Animation end X |
| `target_y` | `float` | — | Animation end Y |
| `color` | `str` | — | Artifact color being cleared |
| `progress` | `float` | `0.0` | Animation progress (0.0 to 1.0) |
| `active` | `bool` | `True` | Whether animation is still running |

#### `Robot`
| Field | Type | Default | Description |
|---|---|---|---|
| `x` | `float` | — | Position on canvas |
| `y` | `float` | — | Position on canvas |
| `speed` | `float` | `CONFIG["robot_speed"]` | Movement speed (px/s) |
| `angle` | `float` | `0.0` | Facing direction (0 = up, radians) |
| `turret_angle` | `float` | `0.0` | World-space radians, auto-updated toward goal each frame |
| `vx` | `float` | `0.0` | Velocity from input (used for physics push) |
| `vy` | `float` | `0.0` | Velocity from input |
| `drive_mode` | `str` | `"field"` | `"robot"` or `"field"` |
| `holding` | `List[Artifact]` | `[]` | Artifacts being carried (max 3) |
| `start_x` | `float` | `0.0` | Initial position (set from `x` via `__post_init__`) |
| `start_y` | `float` | `0.0` | Initial position (set from `y` via `__post_init__`) |
| `alliance` | `str` | `"neutral"` | `"neutral"` (solo), `"blue"` (P1 in 1v1), or `"red"` (P2 in 1v1) |
| `can_pickup()` | method | — | Returns `True` if `len(holding) < CONFIG["max_hold"]` |

**`__post_init__`:** Sets `start_x = x` and `start_y = y` from the constructor position args.

#### `TeamState`
| Field | Type | Default | Description |
|---|---|---|---|
| `ramp` | `List[Optional[str]]` | `[None]*9` | Ramp slots (`None` = empty, `"P"`/`"G"` = occupied) |
| `overflow_held` | `List[str]` | `[]` | Overflow artifacts stored in ramp (released on gate open) |
| `gate_open` | `bool` | `False` | Gate state |
| `gate_timer` | `float` | `0.0` | Gate auto-close countdown |
| `classified` | `int` | `0` | Count of classified artifacts (+3 pts each) |
| `overflow` | `int` | `0` | Count of overflow artifacts (+1 pt each) |
| `depot` | `int` | `0` | Count of depot artifacts (+1 pt each) |
| `pattern_pts` | `int` | `0` | Pattern match score (evaluated at match end) |
| `base_pts` | `int` | `0` | Parking score (evaluated at match end) |

**Methods:**
| Method | Signature | Behavior |
|---|---|---|
| `total_score()` | `-> int` | `classified×3 + overflow + depot + pattern_pts + base_pts` |
| `add_to_ramp(color)` | `(str) -> bool` | Place in first empty slot → classified++; else overflow_held.append → overflow++, depot++. Returns True if slot found. |
| `clear_ramp()` | `-> List[str]` | Empties ramp + overflow_held, returns all colors |

#### `GameState`
| Field | Type | Default | Description |
|---|---|---|---|
| `phase` | `str` | `"TELEOP"` | `"TELEOP"` → `"ENDGAME"` → `"FINISHED"` |
| `timer` | `float` | `CONFIG["teleop_time"]` | Seconds remaining |
| `timer_running` | `bool` | `False` | Timer does NOT auto-start on launch or reset |
| `motif` | `list` | random choice | `["G","P","P"]`, `["P","G","P"]`, or `["P","P","G"]` |
| `motif_name` | `str` | joined motif | e.g., `"GPP"` |
| `team` | `TeamState` | — | P1 scoring state |
| `team2` | `TeamState` | `None` | P2 scoring state (1v1 only) |
| `robot` | `Robot` | — | P1 robot (left-center, facing right) |
| `robot2` | `Robot` | `None` | P2 robot (right-center, facing left; 1v1 only) |
| `artifacts` | `List[Artifact]` | — | All artifacts (18 solo + 18 mirrored in 1v1 = 36 total) |
| `flying` | `List[FlyingArtifact]` | `[]` | Active flying artifacts (shared by both players) |
| `gate_clears` | `List[GateClearAnim]` | `[]` | Gate-clearing animations |
| `secret_tunnel` | `tuple` | center of field | Center of field coordinates |
| `scored` | `bool` | `False` | Scoring flag |
| `park_status` | `str` | `"NONE"` | `"NONE"`, `"PARTIAL"`, or `"FULL"` (P1, live-updated) |
| `park_status2` | `str` | `"NONE"` | `"NONE"`, `"PARTIAL"`, or `"FULL"` (P2, 1v1 only) |
| `intake_active` | `bool` | `False` | P1 intake hold state |
| `intake_heat` | `float` | `0.0` | P1 motor temperature (0.0 cold → 1.0 overheated) |
| `intake_overheated` | `bool` | `False` | P1 10-second cooldown after full overheat |
| `intake_cooldown_timer` | `float` | `0.0` | Seconds remaining in P1 overheat cooldown |
| `intake_active2` | `bool` | `False` | P2 intake hold state (1v1 only) |
| `intake_heat2` | `float` | `0.0` | P2 intake heat (1v1 only) |
| `intake_overheated2` | `bool` | `False` | P2 intake overheat state (1v1 only) |
| `intake_cooldown_timer2` | `float` | `0.0` | P2 intake cooldown timer (1v1 only) |
| `pause_menu_index` | `int` | `0` | Selected pause menu button index |
| `options_active` | `bool` | `False` | Whether Options screen is open |
| `options_page` | `int` | `0` | Current Options tab (0 = keyboard, 1 = gamepad) |
| `options_index` | `int` | `0` | Selected row in Options screen |
| `options_rebinding` | `bool` | `False` | `True` when waiting for new key/button input |
| `keybinds` | `dict` | defaults/saved | P1 key bindings |
| `keybinds_p2` | `dict` | defaults | P2 key bindings (1v1 only) |
| `game_mode` | `str` | constructor arg | `"solo"` or `"1v1"` |
| `p1_device` | `str` | `"keyboard"` | Assigned P1 input device |
| `p2_device` | `str` | `"gamepad1"` | Assigned P2 input device: `"gamepad0"`, `"gamepad1"`, or `"ai"` |
| `pending_return` | `str \| None` | `None` | Set to `"menu"` by pause menu "Mode Select" action |

**Methods:**
| Method | Signature | Behavior |
|---|---|---|
| `_setup()` | `()` | Shared init logic called by `__init__` and `reset()`. Creates artifacts, rebuilds obstacle cache. In 1v1, skips loading keybinds JSON. |
| `reset()` | `()` | Saves `game_mode`, `p1_device`, `p2_device`, calls `_setup()`, restores them. In 1v1, skips saving/restoring keybinds_p2. Imports and calls `reset_ai()` when in 1v1 mode to reset AI state. |
| `_init_artifacts()` | `()` | Creates 18 base artifacts: 9 spike-mark (1 col × 3 rows), 3 loading-zone (PGP), 6 alliance-area (4P+2G random) |
| `_add_1v1_artifacts()` | `()` | Adds 18 mirrored artifacts for P2's side (1v1 only) |
| `goal_rect()` | `-> pygame.Rect` | Goal rectangle |
| `ramp_rect()` | `-> pygame.Rect` | Ramp rectangle below goal |
| `depot_rect()` | `-> pygame.Rect` | Depot rectangle below ramp |
| `gate_rect()` | `-> pygame.Rect` | Gate rectangle on right side of ramp |
| `loading_rect()` | `-> pygame.Rect` | Loading zone rectangle (top-left) |
| `base_rect()` | `-> pygame.Rect` | Base/parking zone rectangle (left-center) |
| `base_rect2()` | `-> pygame.Rect` | P2 base zone — horizontal mirror (right-center, 1v1 only) |
| `loading_rect2()` | `-> pygame.Rect` | P2 loading zone — horizontal mirror (top-right, 1v1 only) |
| `shooting_zone_triangle()` | `-> tuple` | Returns three vertices `(top, bl, br)` of the shooting zone triangle |
| `in_launch_zone(x, y)` | `(float, float) -> bool` | Checks P1's launch zone (top triangle OR base/parking zone OR shooting zone) |
| `in_launch_zone2(x, y)` | `(float, float) -> bool` | Checks P2's mirrored zones (1v1 only) |
| `nearest_artifact(x, y, radius)` | `(float, float, float) -> Artifact \| None` | Finds closest pickup-able artifact within radius |

**Module-level function:**
- `get_ramp_scatter_positions(state)` → `List[Tuple[float, float]]` — Returns 15 positions (9 spike-mark + 6 loading zone for both sides) for gate-release teleport

---

### `drawing.py` — Rendering (Shared Only)

**Initialization:**
- `init_drawing()` — must be called once after `pygame.init()`; initializes all fonts
- `init_fonts` — backward-compatible alias for `init_drawing()`
- `_make_font(name, size)` — helper to create a system font with fallback to default

**Font sizes** (Segoe UI, with fallback):
| Name | Size | Usage |
|---|---|---|
| `f_micro` | 14 | Spike labels |
| `f_tiny` | 17 | Score lines, zone labels, launch zone indicator, parking status label, intake cooldown timer |
| `f_small` | 21 | Section headers, robot label |
| `f_hud_s` | 26 | "SCORE" heading |
| `f_hud` | 34 | Phase text |
| `f_timer` | 56 | Countdown clock |
| `f_huge` | 68 | "MATCH OVER" title |

**Caching:**

Three independent caches improve rendering performance:

1. **Field surface cache** — Static field elements (background, grid, loading zone, goal outline, ramp outline, gate outline, depot, spike marks, launch zone triangle, shooting zone triangle) rendered once to `_field_surface`. Dynamic elements (park status pulse/glow, ramp slot fill, gate open/closed state, drive mode badge) are drawn on top each frame. Cache is rebuilt automatically on first draw. Invalidated via `_invalidate_field_cache()`. Park-specific cache state tracked in `_field_cache_park`.

2. **Robot render cache** — The full 96×96 SRCALPHA robot surface is cached in a dict keyed on `(angle_deg, turret_deg, held_colors, alliance)` via `_robot_cache_key(r)`. Turret angle is quantized to 2° increments (sub-pixel difference at the turret's small size) to maintain good cache hit rate while tracking the goal. Alliance is included in the key so P1 (blue) and P2 (red) robots have distinct cache entries. FIFO eviction via `collections.deque` caps the cache at 360 entries to prevent unbounded memory growth. Surface built by `_build_robot_surface(r)`.

3. **Match-end overlay cache** — The semi-transparent "MATCH OVER" overlay is rendered once to `_end_overlay` by `_build_end_overlay(state)` when the phase transitions to FINISHED. Invalidated (set to `None`) on reset so it rebuilds on next match end.

**Alliance-tinted robot rendering:**
- `draw_robot()` (P1) and `draw_robot2()` (P2) use the same `_build_robot_surface(r)` renderer
- Robot fill color tinted: red alliance → ZENITH_PURPLE + ALLIANCE_RED dim; blue alliance → ZENITH_PURPLE + ALLIANCE_BLUE dim
- REV hub status LED: red = ALLIANCE_RED, blue = ALLIANCE_BLUE
- Mecanum wheel rollers: red = ALLIANCE_RED, blue = ALLIANCE_BLUE
- Robot cache key includes `r.alliance` so red/blue robots have separate cache entries

**Drawing functions** (all take `(screen, state)` unless noted):

| Function | Location | Draws |
|---|---|---|
| `draw_field()` | `drawing.py` | Static field elements from cache + dynamic per-frame: drive mode badge (ZENITH purple theme), base zone park status (fill + pulse/glow), ramp slot fill, gate open/closed state |
| `draw_field_1v1_extras()` | `drawing_1v1.py` | 1v1-only: P2's base rect (2px ALLIANCE_RED outline + fill + park pulse/glow), mirrored loading zone (SOFT_WHITE outline/text, matching P1). |
| `draw_artifacts()` | `drawing.py` | Field artifacts (with glow and motion ghost), flying artifacts (each as individual colored circle with alpha-blended fading trail capped at `MAX_TRAIL`). Trail color matches artifact's own color (green or purple); white outline around each flying artifact. |
| `draw_robot()` | `drawing.py` | **P1 ZENITH (FTC 19084) layered render with cache**: 96×96 SRCALPHA surface, drawn in 12 layers then rotated and blitted. Alliance-tinted (blue in 1v1, neutral in solo). Cache key includes alliance. |
| `draw_robot2()` | `drawing_1v1.py` | **P2 robot** — identical renderer to `draw_robot()` but draws `state.robot2`. Alliance = red in 1v1. |
| `draw_hud()` | `drawing.py` | Routes to `_draw_hud_solo()` (solo) or `_draw_hud_1v1()` (1v1) based on `state.game_mode`. |
| `_draw_hud_solo()` | `drawing.py` | Solo-only HUD: dark panel on right side, team branding header, phase label, STOPPED/PAUSED badge, countdown timer (muted gray when paused), motif circles, launch zone indicator (✓/✗), intake status (ON/OFF/COOLDOWN) with color-interpolated heat bar (green→yellow→orange→red) and cooldown timer, score breakdown, 9-slot ramp display, gate state, parking status 3-segment bar with status label |
| `_draw_hud_1v1()` | `drawing.py` | Split HUD for 1v1: shared gate display (once, between P1/P2 sections), then two vertically stacked panels using `_draw_player_hud_section` helper. P1 panel (BLUE) drawn first, P2 panel (RED) continues directly below. Winner indicator at match end. |
| `_draw_player_hud_section()` | `drawing.py` | Shared helper for compact single-player HUD section. Signature: `(screen, team, robot, park_status, intake_active, intake_heat, intake_overheated, intake_cooldown_timer, state, y, accent_color, in_zone=False)`. Renders: zone indicator, intake status, heat bar, score, ramp, parking. Returns final `y` for stacking. |
| `draw_match_end()` | `drawing.py` | Cached semi-transparent overlay with "MATCH OVER", team branding, final score. In solo: single score breakdown. In 1v1: side-by-side scores, winner label ("P1 WINS" / "P2 WINS" / "TIE"), each player's breakdown, interactive Restart/Exit buttons. |
| `draw_match_end_buttons()` | `drawing.py` | Renders highlight on top of already-blitted match-end overlay buttons. |
| `draw_pause_menu()` | `drawing.py` | Semi-transparent overlay with centered panel containing selectable buttons: Resume, Restart Game, Detect Gamepads, Options (hidden in 1v1), Mode Select, Quit. In 1v1 mode, only 5 buttons are shown (Options omitted). Highlighted button shown with lavender border (ZENITH_ACCENT). Navigation hint at bottom. Subtle ZENITH watermark at panel bottom. |
| `draw_options_screen()` | `drawing.py` | Full-screen overlay for keybind customization (P1 only). Two tabs (KEYBOARD / GAMEPAD). Each tab lists all bindable actions with current binding and highlight for selected row. Supports rebinding pulse animation, duplicate binding warnings, locked binding indicators, and Reset to Default row. **Hidden in 1v1 mode**. |

---

### `game_logic.py` — Update Functions (Shared Only)

**Module-level infrastructure:**
- `_physics_lock` — `threading.Lock` protecting shared state between main and physics threads
- `_physics_running` — flag controlling the background physics loop
- `_physics_thread` — reference to the daemon physics thread
- `_cached_obs_rect` — cached merged goal+depot obstacle rect, rebuilt only on game reset via `rebuild_obstacle_cache(state)`

**Re-imports from `game_logic_p2`** (P2 functions re-exported for backward compatibility):
```python
from game_logic_p2 import (
    update_park_status2,
    constrain_robot_r,
    constrain_robot_robot,
    update_intake_heat_p2,
    score_pattern2,
    score_base2,
    update_turret_angle_r,
)
```
- `rebuild_obstacle_cache(state)` calls `game_logic_p2._set_obs_rect(rect)` to sync the obstacle cache across both modules.

**Core update functions:**

| Function | Location | Responsibility |
|---|---|---|
| `update_timer(state, dt)` | `game_logic.py` | Decrements timer only if `timer_running`; at 20s switches to `ENDGAME`; at 0s triggers scoring (P1 + P2 separately in 1v1), sets `FINISHED`, sets `timer_running = False`, and clears both robots' velocity |
| `score_pattern(state)` | `game_logic.py` | Each ramp slot matching `motif[i % 3]` → +2 points (P1's ramp) |
| `score_pattern2(state)` | `game_logic_p2.py` | Same as `score_pattern` but for P2's ramp and motif |
| `score_base(state)` | `game_logic.py` | Robot fully inside base → 10 pts, partial → 5 pts (P1). Computes robot rect and checks `base_rect().contains()` / `colliderect()` directly. |
| `score_base2(state)` | `game_logic_p2.py` | Robot fully inside P2's base → 10 pts, partial → 5 pts (P2, 1v1 only). Reads pre-computed `state.park_status2` (does NOT check robot position directly). |
| `update_artifact_physics(state, dt)` | `game_logic.py` | 2D physics with early-exit optimization: velocity integration, exponential friction, field-wall bounce with restitution, goal+depot merged-obstacle containment push-out + bounce, artifact–artifact collision resolution, robot–artifact push with restitution + extra push force. Uses cached obstacle rect and local variable aliases for performance. |
| `constrain_robot(state)` | `game_logic.py` | Pushes P1 robot out of cached obstacle rect (iterative resolve, capped at `_CONSTRAIN_MAX_ITER = 8` iterations) |
| `constrain_robot_r(state, robot)` | `game_logic_p2.py` | Pushes any robot (P1 or P2) out of cached obstacle rect. Used for P2 in 1v1 mode. |
| `constrain_robot_robot(state)` | `game_logic_p2.py` | Pushes both robots apart if their 60×60 rects overlap (1v1 only). Symmetric half-push on smallest overlap axis, clamped to field. |
| `update_turret_angle(state)` | `game_logic.py` | Snaps P1 turret angle to point at goal. **Runs on the main thread every frame** (not in physics thread). |
| `update_turret_angle_r(state, robot)` | `game_logic_p2.py` | Snaps any robot's turret angle to point at goal. Used for P2 in 1v1 mode. Runs on main thread. |
| `update_intake_heat(state, dt)` | `game_logic.py` | P1 intake motor heat management. When intake is ON, heat increases at `dt / intake_heat_time`. At 1.0 → overheat: auto-shutoff, cooldown starts, intake blocked. When overheated, heat visually drains at `dt / intake_cooldown_time` synced with cooldown timer. When intake OFF and heat < 1.0, heat decreases at `dt / intake_cool_time`. |
| `update_intake_heat_p2(state, dt)` | `game_logic_p2.py` | P2 intake motor heat management — identical logic to `update_intake_heat` but uses `intake_heat2`, `intake_active2`, `intake_overheated2`, `intake_cooldown_timer2`. |
| `_update_flying_and_gate(state, dt)` | `game_logic.py` | Moves flying artifacts toward goal, routes scoring to correct `TeamState` based on `artifact.team` field (`"p1"` → `state.team`, `"p2"` → `state.team2`), checks launch zone for correct player, updates gate auto-close timer. Runs under `_physics_lock`. |
| `update_physics(state, dt)` | `game_logic.py` | Runs one frame of physics simulation under `_physics_lock`: park status (P1 + P2) always updated; robot constraint (P1 + P2), intake heat (P1 + P2), artifact physics, flying artifacts, and gate timer only run when `timer_running` is `True`. Does NOT update turret angle. |
| `get_park_status(state)` | `game_logic.py` | Returns `"NONE"`, `"PARTIAL"`, or `"FULL"` based on P1 robot rect vs P1 base rect containment |
| `update_park_status(state)` | `game_logic.py` | Writes `get_park_status()` result to `state.park_status` |
| `update_park_status2(state)` | `game_logic_p2.py` | Writes P2 park status to `state.park_status2` using P2 robot vs P2 base rect |

**Intake overheating system:**
- Heat bar on HUD fills from 0→100% over `intake_heat_time` seconds when intake is ON
- Color gradient: green (0–50%) → yellow (50–80%) → orange (80–95%) → red (95–100%)
- At 100%: intake auto-shutoffs, 10-second cooldown begins, bar visually drains alongside countdown timer text
- Partial cool: if intake key/button released before 100%, bar drains over `intake_cool_time` seconds and intake can be re-enabled anytime
- Heat fully reset on pause, match end, or game reset
- P2 has independent intake heat system via `update_intake_heat_p2()`

**Turret tracking:**
- Each frame, the target angle is computed as `atan2(gx, -gy)` from robot to goal center
- Shortest-path wrap-around: `diff = (target - current + π) % (2π) - π` prevents the 360° spin when crossing the goal's vertical centerline
- Snaps instantly to target (no smoothing factor) — turret always points at the goal
- **Runs on the main thread** so turret always tracks in real time regardless of physics thread timing
- P2 uses `update_turret_angle_r(state, robot)` which tracks the same goal rect

**Physics thread:**
- `_physics_thread_target(state)` — background loop running at 60 Hz, calls `update_physics(state, dt)` under `_physics_lock`
- `start_physics_thread(state)` — spawns daemon thread, returns it
- `stop_physics_thread()` — signals thread to stop, joins with 2s timeout
- Uses its own `pygame.time.Clock()` for independent dt calculation

**Cached obstacle rect:**
- `_cached_obs_rect` — module-level `pygame.Rect` storing the merged goal+depot obstacle
- `rebuild_obstacle_cache(state)` — recomputes from `state.goal_rect()` and `state.depot_rect()`; called once in `GameState._setup()`
- `_get_obs_rect()` — returns cached rect (with zero-size fallback if cache not yet built)

**Scoring rules:**
| Event | Points | Notes |
|---|---|---|
| Artifact classified on ramp | +3 | Only if in launch zone (P1's zones for P1, P2's zones for P2) |
| Overflow / Depot | +1 each | Only if in correct launch zone |
| Pattern match (per matching slot) | +2 | Evaluated at match end |
| Full base return | +10 | Robot entirely inside its base rect at match end |
| Partial base return | +5 | Robot partially in its base rect at match end |

**Physics details:**
- Exponential friction: `v *= friction^dt` where `friction = 0.08` → near-instant stops
- Field walls: restitution `0.45`, push out and reverse velocity component
- Goal+depot obstacle: single merged rect (cached), artifacts pushed to nearest edge with bounce `0.45`; outside-edge collision via clamp-based normal push
- Artifact–artifact: overlap separation `0.5` each, impulse with restitution `0.50`; **both-stationary early-exit**: skips pair entirely if both artifacts have zero velocity
- Robot–artifact: overlap pushes artifact, impulse with restitution `0.90`; extra `push_force = 600` applied as velocity bias when speed is low
- Robot–robot: AABB overlap on 60×60 rects, symmetric half-push on smallest overlap axis, iterative resolve (max 8), clamped to field bounds (1v1 only)
- **Early-exit optimization**: Stationary artifacts (`vx == 0, vy == 0`) that are far from the robot (beyond `rob_r + R + 20` px) are skipped entirely
- **Local variable aliases**: All CONFIG dict lookups hoisted to locals; robot position/velocity cached outside loops to avoid repeated attribute access

---

### `input_handler.py` — Controls (P1 and Shared Only)

Processes all Pygame events once per frame. Supports keyboard and gamepad simultaneously. Joystick objects cached at module level via `init_joysticks()` for reliable reconnection.

**Internal helper functions:**
| Function | Purpose |
|---|---|
| `_key_held(state, action, keys)` | Check if a keyboard action's key is currently held |
| `_key_pressed(action, events, state)` | Check if a keyboard action's key was pressed this frame |
| `_gamepad_button(action, events, state, jid)` | Check if a gamepad action's button was pressed this frame |
| `_gamepad_axis(action, joy, state)` | Check if a gamepad action's axis is active (>0.5) |
| `_gamepad_button_held(action, joy, state)` | Check if a gamepad action's button is currently held |
| `_handle_field_drive(r, keys, dt, state)` | Process WASD movement in field-oriented mode |
| `_handle_robot_drive(r, keys, dt, state)` | Process WASD movement in robot-oriented mode |
| `_launch_held(state, r, team=None)` | Launch all held artifacts toward the goal. Optional `team` arg for P2 launching. |
| `_toggle_gate(state, r, override_range=None)` | Toggle gate open if robot is within gate_range. Optional `override_range` parameter used by AI to specify custom interaction range. Acquires `_physics_lock` internally to serialize with physics thread. |
| `_try_pickup(state, r, in_front)` | Attempt to pick up nearest artifact in front cone |
| `_handle_gamepad(state, r, joy, events, dt, in_front)` | Process gamepad stick, trigger, and button input |
| `_execute_pause_action(state, index)` | Execute selected pause menu action (Resume/Restart Game/Detect Gamepads/Options/Mode Select/Quit). In 1v1 mode, indices ≥ 3 are remapped (+1) to skip the hidden Options button. |

**Return value:**
- `handle_input(state, dt, events=None)` returns `True` if a reset was requested (F5 / gamepad Back); `None` otherwise. The caller performs the actual reset under the physics lock. Accepts optional `events` list (mode files collect events once per frame and pass them in to avoid double-collection).

**Public aliases for AI / mode files:**
- `launch_held` = `_launch_held`
- `toggle_gate` = `_toggle_gate`

**Joystick initialization:**
- `init_joysticks(rescan=False)` — initializes all connected gamepads. If `rescan=True`, reinitializes the joystick subsystem for hot-plug support.

**P1 device helpers:**
- `_resolve_p1_joystick(state)` — returns the pygame Joystick object for P1 if on gamepad, else `None`.
- `_resolve_solo_gamepads()` — returns list of ALL connected joysticks (for solo mode dual-input).
- `_is_p1_event(event, state)` — returns `True` if `event` originated from P1's assigned device.

**Pause menu navigation:**
- When paused (and match not finished), keyboard Up/Down (or Numpad 8/2) navigate the pause menu
- Enter/Space selects the highlighted action
- Navigation uses cooldowns (`_MENU_NAV_DELAY_MS = 200`) to prevent rapid-fire

**Timer controls** (admin — always keyboard):
| Key | Action |
|---|---|
| `F5` | Reset game (timer stops) |
| `F6` | Start timer (only works when stopped) |
| `ESC` | Pause / Resume toggle (or close Options screen if open) |
| `F10` | Quit |

- **Solo mode**: Both keyboard AND gamepad work simultaneously, regardless of which device P1 picked in the menu. All connected gamepads are scanned for input.

**Robot** has a facing direction (`angle`, 0 = up). Default `drive_mode = "field"`:
- In field mode: W/S/A/D move in world axes regardless of facing
- In robot mode: W = forward (nose direction), S = backward, A/D strafe left/right perpendicular to facing
- Left/Right arrows rotate in place
- Pickup only works for artifacts in the front cone (120°)

**Keyboard P1:**
| Key | Action |
|---|---|
| `W` | Move forward (facing direction in robot mode, world-up in field mode) |
| `S` | Move backward (facing direction in robot mode, world-down in field mode) |
| `A` | Strafe left (robot mode) / World left (field mode) |
| `D` | Strafe right (robot mode) / World right (field mode) |
| `←` | Rotate left |
| `→` | Rotate right |
| `E` | Hold to intake (continuously picks up artifacts in front cone while held; blocked when overheated) |
| `Q` | Launch ALL held artifacts toward goal (any number) |
| `T` | Toggle gate open (must be within gate_range of gate) |
| `R` | Toggle drive mode (`robot` ↔ `field`) |

**Keyboard P2 (default bindings, rebindable via Options in solo, fixed in 1v1):**
| Key | Action |
|---|---|
| `I` | Move forward |
| `K` | Move backward |
| `J` | Strafe left |
| `L` | Strafe right |
| `U` | Rotate left |
| `O` | Rotate right |
| `P` | Toggle intake |
| `;` | Launch artifacts |
| `.` | Toggle gate |
| `M` | Toggle drive mode |

**Gamepad P1** (first joystick):
| Input | Action |
|---|---|
| Left stick | Move (field-oriented or robot-oriented based on drive mode) |
| Right stick X | Rotate |
| Left trigger (axis 4) | Launch ALL held artifacts (any number) |
| Right trigger (axis 5) | Hold to intake (continuously picks up artifacts in front cone while held; blocked when overheated) |
| X (2) | Toggle gate open (must be within gate_range of gate) |
| Y (3) | Pause / Resume toggle |
| Left Bumper (4) | Toggle drive mode (robot ↔ field) |
| Back / Select (6) | Reset game |

**Drive modes:**
- `"robot"`: W = forward (nose direction), S = backward, A/D = strafe, Left/Right = rotate
- `"field"`: W = world-up, S = world-down, A/D = world-left/right, Left/Right = rotate
- Gamepad: left stick moves in world axes in field mode, relative to robot heading in robot mode
- Badge at field top-left shows current mode
- Toggle with `R` (keyboard) or `Left Bumper` (gamepad)
- **Default on startup: `"field"`**

**Gate behavior:**
- Press `T` (keyboard) or `X` (gamepad) within `gate_range` of the gate to open it
- Gate toggle acquires `_physics_lock` to safely clear the ramp and scatter artifacts without racing the physics thread
- All ramp artifacts + overflow_held teleport to random spike-mark or loading-zone positions with small random velocity
- Gate auto-closes after `gate_open_duration` seconds

**Launch behavior:**
- `Q`/left trigger works with any number of held artifacts
- Launches all held as individual projectiles with random ±6px offset for visual separation
- Each projectile independently reaches the goal and enters the ramp visually
- Points (classified + overflow/depot) only count if robot was in launch zone (top triangle **OR** base/parking zone **OR** shooting zone triangle)
- Outside all three zones = artifact fills ramp visually but awards absolutely 0 points
- In 1v1, each player's launch uses their own `in_launch_zone` / `in_launch_zone2` check

**Intake overheating behavior:**
- `E` (keyboard) holds to intake (intake active while held, deactivates on release); **blocked when `intake_overheated` is True**
- Right trigger (gamepad) holds to intake (intake active while held, deactivates on release); **blocked when `intake_overheated` is True**
- When intake is ON, `intake_heat` increases each frame; HUD shows a color-interpolated bar (green→yellow→orange→red)
- At 100% heat: intake auto-shutoffs, 10-second cooldown begins, bar visually drains alongside countdown timer text
- Partial cool: if intake key/button released before 100%, bar drains over `intake_cool_time` seconds and intake can be re-enabled anytime
- Heat fully reset on pause, match end, or game reset
- P2 has independent intake heat system

**Parking status:**
- Live-updated every frame in `update_park_status()` (P1) and `update_park_status2()` (P2)
- `NONE` — robot has zero overlap with its base rect
- `PARTIAL` — robot overlaps but is not fully inside → +5 pts at match end
- `FULL` — robot entirely inside its base rect → +10 pts at match end
- HUD shows 3-segment indicator bar with status label (per-player in 1v1)
- Field shows pulsing gold border (PARTIAL) or green glow fill (FULL) on each player's base

**Pause behavior:**
- When `timer_running` is `False`, all robot input is frozen (no movement, pickup, launch, gate)
- `intake_active` and `intake_active2` are reset to `False` when timer stops or match ends
- All intake heat fields (P1 + P2) are reset to zero on pause/finish
- Timer digits shown in muted gray; STOPPED or PAUSED badge displayed on HUD
- Physics simulation also frozen (artifacts stop moving)
- A pause menu overlay appears with selectable buttons (Resume, Restart Game, Detect Gamepads, Options, Mode Select, Quit). In 1v1 mode, only 5 buttons are shown (Options omitted).
- **Mode Select** returns to the mode-select screen (physics thread stops, game state discarded)
- **Quit** exits the application
- Navigation via keyboard arrows; selection via Enter/Space
- **Mode Select** sets `state.pending_return = "menu"`; mode files check this at the top of each frame loop and return to the mode-select screen
- In 1v1 mode, the pause menu index is remapped (indices ≥ 3 incremented by 1) to skip the hidden Options button

---

### `game_logic_p2.py` — P2 Physics (Multi-Player Only)

**Module-level infrastructure:**
- Duplicates `_get_obs_rect()` and `_set_obs_rect()` from `game_logic.py` to avoid forbidden cross-import
- `_cached_obs_rect` — local copy of the merged goal+depot obstacle rect, synced from `game_logic.rebuild_obstacle_cache()` via `_set_obs_rect()`
- `_CONSTRAIN_MAX_ITER = 8` — same as `game_logic.py`

**Functions:**
| Function | Responsibility |
|---|---|
| `_set_obs_rect(rect)` | Update the cached obstacle rect. Called by `game_logic.rebuild_obstacle_cache`. |
| `_get_obs_rect()` | Return the cached obstacle rect, falling back to zero-size if unset. |
| `constrain_robot_r(state, robot)` | Pushes any robot (P1 or P2) out of cached obstacle rect. Used for P2 in 1v1 mode. |
| `constrain_robot_robot(state)` | Pushes both robots apart if their 60×60 rects overlap (1v1 only). Symmetric half-push on smallest overlap axis, clamped to field. |
| `update_intake_heat_p2(state, dt)` | P2 intake motor heat management — identical logic to `update_intake_heat` but uses P2 fields. |
| `score_pattern2(state)` | Each ramp slot matching `motif[i % 3]` → +2 points (P2's ramp) |
| `score_base2(state)` | Robot fully inside P2's base → 10 pts, partial → 5 pts (P2, 1v1 only) |
| `update_park_status2(state)` | Writes P2 park status to `state.park_status2` using P2 robot vs P2 base rect |
| `update_turret_angle_r(state, robot)` | Snaps any robot's turret angle to point at goal. Used for P2 in 1v1 mode. Runs on main thread. |

**Dependencies:** Only imports from `config` and `pygame`. Does NOT import from `game_logic`.

---

### `drawing_1v1.py` — 1v1 Rendering (Multi-Player Only)

**Functions:**
| Function | Responsibility |
|---|---|
| `draw_robot2(screen, state)` | P2 robot renderer — identical to `draw_robot()` but draws `state.robot2`. Alliance = red in 1v1. Uses `_build_robot_surface(r)` from `drawing.py`. Uses shared robot cache. |
| `draw_field_1v1_extras(screen, state)` | 1v1-only field elements: P2's base rect (2px ALLIANCE_RED outline + fill + park pulse/glow), mirrored loading zone (SOFT_WHITE outline/text, matching P1). |

**Font access:** Uses `import drawing as _d` then `_d.f_small`, `_d.f_tiny` etc. (fonts are `drawing.py` module-level globals, not in `config.py`).

**Dependencies:** Imports from `config`, `drawing` (for font globals and cache references).

---

### `input_handler_p2.py` — P2 Input (Multi-Player Only)

**Functions:**
| Function | Responsibility |
|---|---|
| `handle_input_p2(state, dt, events=None)` | Processes input for Player 2 in 1v1 mode using `state.robot2`, `state.team2`, `state.keybinds_p2`, and `state.p2_device`. |
| `_handle_p2_keyboard(state, r, keys, events, dt)` | P2 keyboard input using `state.keybinds_p2["keyboard"]` |
| `_handle_p2_field_drive(r, key_held_fn, dt)` | P2 WASD movement in field-oriented mode |
| `_handle_p2_robot_drive(r, key_held_fn, dt)` | P2 WASD movement in robot-oriented mode |
| `_handle_p2_gamepad(state, r, joy, events, dt)` | P2 gamepad input using `state.keybinds_p2["gamepad"]` |

**Key behaviors:**
- Frozen when paused or options open — P2 robot stops moving, intake deactivates
- P2 intake uses `state.intake_active2` / `state.intake_heat2` / `state.intake_overheated2`
- P2 launches with `_launch_held(state, r, state.team2)` from `input_handler`
- P2 can pause/unpause via keyboard ESC or gamepad Y button

**Dependencies:** Imports from `config`, `pygame`, and `input_handler` (for `_launch_held`, `_toggle_gate`, `_try_pickup`, `_joysticks`, `_trigger_cooldown`).

---

### `ai_controller.py` — AI Logic (1v1 Only, for AI-controlled P2)

**Difficulty profiles** (`DIFFICULTIES` dict):
| Parameter | Easy | Medium | Hard | Purpose |
|---|---|---|---|---|
| `speed_mult` | 0.50 | 0.85 | 1.00 | Robot movement speed multiplier |
| `aim_error` | 15.0° | 2.0° | 0.0° | Random turret aim offset (degrees) |
| `radius` | 200 | 350 | 500 | Artifact search radius (px) |
| `reaction` | 0.40s | 0.08s | 0.00s | FSM state transition delay |
| `parks` | False | True | True | Whether AI parks at endgame |
| `launch_hold_threshold` | 3 | 3 | 3 | Artifacts held before navigating to launch |
| `gate_range` | 100 | 100 | 100 | Distance to interact with gate |
| `safe_corridor` | 80 | 80 | 80 | Safety margin for obstacle routing |

**Module-level state:**
- `_ai_state` — current FSM state: `"COLLECT"`, `"NAVIGATE"`, `"LAUNCH"`, `"PARK"`, or `"GATE"`
- `_reaction_timer` — countdown for FSM state transition delay
- `_difficulty` — active difficulty key (`"easy"`, `"medium"`, `"hard"`)
- `_aim_offset` — random turret aim error (radians), refreshed every 0.5–1.5s
- `_aim_refresh_timer` — countdown to next aim offset refresh

**Unstuck system:**
- `_pos_history` — recent robot positions (capped at 90 entries)
- `_stuck` — whether robot is currently stuck
- `_stuck_dir_idx` / `_stuck_dir_timer` — which direction to try and for how long
- `_STUCK_THRESHOLD = 0.8s` — time window to detect no movement
- `_STUCK_MOVE_MIN = 10.0` — minimum distance to consider "moved"
- `_STUCK_DIR_DUR = 0.3s` — duration to try each escape direction
- `_STUCK_DIRS` — 8 directions (cardinal + diagonal) to try when stuck
- When stuck: robot cycles through escape directions, avoiding the obstacle rect

**Obstacle routing:**
- `_routing_side` / `_routing_side_lock` — tracks which side of the obstacle to route around
- `_CORNER_HYSTERESIS = 30.0` / `_CORNER_EXTRA = 25.0` — corner routing parameters
- `_move_toward()` handles obstacle avoidance: detects if the path crosses the expanded obstacle rect, routes under it via safe corridor

**FSM states:**
| State | Behavior |
|---|---|
| `COLLECT` | Drive toward nearest artifact (within radius), intake on. If holding ≥ threshold → NAVIGATE. If no artifacts and holding ≥ 1 → NAVIGATE. If ramp has items and gate closed → GATE. |
| `NAVIGATE` | Drive toward nearest launch point (base zone, launch zone triangle, or shooting zone). On arrival → LAUNCH. |
| `LAUNCH` | If in launch zone and holding artifacts → launch all held. If not in launch zone → NAVIGATE. |
| `PARK` | Drive toward P2's base zone. If holding artifacts and in launch zone → launch first. If fully parked → stop. Forced in last 5 seconds. |
| `GATE` | Approach gate from the right side of the obstacle. When in range → toggle gate → COLLECT. |

**Endgame override:** In the last 5 seconds, AI forces `PARK` state regardless of current state.

**Public API:**
| Function | Signature | Behavior |
|---|---|---|
| `set_difficulty(difficulty)` | `(str)` | Set AI difficulty. Invalid values default to `"medium"`. Resets all AI state. |
| `reset_ai()` | `()` | Reset all AI module state (called by `GameState.reset()`). |
| `update_ai(state, dt)` | `(GameState, float)` | Main AI update. Drives `state.robot2` based on active FSM state and difficulty profile. |

**Helper functions:**
| Function | Responsibility |
|---|---|
| `_state_collect(state, r, dt, profile)` | COLLECT state logic |
| `_state_navigate(state, r, dt, profile)` | NAVIGATE state logic |
| `_state_launch(state, r, dt, profile)` | LAUNCH state logic |
| `_state_park(state, r, dt, profile)` | PARK state logic |
| `_state_gate(state, r, dt, profile)` | GATE state logic |
| `_stop_robot(r)` | Zero out robot velocity |
| `_move_toward(r, tx, ty, speed, dt, obs_rect, profile)` | Move toward target with obstacle avoidance |
| `_rotate_toward(r, tx, ty, dt)` | Rotate robot toward target angle (with aim offset) |
| `_in_front_cone(r, tx, ty)` | Check if target is within pickup cone |
| `_line_crosses_rect(x1, y1, x2, y2, rect)` | Check if line segment intersects rectangle |
| `_nearest_launch_point(state, r)` | Find closest valid launch position |
| `_point_in_triangle(pt, v1, v2, v3)` | Point-in-triangle test |
| `_clamp_to_rect(px, py, rect)` | Clamp point to rectangle bounds |

**Dependencies:** Imports from `config` (clamp), `input_handler` (_launch_held, _toggle_gate, _try_pickup).

**Note:** AI does NOT pause, reset, or open options. AI intake uses `state.intake_active2` / `state.intake_heat2` / `state.intake_overheated2`.

**Current status:** AI IS wired into `mode_1v1.py`. When `p2_device == "ai"`, `handle_input_p2` is skipped and `update_ai()` is called instead. vs AI mode is functional.

---

## Game Flow

### Solo Mode
1. Game starts in **MODE SELECT** — user picks Solo Practice
2. Match starts in **TELEOP** phase with 120 seconds on the clock, timer **STOPPED**, drive mode **FIELD**
3. **Dual-input mode**: Both keyboard AND gamepad work simultaneously, regardless of which device P1 picked in the menu. All connected gamepads are scanned — drive with WASD, pause with gamepad Y, launch with Q or LT, etc. Gamepad stick overrides keyboard drive when active.
4. Press **F6** (keyboard) to begin the timer
5. **ESC** (keyboard) / **Y** (gamepad) pauses and resumes mid-match
6. At **20 seconds remaining**, phase switches to **ENDGAME** (orange flashing text)
7. At **0 seconds**, pattern scoring + base scoring are calculated atomically (under lock), `timer_running` is set to `False`, and robot velocity is cleared
8. Phase becomes **FINISHED** — robot freezes, all scoring stops, overlay appears with score
9. Press **Restart** (Enter) to reset, **Exit** (Esc) to quit. Navigate between buttons with **Left/Right** arrows.
10. Window is **resizable** — content scales to fit while preserving aspect ratio

### 1v1 Mode
1. Game starts in **MODE SELECT** — user picks 1v1 Local
2. **Controller-assign screen**: Defaults are set automatically based on detected gamepads (2+ gamepads → P1=Gamepad 1, P2=Gamepad 2; 1 gamepad → P1=Gamepad 1, P2=AI). User can change selections. P1 picks Gamepad 1 or Gamepad 2. P2 picks Gamepad 1, Gamepad 2, or AI.
3. Match starts in **TELEOP** phase with 120 seconds on the clock, timer **STOPPED**
4. Both robots appear on the field: P1 (blue alliance) at left-center facing right, P2 (red alliance) at right-center facing left
5. 36 artifacts total: 18 base + 18 mirrored on P2's half of the field
6. Both players share the same timer, phase transitions, and physics simulation
7. Each player has independent: intake, heat, ramp, scoring, and park status
8. Flying artifacts are tagged with `team` field (`"p1"` or `"p2"`) so scoring routes to the correct player
9. If P2 is assigned AI, AI controller IS now active (vs AI now functional)
10. At match end: both scores shown side-by-side, winner announced ("P1 WINS" / "P2 WINS" / "TIE")
11. **Restart** button resets the match (preserves `game_mode`, device assignments); **Exit** quits

### Controller-Assign Flow
1. When entering the controller-assign screen, **defaults are set automatically** based on detected gamepads:
   - 2+ gamepads detected → P1 = Gamepad 1 (`"gamepad0"`), P2 = Gamepad 2 (`"gamepad1"`)
   - 1 gamepad detected → P1 = Gamepad 1 (`"gamepad0"`), P2 = AI (`"ai"`)
   - 0 gamepads detected → P1 = Gamepad 1 (not found), P2 = AI (`"ai"`)
2. P1 can change to: Gamepad 1 or Gamepad 2
3. P2 can change to: Gamepad 1, Gamepad 2, or AI
4. Conflict check:
   - If P1 = gamepad and P2 = gamepad and same joystick ID → **blocked** (show warning)
   - Otherwise → accepted, both devices stored
5. Device format: plain strings — `"gamepad0"`, `"gamepad1"`, or `"ai"` for AI

---

## Threading Architecture

```
Main Thread                          Physics Thread (daemon)
─────────────                        ──────────────────────
menu loop (mode select,              _physics_thread_target loop:
  controller assign)                      acquire _physics_lock
Dispatcher:                               update_park_status()
  mode_solo.run_solo()                    update_park_status2()     [1v1]
    or mode_1v1.run_1v1()                 constrain_robot()
  (each mode owns its own                 constrain_robot_r()      [1v1]
   frame loop and physics thread)         constrain_robot_robot()  [1v1]
                                          update_intake_heat()
  Mode frame loop:                        update_intake_heat_p2()  [1v1]
    handle_input()                        update_artifact_physics()
    handle_input_p2()  [1v1]              _update_flying_and_gate()
    update_turret_angle()            release _physics_lock
    update_turret_angle_r() [1v1]
    acquire _physics_lock
      update_timer()
      draw_*()
    release _physics_lock
    smoothscale + display.flip()
    clock.tick_busy_loop(144)
```

- `_physics_lock` protects all shared `GameState` mutations
- `update_timer()` runs under the lock so `score_pattern()`/`score_pattern2()`/`score_base()`/`score_base2()` are atomic with respect to `_update_flying_and_gate()` — no race between scoring and the last flying artifacts arriving
- When the match ends, `timer_running` is set to `False` and both robots' velocity is cleared, stopping all physics updates and preventing phantom artifact pushes
- Turret angle updates run on main thread outside the lock (simple float reads/writes are GIL-atomic)
- Reset acquires the lock to prevent physics thread from accessing state mid-reset
- Gate toggle acquires the lock internally to safely clear the ramp without racing the physics thread
- Physics thread runs at 60 Hz independently of the main thread's 144 Hz render rate
- P2 input runs on main thread in the same frame as P1 input (sequential, no lock needed)

---

## Key Design Decisions

- **File ownership rule (enforced from refactoring onward)**: Strict separation of solo-only and multi-player-only code. `game_logic_p2.py`, `drawing_1v1.py`, and `input_handler_p2.py` are NEVER edited for solo work. `ai_controller.py` is only used by `mode_1v1.py` when P2 is assigned AI. Shared files (`game_logic.py`, `drawing.py`, `input_handler.py`) contain only P1/shared code with no P2 function bodies.
- **`FlyingArtifact.team` field**: Each launched artifact carries a `team` tag (`"p1"` or `"p2"`) so scoring routes to the correct `TeamState` without needing separate flying lists per player
- **`GameState.reset()` preserves 1v1 state**: Saves `game_mode`, `p1_device`, `p2_device` across `_setup()` call so returning from pause menu to mode select and re-selecting 1v1 retains device assignments
- **Font access pattern in `menu.py` and `drawing_1v1.py`**: Uses `import drawing as _drawing` then `_drawing.f_huge.render(...)` instead of `from drawing import f_huge` because font globals are `None` until `init_drawing()` runs, and module-level imports capture the `None` at import time
- **Alliance-tinted rendering**: Robot LED, rollers, and fill are tinted per alliance (red/blue) in `_build_robot_surface()`. Cache key includes alliance so P1 and P2 robots have separate cache entries.
- **Mirror layout**: 1v1 loading zone (top-right) is mirrored from P1's loading zone (top-left). P2's base is at right-center of field, P1's at left-center. Spike marks are mirrored horizontally (P1 left-of-center, P2 right-of-center). Alliance area artifacts are mirrored to the right side for P2.
- **Interactive match-end buttons**: In 1v1, both scores shown side-by-side with winner announcement. Restart/Exit buttons navigable via keyboard arrows.
- **One-way dependency**: MP-only files (`game_logic_p2`, `drawing_1v1`, `input_handler_p2`, `ai_controller`) may import from shared files, but shared files never import from MP-only files. `game_logic_p2.py` does NOT import from `game_logic.py` — obstacle cache is synced via `_set_obs_rect()` setter.
- **No `mode_vs_ai.py`**: AI-controlled P2 runs through `mode_1v1.py` with `p2_device == "ai"` — AI update happens in the 1v1 frame loop (not in `handle_input_p2`). **✅ Now wired** — `update_ai()` IS called from `mode_1v1.py`, so vs AI mode is now functional.
