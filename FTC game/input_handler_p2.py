"""
FTC DECODE — P2 input handling (multi-player only).
"""

import math

import pygame
from config import CONFIG, FX, FY, FS, clamp
from input_handler import (
    _launch_held,
    _toggle_gate,
    _try_pickup,
    _joysticks,
    _trigger_cooldown,
)


# ============================================================
# P2 INPUT HANDLER
# ============================================================
def handle_input_p2(state, dt, events=None):
    """Process input for Player 2 in 1v1 mode.

    Uses state.robot2, state.team2, state.keybinds_p2, and state.p2_device.
    P2 can pause/unpause the game and navigate the pause menu.
    """
    if state.game_mode != "1v1" or state.robot2 is None:
        return
    if state.phase == "FINISHED":
        state.intake_active2 = False
        state.intake_heat2 = 0.0
        state.intake_overheated2 = False
        state.intake_cooldown_timer2 = 0.0
        return

    # P2 robot freezes when paused or options screen is open
    if not state.timer_running or state.options_active:
        state.intake_active2 = False
        state.intake_heat2 = 0.0
        state.intake_overheated2 = False
        state.intake_cooldown_timer2 = 0.0
        return  # still returns — robot frozen, but pause toggle is in global controls

    r = state.robot2
    r.vx = 0.0
    r.vy = 0.0

    keys = pygame.key.get_pressed()
    if events is None:
        events = pygame.event.get()

    device = state.p2_device

    if device == "keyboard":
        _handle_p2_keyboard(state, r, keys, events, dt)
    elif device in ("gamepad0", "gamepad1"):
        joy_idx = 0 if device == "gamepad0" else 1
        if joy_idx < len(_joysticks):
            joy = _joysticks[joy_idx]
            _handle_p2_gamepad(state, r, joy, events, dt)


def _handle_p2_keyboard(state, r, keys, events, dt):
    """Handle P2 keyboard input using P2 keybinds."""
    binds = state.keybinds_p2.get("keyboard", {})

    def _p2_key_held(action):
        binding = binds.get(action)
        return binding is not None and binding[0] == "key" and keys[binding[1]]

    def _p2_key_pressed(action):
        binding = binds.get(action)
        return (binding is not None and binding[0] == "key" and
                any(e.type == pygame.KEYDOWN and e.key == binding[1] for e in events))

    if r.drive_mode == "field":
        _handle_p2_field_drive(r, _p2_key_held, dt)
    else:
        _handle_p2_robot_drive(r, _p2_key_held, dt)

    def in_front(ax, ay):
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

    if _p2_key_pressed("Launch Artifacts"):
        _launch_held(state, r, state.team2)
    if _p2_key_pressed("Toggle Gate"):
        _toggle_gate(state, r)

    # Hold-to-intake
    if _p2_key_held("Toggle Intake") and not state.intake_overheated2:
        state.intake_active2 = True
    else:
        state.intake_active2 = False

    if state.intake_active2:
        _try_pickup(state, r, in_front)


def _handle_p2_field_drive(r, key_held_fn, dt):
    """Process WASD movement in field-oriented mode for P2."""
    dx, dy = 0, 0
    if key_held_fn("Move Forward"):
        dy = -1
    if key_held_fn("Move Backward"):
        dy = 1
    if key_held_fn("Strafe Left"):
        dx = -1
    if key_held_fn("Strafe Right"):
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
    if key_held_fn("Rotate Left"):
        rot -= 1
    if key_held_fn("Rotate Right"):
        rot += 1
    if rot != 0:
        r.angle += rot * math.radians(CONFIG["rotation_speed"]) * dt


def _handle_p2_robot_drive(r, key_held_fn, dt):
    """Process WASD movement in robot-oriented mode for P2."""
    fx = math.sin(r.angle)
    fy = -math.cos(r.angle)
    sx = math.cos(r.angle)
    sy = math.sin(r.angle)
    if key_held_fn("Move Forward"):
        r.vx += fx * r.speed
        r.vy += fy * r.speed
    if key_held_fn("Move Backward"):
        r.vx -= fx * r.speed
        r.vy -= fy * r.speed
    if key_held_fn("Strafe Left"):
        r.vx -= sx * r.speed
        r.vy -= sy * r.speed
    if key_held_fn("Strafe Right"):
        r.vx += sx * r.speed
        r.vy += sy * r.speed
    rot = 0.0
    if key_held_fn("Rotate Left"):
        rot -= 1
    if key_held_fn("Rotate Right"):
        rot += 1
    if rot != 0:
        r.angle += rot * math.radians(CONFIG["rotation_speed"]) * dt
    if r.vx != 0 or r.vy != 0:
        r.x += r.vx * dt
        r.y += r.vy * dt
        r.x = clamp(r.x, FX, FX + FS)
        r.y = clamp(r.y, FY, FY + FS)


def _handle_p2_gamepad(state, r, joy, events, dt):
    """Handle P2 gamepad input using P2 keybinds."""
    binds = state.keybinds_p2.get("gamepad", {})
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

    jid = joy.get_id()

    def _gp_button(action):
        binding = binds.get(action)
        return (binding is not None and binding[0] == "button" and
                any(e.type == pygame.JOYBUTTONDOWN and e.joy == jid and e.button == binding[1]
                    for e in events))

    def _gp_axis(action):
        binding = binds.get(action)
        if binding and binding[0] == "axis":
            n = joy.get_numaxes()
            if binding[1] < n:
                return joy.get_axis(binding[1]) > 0.5
        return False

    def _gp_button_held(action):
        binding = binds.get(action)
        if binding and binding[0] == "button":
            n = joy.get_numbuttons()
            if binding[1] < n:
                return joy.get_button(binding[1])
        return False

    lt = _gp_axis("Launch") or _gp_button("Launch")
    rt = _gp_axis("Intake") or _gp_button_held("Intake")

    # Left trigger: launch (edge-detect)
    prev_lt = _trigger_cooldown.get((jid, "prev_lt_p2"), 0)
    if lt and not prev_lt:
        _launch_held(state, r, state.team2)
    _trigger_cooldown[(jid, "prev_lt_p2")] = int(lt)

    # Right trigger: hold-to-intake
    if rt:
        if not state.intake_overheated2:
            state.intake_active2 = True
    else:
        state.intake_active2 = False

    def in_front(ax, ay):
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

    if state.intake_active2:
        _try_pickup(state, r, in_front)

    if _gp_button("Gate") or _gp_axis("Gate"):
        _toggle_gate(state, r)
