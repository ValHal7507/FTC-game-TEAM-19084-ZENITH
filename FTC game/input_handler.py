"""
FTC DECODE — Keyboard and gamepad input handling.
"""

import math
import sys
import random

import pygame
from config import CONFIG, FX, FY, FS, clamp, dist, DEFAULT_KEYBINDS, LOCKED_KEYBINDS, save_keybinds
from game_state import Artifact, FlyingArtifact, get_ramp_scatter_positions
from game_logic import _physics_lock

_joysticks: list = []
_trigger_cooldown: dict = {}
_menu_nav_cooldown: dict = {}
_MENU_NAV_DELAY_MS = 200


# ============================================================
# P1 DEVICE HELPERS
# ============================================================
def _resolve_p1_joystick(state):
    """Return the pygame Joystick object for P1 if they are on gamepad, else None."""
    dev = state.p1_device
    if isinstance(dev, str) and dev.startswith("gamepad"):
        joy_idx = int(dev[-1])
        if joy_idx < len(_joysticks):
            return _joysticks[joy_idx]
    return None


def _is_p1_event(event, state):
    """Return True if *event* originated from P1's assigned device."""
    dev = state.p1_device
    if dev == "keyboard":
        return event.type == pygame.KEYDOWN
    if isinstance(dev, str) and dev.startswith("gamepad"):
        joy_idx = int(dev[-1])
        if joy_idx < len(_joysticks):
            return event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION) and getattr(event, "joy", None) == _joysticks[joy_idx].get_id()
    return False


def _resolve_solo_gamepads():
    """Return list of all connected joysticks (for solo mode dual-input)."""
    return list(_joysticks)


# ============================================================
# KEYBIND HELPERS
# ============================================================
def _key_held(state, action, keys):
    """Check if a keyboard action's key is currently held."""
    binding = state.keybinds["keyboard"].get(action)
    return binding is not None and binding[0] == "key" and keys[binding[1]]


def _key_pressed(action, events, state):
    """Check if a keyboard action's key was pressed this frame."""
    binding = state.keybinds["keyboard"].get(action)
    return (binding is not None and binding[0] == "key" and
            any(e.type == pygame.KEYDOWN and e.key == binding[1] for e in events))


def _gamepad_button(action, events, state, jid):
    """Check if a gamepad action's button was pressed this frame."""
    binding = state.keybinds["gamepad"].get(action)
    return (binding is not None and binding[0] == "button" and
            any(e.type == pygame.JOYBUTTONDOWN and e.joy == jid and e.button == binding[1]
                for e in events))


def _gamepad_axis(action, joy, state):
    """Check if a gamepad action's axis is active (>0.5)."""
    binding = state.keybinds["gamepad"].get(action)
    if binding and binding[0] == "axis":
        n = joy.get_numaxes()
        if binding[1] < n:
            return joy.get_axis(binding[1]) > 0.5
    return False


def _gamepad_button_held(action, joy, state):
    """Check if a gamepad action's button is currently held."""
    binding = state.keybinds["gamepad"].get(action)
    if binding and binding[0] == "button":
        n = joy.get_numbuttons()
        if binding[1] < n:
            return joy.get_button(binding[1])
    return False


def init_joysticks(rescan=False):
    """Initialize all connected gamepads.
    If rescan=True, reinitializes joystick subsystem for hot-plug support.
    """
    if rescan:
        pygame.joystick.quit()
        pygame.joystick.init()
    _joysticks.clear()
    for i in range(pygame.joystick.get_count()):
        try:
            j = pygame.joystick.Joystick(i)
            j.init()
            _joysticks.append(j)
            print(f"  Gamepad {i}: {j.get_name()}")
        except Exception as e:
            print(f"  Gamepad {i}: init failed ({e})")


