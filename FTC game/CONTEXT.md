# FTC DECODE Match Simulator — Project Context

A single-robot, single-team 2D match simulator for the FIRST Tech Challenge 2025–2026 game "DECODE," built with **Python 3 + Pygame**.

---

## Project Structure

```
FTC game/
├── main.py              # Entry point, window creation, game loop, physics thread lifecycle
├── config.py            # Colors, CONFIG dict, layout constants, math helpers
├── game_state.py        # Data classes: Artifact, FlyingArtifact, Robot, TeamState, GameState
├── drawing.py           # Rendering: field, artifacts, robot, HUD, match-end overlay (with caching)
├── game_logic.py        # Timer, scoring, 2D artifact physics, flying updates, robot constraints, park status, intake heat, physics thread
├── input_handler.py     # Keyboard and gamepad input, pause/start/reset controls
├── keybinds.json        # Saved custom keybinds (created on first rebinding, loaded on startup)
├── CONTROLS.md          # User-facing controls guide (Romanian)
└── CONTEXT.md           # This file
```

No external dependencies beyond Python stdlib and `pygame`.

---

## Module Breakdown

### `main.py` — Entry Point

- Initializes Pygame, creates a **resizable window** (`pygame.RESIZABLE`) titled `"FTC DECODE — Robot simulator by TEAM ZENITH 19084"`
- Creates a fixed-size **virtual canvas** (`1050 × 778`) that all drawing targets
- Each frame: input → turret update → (under lock) timer → render → smoothscale to window (aspect-ratio-preserving with black letterbox bars)
- Uses `clock.tick_busy_loop(fps)` for precise frame pacing
- Calls `init_drawing()` after `pygame.init()` to initialize fonts (must happen after pygame init)
- Detects and initializes joysticks on startup via `input_handler.init_joysticks()`
- **Physics thread**: spawns a background thread via `start_physics_thread(state)` that runs `update_physics()` at 60 Hz under `_physics_lock`
- **Thread safety**: Acquires `_physics_lock` during render to prevent physics mutations mid-draw; `update_timer()` also runs under this lock so scoring is atomic with respect to flying artifact updates; reset is also performed under lock
- **Turret tracking**: `update_turret_angle(state)` runs on the main thread every frame (outside lock) so the turret always tracks the goal in real time
- `handle_input()` returns `True` when reset is requested; main.py performs `state.reset()` under the physics lock
- Options screen (`draw_options_screen`) rendered on top when `state.options_active` is True

### `config.py` — Constants

**Color palette** (all RGB/RGBA tuples):
| Constant | Usage |
|---|---|
| `BLACK`, `WHITE`, `GRAY` | Basic colors used throughout rendering |
| `CHARCOAL`, `DARK_GRAY`, `BG_DARK` | Field background, grid lines, HUD panel |
| `LIGHT_GRAY`, `SOFT_WHITE` | Light text and highlights |
| `ROBOT_PURPLE`, `ROBOT_DARK`, `GLOW_PURPLE` | Robot fill, dark shade, and selection glow (ZENITH brand purple) |
| `ZENITH_PURPLE`, `ZENITH_ACCENT`, `ZENITH_DARK` | Team ZENITH brand colors: primary purple, lavender accent, deep dark |
| `ZENITH_LABEL`, `ZENITH_TAG` | Team display string `"ZENITH  19084"` and tagline `"Visions above ground"` |
| `GOAL_GOLD`, `GOAL_DARK` | Goal outline and fill |
| `RAMP_DARK` | Ramp background |
| `GATE_COLOR`, `GATE_OPEN_COLOR` | Gate closed/open state colors |
| `SLOT_EMPTY`, `SLOT_BORDER` | Ramp classifier slot colors |
| `PURPLE` / `GREEN` | Artifact colors (color "P" and "G") |
| `PURPLE_DIM` / `GREEN_DIM` | Dimmed artifact colors |
| `GOLD`, `ORANGE` | UI text and highlights |
| `PARK_GREEN` | Parking status indicator (full park) |
| `RED_ACCENT` | Match-end overlay (not parked) |
| `YELLOW_ACCENT`, `TEAL_ACCENT` | Available for general use |
| `HEAT_GREEN` | Intake heat bar: cool (low heat) |
| `HEAT_YELLOW` | Intake heat bar: warm (mid heat) |
| `HEAT_ORANGE` | Intake heat bar: hot (high heat) |
| `HEAT_RED` | Intake heat bar: critical / cooldown text |
| `PAUSE_OVERLAY` | Semi-transparent black overlay for pause menu background |
| `MENU_BG` | Pause menu panel background |
| `MENU_BORDER` | Pause menu panel border (ZENITH purple) |
| `MENU_HIGHLIGHT_BG` | Pause menu highlighted button background (dark purple) |
| `MENU_HIGHLIGHT_BORDER` | Pause menu highlighted button border (ZENITH_ACCENT lavender) |
| `MENU_TEXT` | Pause menu button text |
| `MENU_TITLE` | Pause menu "PAUSED" title text (ZENITH_ACCENT lavender) |
| `OPTIONS_REBIND` | Options screen rebinding pulse color (red-orange) |
| `OPTIONS_BIND` | Options screen selected binding color (green) |

