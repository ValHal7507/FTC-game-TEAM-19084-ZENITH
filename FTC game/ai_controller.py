"""
FTC DECODE — AI controller for P2 (vs AI mode only).
"""

import math
from config import CONFIG, FX, FY, FS, clamp
from input_handler import launch_held, toggle_gate, _try_pickup


def update_ai(state, dt):
    """Simple rule-based AI controller for P2 (robot2)."""
    r = state.robot2
    if r is None:
        return

    r.vx = 0.0
    r.vy = 0.0

    # PRIORITY 1 — Overheat guard
    if state.intake_overheated2:
        state.intake_active2 = False

    # PRIORITY 2 — Collect artifacts if holding < 3 and one is nearby
    if r.can_pickup():
        nearest = state.nearest_artifact(r.x, r.y, 300)
        if nearest is not None:
            state.intake_active2 = True
            dx = nearest.x - r.x
            dy = nearest.y - r.y
            d = math.hypot(dx, dy)
            if d > 0:
                speed = CONFIG["robot_speed"]
                r.vx = (dx / d) * speed
                r.vy = (dy / d) * speed
                r.angle = math.atan2(dx, -dy)
                r.x += r.vx * dt
                r.y += r.vy * dt
                r.x = clamp(r.x, FX, FX + FS)
                r.y = clamp(r.y, FY, FY + FS)

            def in_front(ax, ay):
                lfx = math.sin(r.angle)
                lfy = -math.cos(r.angle)
                ddx = ax - r.x
                ddy = ay - r.y
                dd = math.hypot(ddx, ddy)
                if dd == 0:
                    return False
                dot = (ddx / dd) * lfx + (ddy / dd) * lfy
                half_cone = math.radians(CONFIG["pickup_cone_angle"] / 2)
                return dot > math.cos(half_cone)

            _try_pickup(state, r, in_front)
            return

    # PRIORITY 3 — Launch if holding artifacts and in launch zone
    if len(r.holding) >= 1 and state.in_launch_zone2(r.x, r.y):
        launch_held(state, r, team=state.team2)
        if not state.team2.gate_open and any(s is not None for s in state.team2.ramp):
            toggle_gate(state, r)
        return

    # PRIORITY 4 — Drive toward launch zone if holding artifacts
    if len(r.holding) >= 1:
        target = state.loading_rect2()
        tx, ty = target.centerx, target.centery
        dx = tx - r.x
        dy = ty - r.y
        d = math.hypot(dx, dy)
        if d > 0:
            speed = CONFIG["robot_speed"]
            r.vx = (dx / d) * speed
            r.vy = (dy / d) * speed
            r.angle = math.atan2(dx, -dy)
            r.x += r.vx * dt
            r.y += r.vy * dt
            r.x = clamp(r.x, FX, FX + FS)
            r.y = clamp(r.y, FY, FY + FS)
        return

    # PRIORITY 5 — Idle: keep trying to intake
    state.intake_active2 = True
    r.vx = 0.0
    r.vy = 0.0