def handle_input(state, dt, events=None):
    """Process all keyboard and gamepad events for one frame.

    Returns True if a game reset was requested (caller must perform the
    reset under the physics lock).
    """
    if events is None:
        events = pygame.event.get()
    keys = pygame.key.get_pressed()

    for e in events:
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.VIDEORESIZE:
            pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)

    # Global controls (always active)
    reset_requested = False
    solo_mode = state.game_mode == "solo"
    for e in events:
        if e.type == pygame.KEYDOWN:
            # Admin controls (F5/F6/F10): always available via keyboard
            if True:
                if e.key == pygame.K_F5:
                    reset_requested = True
                elif e.key == pygame.K_F6:
                    if state.phase != "FINISHED" and not state.timer_running:
                        state.timer_running = True
                elif e.key == pygame.K_F10:
                    pygame.quit()
                    sys.exit()
            # Pause (ESC): always available via keyboard
            if True:
                if e.key == pygame.K_ESCAPE:
                    if state.phase == "FINISHED":
                        pass
                    elif state.options_active:
                        state.options_active = False
                    elif state.timer_running:
                        state.timer_running = False
                        state.pause_menu_index = 0
                    else:
                        state.timer_running = True

    if reset_requested:
        return True

    # Pause menu navigation (when timer not running and match not finished)
    if not state.timer_running and state.phase != "FINISHED" and not state.options_active:
        num_btns = 5 if state.game_mode == "1v1" else 6
        # Keyboard navigation — always available
        if True:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_UP, pygame.K_KP8):
                        state.pause_menu_index = (state.pause_menu_index - 1) % num_btns
                    elif e.key in (pygame.K_DOWN, pygame.K_KP2):
                        state.pause_menu_index = (state.pause_menu_index + 1) % num_btns
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return _execute_pause_action(state, state.pause_menu_index)

        state.intake_active = False
        state.intake_heat = 0.0
        state.intake_overheated = False
        state.intake_cooldown_timer = 0.0
        return

    # OPTIONS SCREEN INPUT
    if state.options_active:
        page_name = "keyboard" if state.options_page == 0 else "gamepad"
        if state.options_page == 0:
            from config import KEYBIND_ACTIONS_KEYBOARD as actions
        else:
            from config import KEYBIND_ACTIONS_GAMEPAD as actions
        num_rows = len(actions) + 1  # +1 for Reset to Default row

        for e in events:
            if e.type == pygame.KEYDOWN:
                if state.options_rebinding:
                    if e.key == pygame.K_BACKSPACE:
                        action = actions[state.options_index]
                        state.keybinds["keyboard"][action] = None
                        state.options_rebinding = False
                        save_keybinds(state.keybinds)
                    elif e.key == pygame.K_ESCAPE:
                        state.options_rebinding = False
                    else:
                        action = actions[state.options_index]
                        state.keybinds["keyboard"][action] = ("key", e.key)
                        state.options_rebinding = False
                        save_keybinds(state.keybinds)
                else:
                    if e.key == pygame.K_ESCAPE or e.key == pygame.K_BACKSPACE:
                        state.options_active = False
                        state.options_rebinding = False
                    elif e.key in (pygame.K_UP, pygame.K_KP8):
                        state.options_index = (state.options_index - 1) % num_rows
                    elif e.key in (pygame.K_DOWN, pygame.K_KP2):
                        state.options_index = (state.options_index + 1) % num_rows
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if state.game_mode != "1v1":
                            if state.options_index == num_rows - 1:
                                state.keybinds[page_name] = dict(DEFAULT_KEYBINDS[page_name])
                                save_keybinds(state.keybinds)
                            else:
                                action = actions[state.options_index]
                                if action not in LOCKED_KEYBINDS.get(page_name, set()):
                                    state.options_rebinding = True
                    elif e.key in (pygame.K_LEFT, pygame.K_KP4):
                        state.options_page = 0
                        state.options_index = 0
                        state.options_rebinding = False
                    elif e.key in (pygame.K_RIGHT, pygame.K_KP6):
                        state.options_page = 1
                        state.options_index = 0
                        state.options_rebinding = False

        # Gamepad axis rebinding — capture axis input when rebinding gamepad page
        if state.options_rebinding and state.options_page == 1:
            for p1_joy in _resolve_solo_gamepads():
                jid = p1_joy.get_id()
                for e in events:
                    if e.type == pygame.JOYAXISMOTION and e.joy == jid:
                        if abs(e.value) > 0.5:
                            action = actions[state.options_index]
                            state.keybinds["gamepad"][action] = ("axis", e.axis)
                            state.options_rebinding = False
                            save_keybinds(state.keybinds)

        state.intake_active = False
        state.intake_heat = 0.0
        state.intake_overheated = False
        state.intake_cooldown_timer = 0.0
        return

    # Frozen when match is over
    if state.phase == "FINISHED":
        state.intake_active = False
        state.intake_heat = 0.0
        state.intake_overheated = False
        state.intake_cooldown_timer = 0.0
        return

    r = state.robot
    r.vx = 0.0
    r.vy = 0.0

    p1_dev = state.p1_device

    def _in_front(ax, ay):
        lfx = math.sin(r.angle)
        lfy = -math.cos(r.angle)
        dx = ax - r.x
        dy = ay - r.y
        d = math.hypot(dx, dy)
        if d == 0:
            return False
        dot = (dx / d) * lfx + (dy / d) * lfy
        half_cone = math.radians(CONFIG["pickup_cone_angle"] / 2)
        return dot > math.cos(half_cone)

    # In solo mode: run BOTH keyboard and gamepad input simultaneously
    if solo_mode:
        # Keyboard drive — always runs
        if r.drive_mode == "field":
            _handle_field_drive(r, keys, dt, state)
        else:
            _handle_robot_drive(r, keys, dt, state)

        # Keyboard rotation — always runs
        rot = 0.0
        if _key_held(state, "Rotate Left", keys):
            rot -= 1
        if _key_held(state, "Rotate Right", keys):
            rot += 1
        if rot != 0:
            r.angle += rot * math.radians(CONFIG["rotation_speed"]) * dt

        # Gamepad drive + rotation — scan ALL connected gamepads
        for joy in _resolve_solo_gamepads():
            lx, ly = joy.get_axis(0), joy.get_axis(1)
            deadzone = 0.15
            if abs(lx) > deadzone or abs(ly) > deadzone:
                if r.drive_mode == "field":
                    r.vx = lx * r.speed
                    r.vy = ly * r.speed
                    r.x += r.vx * dt
                    r.y += r.vy * dt
                    r.x = clamp(r.x, FX, FX + FS)
                    r.y = clamp(r.y, FY, FY + FS)
                else:
                    fx = math.sin(r.angle)
                    fy = -math.cos(r.angle)
                    sx = math.cos(r.angle)
                    sy = math.sin(r.angle)
                    r.vx = (fx * -ly + sx * lx) * r.speed
                    r.vy = (fy * -ly + sy * lx) * r.speed
                    r.x += r.vx * dt
                    r.y += r.vy * dt
                    r.x = clamp(r.x, FX, FX + FS)
                    r.y = clamp(r.y, FY, FY + FS)
            # Gamepad rotation
            rx = joy.get_axis(2)
            if abs(rx) > 0.15:
                r.angle += rx * math.radians(CONFIG["rotation_speed"]) * dt

        # Keyboard actions
        if _key_pressed("Launch Artifacts", events, state):
            _launch_held(state, r)
        if _key_pressed("Drive Mode", events, state):
            r.drive_mode = "robot" if r.drive_mode == "field" else "field"
        if _key_pressed("Toggle Gate", events, state):
            _toggle_gate(state, r)

        # Keyboard hold-to-intake
        kbd_intake = _key_held(state, "Toggle Intake", keys) and not state.intake_overheated

        # Gamepad actions — scan ALL connected gamepads
        any_rt = False
        for joy in _resolve_solo_gamepads():
            jid = joy.get_id()
            lt = _gamepad_axis("Launch", joy, state) or _gamepad_button("Launch", events, state, jid)
            rt = _gamepad_axis("Intake", joy, state) or _gamepad_button_held("Intake", joy, state)
            prev_lt = _trigger_cooldown.get((jid, "prev_lt"), 0)
            if lt and not prev_lt:
                _launch_held(state, r)
            _trigger_cooldown[(jid, "prev_lt")] = int(lt)
            if rt:
                any_rt = True
            if _gamepad_button("Gate", events, state, jid) or _gamepad_axis("Gate", joy, state):
                _toggle_gate(state, r)
            if _gamepad_button("Drive Mode", events, state, jid):
                r.drive_mode = "robot" if r.drive_mode == "field" else "field"

        # Combine: intake active if keyboard OR gamepad is held
        if kbd_intake or any_rt:
            state.intake_active = True
        else:
            state.intake_active = False

        if state.intake_active:
            _try_pickup(state, r, _in_front)

    # 1v1: use only the assigned device
    elif p1_dev == "keyboard":
        if r.drive_mode == "field":
            _handle_field_drive(r, keys, dt, state)
        else:
            _handle_robot_drive(r, keys, dt, state)

        if _key_pressed("Launch Artifacts", events, state):
            _launch_held(state, r)
        if _key_pressed("Toggle Gate", events, state):
            _toggle_gate(state, r)

        # Hold-to-intake
        if _key_held(state, "Toggle Intake", keys) and not state.intake_overheated:
            state.intake_active = True
        else:
            state.intake_active = False

        if state.intake_active:
            _try_pickup(state, r, _in_front)

    elif isinstance(p1_dev, str) and p1_dev.startswith("gamepad"):
        joy_idx = int(p1_dev[-1])
        if joy_idx < len(_joysticks):
            joy = _joysticks[joy_idx]
            _handle_gamepad(state, r, joy, events, dt, _in_front)


