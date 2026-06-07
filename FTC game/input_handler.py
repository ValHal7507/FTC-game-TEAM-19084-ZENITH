"""
FTC DECODE — Keyboard and gamepad input handling.
"""

import math
import sys
import random

import pygame
from config import CONFIG, FX, FY, FS, clamp, dist
from game_state import Artifact, FlyingArtifact, get_ramp_scatter_positions

_joysticks: list = []
_trigger_cooldown: dict = {}


def init_joysticks():
    """Initialize all connected gamepads."""
    _joysticks.clear()
    for i in range(pygame.joystick.get_count()):
        try:
            j = pygame.joystick.Joystick(i)
            j.init()
            _joysticks.append(j)
            print(f"  Gamepad {i}: {j.get_name()}")
        except Exception as e:
            print(f"  Gamepad {i}: init failed ({e})")


def handle_input(state, dt):
    """Process all keyboard and gamepad events for one frame.

    Returns True if a game reset was requested (caller must perform the
    reset under the physics lock).
    """
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
    for e in events:
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_F5:
                reset_requested = True
            elif e.key == pygame.K_F6:
                if state.phase != "FINISHED" and not state.timer_running:
                    state.timer_running = True
            elif e.key == pygame.K_ESCAPE:
                if state.phase != "FINISHED":
                    state.timer_running = not state.timer_running
            elif e.key == pygame.K_F10:
                pygame.quit()
                sys.exit()

    for joy in _joysticks[:1]:
        jid = joy.get_id()
        for e in events:
            if e.type == pygame.JOYBUTTONDOWN and e.joy == jid:
                if e.button == 6:  # Back / Select
                    reset_requested = True
                elif e.button == 7:  # Start
                    if state.phase != "FINISHED" and not state.timer_running:
                        state.timer_running = True
                    elif state.phase != "FINISHED" and state.timer_running:
                        state.timer_running = False

    if reset_requested:
        return True

    # Frozen when timer not running
    if not state.timer_running:
        state.intake_active = False
        return

    # Frozen when match is over
    if state.phase == "FINISHED":
        state.intake_active = False
        return

    r = state.robot
    r.vx = 0.0
    r.vy = 0.0

    if r.drive_mode == "field":
        _handle_field_drive(r, keys, dt)
    else:
        _handle_robot_drive(r, keys, dt)

    def in_front(ax, ay):
        """Check if (ax, ay) is within the robot's front pickup cone."""
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

    for e in events:
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_q:
                _launch_held(state, r)
            elif e.key == pygame.K_r:
                r.drive_mode = "robot" if r.drive_mode == "field" else "field"
            elif e.key == pygame.K_t:
                _toggle_gate(state, r)
            elif e.key == pygame.K_e:
                state.intake_active = not state.intake_active

    if state.intake_active:
        _try_pickup(state, r, in_front)

    for joy in _joysticks[:1]:
        _handle_gamepad(state, r, joy, events, dt, in_front)


def _handle_field_drive(r, keys, dt):
    """Process WASD movement in field-oriented mode."""
    dx, dy = 0, 0
    if keys[pygame.K_w]:
        dy = -1
    if keys[pygame.K_s]:
        dy = 1
    if keys[pygame.K_a]:
        dx = -1
    if keys[pygame.K_d]:
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
    if keys[pygame.K_LEFT]:
        rot -= 1
    if keys[pygame.K_RIGHT]:
        rot += 1
    if rot != 0:
        r.angle += rot * math.radians(CONFIG["rotation_speed"]) * dt


def _handle_robot_drive(r, keys, dt):
    """Process WASD movement in robot-oriented mode."""
    fx = math.sin(r.angle)
    fy = -math.cos(r.angle)
    sx = math.cos(r.angle)
    sy = math.sin(r.angle)
    if keys[pygame.K_w]:
        r.vx += fx * r.speed
        r.vy += fy * r.speed
    if keys[pygame.K_s]:
        r.vx -= fx * r.speed
        r.vy -= fy * r.speed
    if keys[pygame.K_a]:
        r.vx -= sx * r.speed
        r.vy -= sy * r.speed
    if keys[pygame.K_d]:
        r.vx += sx * r.speed
        r.vy += sy * r.speed
    rot = 0.0
    if keys[pygame.K_LEFT]:
        rot -= 1
    if keys[pygame.K_RIGHT]:
        rot += 1
    if rot != 0:
        r.angle += rot * math.radians(CONFIG["rotation_speed"]) * dt
    if r.vx != 0 or r.vy != 0:
        r.x += r.vx * dt
        r.y += r.vy * dt
        r.x = clamp(r.x, FX, FX + FS)
        r.y = clamp(r.y, FY, FY + FS)


def _launch_held(state, r):
    """Launch all held artifacts toward the goal."""
    if not r.holding:
        return
    from_zone = state.in_launch_zone(r.x, r.y)
    full = len(r.holding) == CONFIG["max_hold"]
    gr = state.goal_rect()
    held = list(r.holding)
    r.holding.clear()
    for a in held:
        ox = random.uniform(-6, 6)
        oy = random.uniform(-6, 6)
        state.flying.append(FlyingArtifact(
            r.x + ox, r.y + oy, gr.centerx, gr.centery, a.color,
            scoring=from_zone, full_set=full
        ))


def _toggle_gate(state, r):
    """Toggle the gate open if robot is close enough."""
    gt = state.gate_rect()
    if dist((r.x, r.y), (gt.centerx, gt.centery)) < CONFIG["gate_range"]:
        if not state.team.gate_open:
            state.team.gate_open = True
            state.team.gate_timer = CONFIG["gate_open_duration"]
            cleared = state.team.clear_ramp()
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
    lt = joy.get_axis(4) > 0.5 if joy.get_numaxes() > 4 else 0
    rt = joy.get_axis(5) > 0.5 if joy.get_numaxes() > 5 else 0
    jid = joy.get_id()
    prev_lt = _trigger_cooldown.get((jid, "prev_lt"), 0)
    if lt and not prev_lt:
        state.intake_active = not state.intake_active
    _trigger_cooldown[(jid, "prev_lt")] = int(lt)
    cd_rt = _trigger_cooldown.get((jid, "rt"), 0.0)
    if state.intake_active:
        _try_pickup(state, r, in_front)
    if rt and cd_rt <= 0:
        _launch_held(state, r)
        _trigger_cooldown[(jid, "rt")] = 0.25
    _trigger_cooldown[(jid, "rt")] = max(0, _trigger_cooldown.get((jid, "rt"), 0) - dt)

    for e in events:
        if e.type == pygame.JOYBUTTONDOWN and e.joy == jid:
            if e.button == 3:
                r.drive_mode = "robot" if r.drive_mode == "field" else "field"
            elif e.button == 2:
                _toggle_gate(state, r)