**`CONFIG` dict** — All tunable magic numbers:
| Key | Value | Purpose |
|---|---|---|
| `field_size_px` | 720 | Field side length in pixels (144" at 5 px/in) |
| `fps` | 120 | Target frames per second |
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
| `spike_mark_count` | 6 | Number of spike marks |
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
| `goal_w` / `goal_h` | 130 | Goal rectangle size |
| `loading_zone_size` | 100 | Loading zone square size |
| `base_size` | 80 | Base zone square size |
| `shooting_zone_size` | 220 | Shooting zone triangle hypotenuse width (px) |
| `spike_cols` | 2 | Spike mark columns |
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
| `VW`, `VH` | 1050, 778 | Virtual canvas dimensions |
| `FX`, `FY` | 5, 5 | Field top-left corner on canvas |
| `FS` | 720 | Field size (alias for `field_size_px`) |
| `HX`, `HW` | 730, 320 | HUD panel left edge and width |

**Helpers**: `dist(a, b)`, `clamp(v, lo, hi)`, `lerp(a, b, t)`

**Backward-compatible aliases**: `W, H = VW, VH` (used by drawing.py)

**Global render state**: `scale_factor = 1.0`, `render_surf = None` (set by main.py)

**Keybind constants:**
- `GAMEPAD_NAMES` — dict mapping `("button", N)` / `("axis", N)` tuples to human-readable names (e.g., `"A"`, `"LT (axis 4)"`)
- `KEYBIND_ACTIONS_KEYBOARD` — list of 10 keyboard action names: Move Forward, Move Backward, Strafe Left, Strafe Right, Rotate Left, Rotate Right, Toggle Intake, Launch Artifacts, Toggle Gate, Drive Mode
- `KEYBIND_ACTIONS_GAMEPAD` — list of 5 gamepad action names: Launch, Intake, Gate, Pause, Drive Mode
- `DEFAULT_KEYBINDS` — dict with `"keyboard"` and `"gamepad"` sub-dicts mapping action names to binding tuples like `("key", pygame.K_w)` or `("axis", 4)`
- `LOCKED_KEYBINDS` — dict of actions that cannot be rebound: `{"keyboard": set(), "gamepad": {"Reset"}}`
- `save_keybinds(keybinds)` — writes current keybinds to `keybinds.json` in the game directory (JSON, tuples→lists). Never raises.
- `load_keybinds()` → `dict | None` — reads `keybinds.json`, converts lists→tuples. Returns `None` on any error (missing file, corrupt JSON, invalid structure). Prints a one-line note to console on fallback.

---

### `game_state.py` — Data Classes

**Module-level helpers:**
- `_sign(p1, p2, p3)` — Signed area of triangle (p1, p2, p3). Used for point-in-triangle test.
- `_point_in_triangle(pt, v1, v2, v3)` — Return True if pt is inside triangle defined by v1, v2, v3 (sign-of-cross-product method).

#### `Artifact`
- `x, y` — position on canvas
- `vx, vy` — 2D velocity for physics integration
- `color` — `"P"` (purple) or `"G"` (green)
- `on_field` — `True` if available for pickup
- `zone` — `"spike"`, `"loading"`, or `"alliance"`
- `respawn_timer` — unused (no respawning)
- `index` — position within spike zone

#### `FlyingArtifact`
- `x, y` — current position (animated toward target)
- `target_x, target_y` — goal center
- `color`, `speed`, `active`
- `trail` — list of recent positions for trail rendering (capped at `MAX_TRAIL`)
- `scoring: bool` — `True` if launched from launch zone
- `full_set: bool` — `True` if robot held 3 artifacts at launch
- `MAX_TRAIL: ClassVar[int] = 18` — max trail length (class variable, not instance field)

#### `GateClearAnim`
- `x, y`, `target_x`, `target_y` — animation start and end positions
- `color` — artifact color being cleared
- `progress: float` — animation progress (0.0 to 1.0)
- `active: bool` — whether animation is still running

#### `Robot`
- `x, y`, `speed`, `angle` (0 = up, radians)
- `turret_angle: float` — world-space radians, auto-updated toward goal each frame via shortest-path wrap-around (instant snap, no smoothing)
- `vx, vy` — velocity from input (used for physics push)
- `drive_mode` — `"robot"` or `"field"` (default: `"field"`)
- `holding` — list of `Artifact` objects being carried (max 3)
- `start_x`, `start_y` — initial position (set from constructor args in `__post_init__`)
- `can_pickup()` — returns `True` if holding < 3

#### `TeamState`
- `ramp` — `List[Optional[str]]` of length 9 (`None` = empty, `"P"`/`"G"` = occupied)
- `overflow_held: List[str]` — overflow artifacts stored in ramp (released on gate open)
- `gate_open`, `gate_timer` — gate state
- `classified`, `overflow`, `depot` — artifact counts
- `pattern_pts`, `base_pts` — end-of-match scores
- `total_score()` — `classified×3 + overflow + depot + pattern + base`
- `add_to_ramp(color)` — places in first empty slot, or appends to `overflow_held` + increments overflow/depot
- `clear_ramp()` — empties ramp + overflow_held, returns all colors

#### `GameState`
- `phase` — `"TELEOP"` → `"ENDGAME"` → `"FINISHED"`
- `timer` — seconds remaining
- `timer_running: bool` — `False` by default; timer does NOT auto-start on launch or reset
- `motif` — `["G","P","P"]`, `["P","G","P"]`, or `["P","P","G"]` (random at reset)
- `team` — `TeamState` instance
- `robot` — `Robot` instance (default drive_mode = `"field"`)
- `artifacts` — all `Artifact` instances (initial 27 + gate-spawned)
- `flying` — active `FlyingArtifact` list
- `park_status: str` — `"NONE"`, `"PARTIAL"`, or `"FULL"` (live-updated every frame)
- `intake_active: bool` — toggle state for intake; `True` = continuously picking up artifacts in range
- `intake_heat: float` — motor temperature, 0.0 (cold) to 1.0 (overheated)
- `intake_overheated: bool` — `True` during 10-second cooldown after full overheat
- `intake_cooldown_timer: float` — seconds remaining in overheat cooldown
- `gate_clears: List[GateClearAnim]` — gate-clearing animations
- `secret_tunnel: tuple` — center of field coordinates
- `scored: bool` — scoring flag
- `motif_name: str` — joined string of motif (e.g., `"GPP"`)
- `pause_menu_index: int` — selected pause menu button index (0–4)
- `options_active: bool` — whether the Options (keybind customization) screen is open
- `options_page: int` — current Options tab (0 = keyboard, 1 = gamepad)
- `options_index: int` — selected row in Options screen
- `options_rebinding: bool` — `True` when waiting for a new key/button input during rebinding
- `keybinds: dict` — current key bindings, structured as `{"keyboard": {action: ("key", K)}, "gamepad": {action: ("button"|"axis", N)}}`
- **`_setup()`** — shared init logic called by both `__init__` and `reset()`; calls `rebuild_obstacle_cache(self)` at the end
- **`reset()`** — calls `_setup()` to reinitialize all state
- **`_init_artifacts()`** — creates 27 artifacts:
  - **18 spike-mark** artifacts (2 cols × 3 rows, each row has a GPP/PGP/PPG arrangement)
  - **3 loading-zone** artifacts (PGP, no respawn)
  - **6 alliance-area** artifacts (4P+2G random)
- **`goal_rect()`**, `ramp_rect()`, `depot_rect()`, `gate_rect()`, `loading_rect()`, `base_rect()` — computed `pygame.Rect` helpers
- **`shooting_zone_triangle()`** — returns the three vertices `(top, bl, br)` of the right-angle isosceles shooting zone triangle (bottom-center of field, hypotenuse at bottom)
- **`in_launch_zone(x, y)`** — checks if point is within the triangular launch zone at top of field **OR** within the base/parking zone rectangle **OR** within the shooting zone triangle; all three zones count for scoring
- **`nearest_artifact(x, y, radius)`** — finds closest pickup-able artifact
- **`get_ramp_scatter_positions(state)`** (module-level) — returns 21 `(x, y)` positions (18 spike-mark + 3 loading zone) for gate-release teleport

---

### `drawing.py` — Rendering

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

2. **Robot render cache** — The full 96×96 SRCALPHA robot surface is cached in a dict keyed on `(angle_deg, turret_deg, held_colors)` via `_robot_cache_key(r)`. Turret angle is quantized to 2° increments (sub-pixel difference at the turret's small size) to maintain good cache hit rate while tracking the goal. FIFO eviction via `collections.deque` caps the cache at 360 entries to prevent unbounded memory growth. Surface built by `_build_robot_surface(r)`.

3. **Match-end overlay cache** — The semi-transparent "MATCH OVER" overlay is rendered once to `_end_overlay` by `_build_end_overlay(state)` when the phase transitions to FINISHED. Invalidated (set to `None`) on reset so it rebuilds on next match end.

**Drawing functions** (all take `(screen, state)`):

| Function | Draws |
|---|---|
| `draw_field()` | Static field elements from cache + dynamic per-frame: drive mode badge (ZENITH purple theme), base zone park status (fill + pulse/glow), ramp slot fill, gate open/closed state |
| `draw_artifacts()` | Field artifacts (with glow and motion ghost), flying artifacts (each as individual colored circle with alpha-blended fading trail capped at `MAX_TRAIL`) |
| `draw_robot()` | **ZENITH (FTC 19084) layered render with cache**: 96×96 SRCALPHA surface, drawn in 12 layers then rotated and blitted. Layers: drop shadow, 4 mecanum wheels with blue rollers, silver open truss frame with X-braces, purple 3D-printed infill panels, blue LED glow, green REV hub status LED, black corrugated intake hose arc, front intake rollers, turret base ring, **goal-tracking turret** (rotated independently of body via `turret_angle`, always points at goal), team labels (ZENITH_ACCENT lavender), gold forward triangle. Held artifacts are baked onto the surface before rotation so they stay glued to the robot. Cache key includes turret angle so turret tracks goal even during pure translation. |
| `draw_hud()` | Dark panel on right side: team branding header ("ZENITH 19084" + tagline), phase label, STOPPED/PAUSED badge, countdown timer (muted gray when paused), motif circles, launch zone indicator (✓/✗), intake status (ON/OFF/COOLDOWN) with color-interpolated heat bar (green→yellow→orange→red) and cooldown timer, score breakdown, 9-slot ramp display, gate state, parking status 3-segment bar with status label |
| `draw_match_end()` | Cached semi-transparent overlay with "MATCH OVER", team branding ("ZENITH 19084" + tagline), final score, breakdown with colored parking result, F5/F10 prompt |
| `draw_pause_menu()` | Semi-transparent overlay with centered panel containing 5 selectable buttons: Resume, Restart Game, Detect Gamepads, Options, Exit. Highlighted button shown with lavender border (ZENITH_ACCENT). Navigation hint at bottom. Subtle ZENITH watermark at panel bottom. Rendered when `timer_running` is False and phase is not FINISHED. |
| `draw_options_screen()` | Full-screen overlay for keybind customization. Two tabs (KEYBOARD / GAMEPAD). Each tab lists all bindable actions with current binding and highlight for selected row. Supports rebinding pulse animation, duplicate binding warnings, locked binding indicators, and Reset to Default row. |

---

### `game_logic.py` — Update Functions

**Module-level infrastructure:**
- `_physics_lock` — `threading.Lock` protecting shared state between main and physics threads
- `_physics_running` — flag controlling the background physics loop
- `_physics_thread` — reference to the daemon physics thread
- `_cached_obs_rect` — cached merged goal+depot obstacle rect, rebuilt only on game reset via `rebuild_obstacle_cache(state)`

**Core update functions:**

| Function | Responsibility |
|---|---|
| `update_timer(state, dt)` | Decrements timer only if `timer_running`; at 20s switches to `ENDGAME`; at 0s triggers scoring, sets `FINISHED`, sets `timer_running = False`, and clears robot velocity |
| `score_pattern(state)` | Each ramp slot matching `motif[i % 3]` → +2 points |
| `score_base(state)` | Robot fully inside base → 10 pts, partial → 5 pts |
| `update_artifact_physics(state, dt)` | 2D physics with early-exit optimization: velocity integration, exponential friction, field-wall bounce with restitution, goal+depot merged-obstacle containment push-out + bounce, artifact–artifact collision resolution, robot–artifact push with restitution + extra push force. Uses cached obstacle rect and local variable aliases for performance. |
| `constrain_robot(state)` | Pushes robot out of cached obstacle rect (iterative resolve, capped at `_CONSTRAIN_MAX_ITER = 8` iterations) |
| `update_turret_angle(state)` | Snaps turret angle to point at goal. **Runs on the main thread every frame** (not in physics thread). |
| `update_intake_heat(state, dt)` | Intake motor heat management. When intake is ON, heat increases at `dt / intake_heat_time`. At 1.0 → overheat: auto-shutoff, cooldown starts, intake blocked. When overheated, heat visually drains at `dt / intake_cooldown_time` synced with cooldown timer. When intake OFF and heat < 1.0, heat decreases at `dt / intake_cool_time`. |
| `_update_flying_and_gate(state, dt)` | Moves flying artifacts toward goal, handles scoring on arrival, updates gate auto-close timer. Runs under `_physics_lock`. |
| `update_physics(state, dt)` | Runs one frame of physics simulation under `_physics_lock`: park status is always updated; robot constraint, intake heat, artifact physics, flying artifacts, and gate timer only run when `timer_running` is `True`. Does NOT update turret angle. |
| `get_park_status(state)` | Returns `"NONE"`, `"PARTIAL"`, or `"FULL"` based on robot rect vs base rect containment |
| `update_park_status(state)` | Writes `get_park_status()` result to `state.park_status` |

**Intake overheating system:**
- Heat bar on HUD fills from 0→100% over `intake_heat_time` seconds when intake is ON
- Color gradient: green (0–50%) → yellow (50–80%) → orange (80–95%) → red (95–100%)
- At 100%: intake auto-shutoffs, enters cooldown
- During cooldown: bar visually drains from full→empty over `intake_cooldown_time` seconds, countdown timer text displayed next to bar
- Intake is blocked during cooldown (toggle disabled on keyboard E, hold blocked on gamepad right trigger)
- Partial cool: if intake toggled OFF before overheating, heat drains at `intake_cool_time` seconds
- Heat fully reset on pause, finish, or game reset

**Turret tracking:**
- Each frame, the target angle is computed as `atan2(gx, -gy)` from robot to goal center
- Shortest-path wrap-around: `diff = (target - current + π) % (2π) - π` prevents the 360° spin when crossing the goal's vertical centerline
- Snaps instantly to target (no smoothing factor) — turret always points at the goal
- **Runs on the main thread** so turret always tracks in real time regardless of physics thread timing

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
| Artifact classified on ramp | +3 | Only if in launch zone (top triangle, base/parking zone, or shooting zone) |
| Overflow / Depot | +1 each | Only if in launch zone (top triangle, base/parking zone, or shooting zone) |
| Pattern match (per matching slot) | +2 | Evaluated at match end |
| Full base return | +10 | Robot entirely inside base rect at match end |
| Partial base return | +5 | Robot partially in base rect at match end |

**Physics details:**
- Exponential friction: `v *= friction^dt` where `friction = 0.08` → near-instant stops
- Field walls: restitution `0.45`, push out and reverse velocity component
- Goal+depot obstacle: single merged rect (cached), artifacts pushed to nearest edge with bounce `0.45`; outside-edge collision via clamp-based normal push
- Artifact–artifact: overlap separation `0.5` each, impulse with restitution `0.50`; **both-stationary early-exit**: skips pair entirely if both artifacts have zero velocity
- Robot–artifact: overlap pushes artifact, impulse with restitution `0.90`; extra `push_force = 600` applied as velocity bias when speed is low
- **Early-exit optimization**: Stationary artifacts (`vx == 0, vy == 0`) that are far from the robot (beyond `rob_r + R + 20` px) are skipped entirely
- **Local variable aliases**: All CONFIG dict lookups hoisted to locals; robot position/velocity cached outside loops to avoid repeated attribute access

---

### `input_handler.py` — Controls

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
| `_launch_held(state, r)` | Launch all held artifacts toward the goal |
| `_toggle_gate(state, r)` | Toggle gate open if robot is within gate_range. Acquires `_physics_lock` internally to serialize with physics thread. |
| `_try_pickup(state, r, in_front)` | Attempt to pick up nearest artifact in front cone |
| `_handle_gamepad(state, r, joy, events, dt, in_front)` | Process gamepad stick, trigger, and button input |
| `_execute_pause_action(state, index)` | Execute selected pause menu action (Resume/Restart/Detect Gamepads/Options/Exit) |

**Return value:**
- `handle_input(state, dt)` returns `True` if a reset was requested (F5 / gamepad Back); `None` otherwise. The caller performs the actual reset under the physics lock.

**Joystick initialization:**
- `init_joysticks(rescan=False)` — initializes all connected gamepads. If `rescan=True`, reinitializes the joystick subsystem for hot-plug support.

**Pause menu navigation:**
- When paused (and match not finished), keyboard Up/Down (or Numpad 8/2) or gamepad D-pad/stick navigate the 5-button pause menu
- Enter/Space (keyboard) or A button (gamepad) selects the highlighted action
- Navigation uses cooldowns (`_MENU_NAV_DELAY_MS = 200`) to prevent rapid-fire
- Gamepad stick uses deadzone and `_menu_stick_used` flag for clean single-step navigation

**Options screen (keybind customization):**
- Accessed from pause menu "Options" button
- Two tabs: KEYBOARD and GAMEPAD, switchable with Left/Right arrows (or Numpad 4/6), LB/RB, or gamepad D-pad left/right
- Each tab lists all bindable actions with current binding; selected row highlighted
- Enter/A on a row starts rebinding mode (pulsing red-orange highlight)
- During rebinding: press any key/button to assign, or Backspace/B to clear
- Escape/backspace exits Options screen (returns to pause menu)
- "Reset to Default" row at bottom restores all bindings on current tab
- Duplicate bindings shown with `!` warning indicator
- Locked bindings (gamepad Reset) shown as `(Fixed)`
- Navigation cooldown prevents rapid-fire on all input methods
- **Keybinds persist** across game sessions: saved to `keybinds.json` in the game directory after every change (rebind, clear, or reset). Loaded on startup. Falls back to `DEFAULT_KEYBINDS` if file is missing or corrupt.

**Timer controls** (always active, even when paused/stopped):
| Key | Action |
|---|---|
| `F5` | Reset game (timer stops) |
| `F6` | Start timer (only works when stopped) |
| `ESC` | Pause / Resume toggle |
| `F10` | Quit |

**Robot** has a facing direction (`angle`, 0 = up). Default `drive_mode = "field"`:
- In field mode: W/S/A/D move in world axes regardless of facing
- In robot mode: W = forward (nose direction), S = backward, A/D strafe left/right perpendicular to facing
- Left/Right arrows rotate in place
- Pickup only works for artifacts in the front cone (120°)

**Keyboard:**
| Key | Action |
|---|---|
| `W` | Move forward (facing direction in robot mode, world-up in field mode) |
| `S` | Move backward (facing direction in robot mode, world-down in field mode) |
| `A` | Strafe left (robot mode) / World left (field mode) |
| `D` | Strafe right (robot mode) / World right (field mode) |
| `←` | Rotate left |
| `→` | Rotate right |
| `E` | Toggle intake on/off (when on, continuously picks up artifacts in front cone; blocked when overheated) |
| `Q` | Launch ALL held artifacts toward goal (any number) |
| `T` | Toggle gate open (must be within gate_range of gate) |
| `R` | Toggle drive mode (`robot` ↔ `field`) |

**Gamepad** (first joystick):
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

**Intake overheating behavior:**
- `E` (keyboard) toggles intake; **blocked when `intake_overheated` is True**
- Right trigger (gamepad) holds to intake (intake active while held, deactivates on release); **blocked when `intake_overheated` is True**
- When intake is ON, `intake_heat` increases each frame; HUD shows a color-interpolated bar (green→yellow→orange→red)
- At 100% heat: intake auto-shutoffs, 10-second cooldown begins, bar visually drains alongside countdown timer text
- Partial cool: if intake toggled OFF before 100%, bar drains over `intake_cool_time` seconds and intake can be re-enabled anytime
- Heat fully reset on pause, match end, or game reset

**Parking status:**
- Live-updated every frame in `update_park_status()`
- `NONE` — robot has zero overlap with base rect
- `PARTIAL` — robot overlaps but is not fully inside → +5 pts at match end
- `FULL` — robot entirely inside base rect → +10 pts at match end
- HUD shows 3-segment indicator bar with status label (no header text)
- Field shows pulsing gold border (PARTIAL) or green glow fill (FULL)

**Pause behavior:**
- When `timer_running` is `False`, all robot input is frozen (no movement, pickup, launch, gate)
- `intake_active` is reset to `False` when timer stops or match ends
- `intake_heat`, `intake_overheated`, and `intake_cooldown_timer` are all reset to zero on pause/finish
- Timer digits shown in muted gray; STOPPED or PAUSED badge displayed on HUD
- Physics simulation also frozen (artifacts stop moving)
- A pause menu overlay appears with selectable buttons (Resume, Restart Game, Detect Gamepads, Options, Exit)
- Navigation via keyboard arrows or gamepad D-pad/stick; selection via Enter/Space or gamepad A button

---

## Game Flow

1. Game starts in **TELEOP** phase with 120 seconds on the clock, timer **STOPPED**, drive mode **FIELD**
2. Press **F6** (keyboard) to begin the timer
3. **ESC** (keyboard) / **Y** (gamepad) pauses and resumes mid-match
4. At **20 seconds remaining**, phase switches to **ENDGAME** (orange flashing text)
5. At **0 seconds**, pattern scoring + base scoring are calculated atomically (under lock), `timer_running` is set to `False`, and robot velocity is cleared
6. Phase becomes **FINISHED** — robots freeze, all scoring stops, overlay appears with the exact same score shown on the HUD
7. Press **F5** to reset, **F10** to quit
8. Window is **resizable** — content scales to fit while preserving aspect ratio

---

## Threading Architecture

```
Main Thread                          Physics Thread (daemon)
─────────────                        ──────────────────────
input_handler.handle_input()
update_turret_angle()
                                     _physics_thread_target loop:
acquire _physics_lock                   acquire _physics_lock
  update_timer()                          update_park_status()
  draw_field()                            constrain_robot()
  draw_artifacts()                        update_intake_heat()
  draw_robot()                            update_artifact_physics()
  draw_hud()                              _update_flying_and_gate()
  draw_match_end()                     release _physics_lock
  draw_pause_menu()
release _physics_lock
smoothscale + display.flip()
clock.tick_busy_loop(120)
```

- `_physics_lock` protects all shared `GameState` mutations
- `update_timer()` runs under the lock so `score_pattern()`/`score_base()` are atomic with respect to `_update_flying_and_gate()` — no race between scoring and the last flying artifacts arriving
- When the match ends, `timer_running` is set to `False` and `robot.vx`/`robot.vy` are cleared, stopping all physics updates and preventing phantom artifact pushes
- Turret angle update runs on main thread outside the lock (simple float reads/writes are GIL-atomic)
- Reset acquires the lock to prevent physics thread from accessing state mid-reset
- Gate toggle acquires the lock internally to safely clear the ramp without racing the physics thread
- Physics thread runs at 60 Hz independently of the main thread's 120 Hz render rate