def _execute_pause_action(state, index):
    """Execute the selected pause menu action. Returns True if reset requested."""
    # In 1v1, Options is hidden — remap indices 3,4 to buttons 4,5 (Mode Select, Quit)
    if state.game_mode == "1v1" and index >= 3:
        index += 1
    if index == 0:  # Resume
        state.timer_running = True
    elif index == 1:  # Restart Game
        return True
    elif index == 2:  # Detect Gamepads
        init_joysticks(rescan=True)
        print(f"Detected {len(_joysticks)} gamepad(s)")
    elif index == 3:  # Options
        state.options_active = True
        state.options_page = 0
        state.options_index = 0
        state.options_rebinding = False
    elif index == 4:  # Mode Select
        state.pending_return = "menu"
    elif index == 5:  # Quit
        pygame.quit()
        sys.exit()
    return False


def _handle_field_drive(r, keys, dt, state):
    """Process WASD movement in field-oriented mode."""
    dx, dy = 0, 0
    if _key_held(state, "Move Forward", keys):
        dy = -1
    if _key_held(state, "Move Backward", keys):
        dy = 1
    if _key_held(state, "Strafe Left", keys):
        dx = -1
    if _key_held(state, "Strafe Right", keys):
        dx = 1
    if dx != 0 or dy != 0:
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        r.vx = dx * r.speed
        r.vy = dy * r.speed
        r.x += dx * r.speed * dt
        r.y += dy * r.speed * dt
        r.x = clamp(r.x, FX, FX + FS)
        r.y = clamp(r.y, FY, FY + FS)
    rot = 0.0
    if _key_held(state, "Rotate Left", keys):
        rot -= 1
    if _key_held(state, "Rotate Right", keys):
        rot += 1
    if rot != 0:
        r.angle += rot * math.radians(CONFIG["rotation_speed"]) * dt


def _handle_robot_drive(r, keys, dt, state):
    """Process WASD movement in robot-oriented mode."""
    fx = math.sin(r.angle)
    fy = -math.cos(r.angle)
    sx = math.cos(r.angle)
    sy = math.sin(r.angle)
    if _key_held(state, "Move Forward", keys):
        r.vx += fx * r.speed
        r.vy += fy * r.speed
    if _key_held(state, "Move Backward", keys):
        r.vx -= fx * r.speed
        r.vy -= fy * r.speed
    if _key_held(state, "Strafe Left", keys):
        r.vx -= sx * r.speed
        r.vy -= sy * r.speed
    if _key_held(state, "Strafe Right", keys):
        r.vx += sx * r.speed
        r.vy += sy * r.speed
    rot = 0.0
    if _key_held(state, "Rotate Left", keys):
        rot -= 1
    if _key_held(state, "Rotate Right", keys):
        rot += 1
    if rot != 0:
        r.angle += rot * math.radians(CONFIG["rotation_speed"]) * dt
    if r.vx != 0 or r.vy != 0:
        r.x += r.vx * dt
        r.y += r.vy * dt
        r.x = clamp(r.x, FX, FX + FS)
        r.y = clamp(r.y, FY, FY + FS)


def _launch_held(state, r=None, team=None):
    """Launch all held artifacts toward the goal."""
    if r is None:
        r = state.robot
    if team is None:
        team = state.team
    if not r.holding:
        return
    if state.robot2 is not None and r is state.robot2:
        from_zone = state.in_launch_zone2(r.x, r.y)
    else:
        from_zone = state.in_launch_zone(r.x, r.y)
    full = len(r.holding) == CONFIG["max_hold"]
    gr = state.goal_rect()
    held = list(r.holding)
    r.holding.clear()
    team_id = "p2" if r is getattr(state, 'robot2', None) else "p1"
    for a in held:
        ox = random.uniform(-6, 6)
        oy = random.uniform(-6, 6)
        state.flying.append(FlyingArtifact(
            r.x + ox, r.y + oy, gr.centerx, gr.centery, a.color,
            scoring=from_zone, full_set=full, team=team_id
        ))


def _toggle_gate(state, r):
    """Toggle the gate open if robot is close enough."""
    gt = state.gate_rect()
    if dist((r.x, r.y), (gt.centerx, gt.centery)) < CONFIG["gate_range"]:
        team = state.team2 if (state.robot2 is not None and r is state.robot2) else state.team
        if not team.gate_open:
            with _physics_lock:
                team.gate_open = True
                team.gate_timer = CONFIG["gate_open_duration"]
                cleared = team.clear_ramp()
                positions = get_ramp_scatter_positions(state)
                for c in cleared:
                    tx, ty = random.choice(positions)
                    a = Artifact(tx, ty, c,
                        vx=random.uniform(-40, 40), vy=random.uniform(-40, 40),
                        zone="alliance", index=0)
                    state.artifacts.append(a)


def _try_pickup(state, r, in_front):
    """Attempt to pick up the nearest artifact in front of the robot."""
    a = state.nearest_artifact(r.x, r.y, CONFIG["pickup_radius"])
    if a and r.can_pickup() and in_front(a.x, a.y):
        a.on_field = False
        r.holding.append(a)


def _handle_gamepad(state, r, joy, events, dt, in_front):
    """Process gamepad stick, trigger, and button input."""
    lx, ly = joy.get_axis(0), joy.get_axis(1)
    rx = joy.get_axis(2)
    dz = 0.15
    if abs(lx) < dz:
        lx = 0
    if abs(ly) < dz:
        ly = 0
    if abs(rx) < dz:
        rx = 0
    if rx != 0:
        r.angle += rx * math.radians(CONFIG["rotation_speed"]) * dt
    if r.drive_mode == "field":
        mvx = lx
        mvy = ly
    else:
        cfx = math.sin(r.angle)
        cfy = -math.cos(r.angle)
        px = math.cos(r.angle)
        py = math.sin(r.angle)
        mvx = cfx * (-ly) + px * lx
        mvy = cfy * (-ly) + py * lx
    if mvx != 0 or mvy != 0:
        r.vx = mvx * r.speed
        r.vy = mvy * r.speed
        r.x += mvx * r.speed * dt
        r.y += mvy * r.speed * dt
        r.x = clamp(r.x, FX, FX + FS)
        r.y = clamp(r.y, FY, FY + FS)
    lt = _gamepad_axis("Launch", joy, state) or _gamepad_button("Launch", events, state, joy.get_id())
    rt = _gamepad_axis("Intake", joy, state) or _gamepad_button_held("Intake", joy, state)
    jid = joy.get_id()

    # Left trigger: launch (edge-detect, press only)
    prev_lt = _trigger_cooldown.get((jid, "prev_lt"), 0)
    if lt and not prev_lt:
        _launch_held(state, r)
    _trigger_cooldown[(jid, "prev_lt")] = int(lt)

    # Right trigger: hold-to-intake (active while held, blocked when overheated)
    if rt:
        if not state.intake_overheated:
            state.intake_active = True
    else:
        state.intake_active = False

    if state.intake_active:
        _try_pickup(state, r, in_front)

    if _gamepad_button("Gate", events, state, jid) or _gamepad_axis("Gate", joy, state):
        _toggle_gate(state, r)


# Public aliases for AI / mode files
launch_held = _launch_held
toggle_gate = _toggle_gate

