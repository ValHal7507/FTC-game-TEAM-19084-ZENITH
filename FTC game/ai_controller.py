"""
FTC DECODE — AI controller for P2 (1v1 vs AI mode).
"""

import math
import random
import pygame
from config import CONFIG, FX, FY, FS, clamp
from input_handler import _launch_held, _toggle_gate, _try_pickup

# ── Difficulty profiles ───────────────────────────────────────────────────────

DIFFICULTIES = {
    "easy": {
        "speed_mult":            0.50,
        "aim_error":            15.0,
        "radius":                200,
        "reaction":             0.40,
        "parks":               False,
        "launch_hold_threshold":   3,
        "gate_range":             100,
        "safe_corridor":           80,
    },
    "medium": {
        "speed_mult":            0.85,
        "aim_error":             2.0,
        "radius":                350,
        "reaction":             0.08,
        "parks":                True,
        "launch_hold_threshold":   3,
        "gate_range":             100,
        "safe_corridor":           80,
    },
    "hard": {
        "speed_mult":            1.00,
        "aim_error":             0.0,
        "radius":                500,
        "reaction":             0.00,
        "parks":                True,
        "launch_hold_threshold":   3,
        "gate_range":             100,
        "safe_corridor":           80,
    },
}

# ── Module-level state ────────────────────────────────────────────────────────

_ai_state          = "COLLECT"
_reaction_timer    = 0.0
_difficulty        = "medium"
_aim_offset        = 0.0
_aim_refresh_timer = 0.0

# ── Unstuck state ──────────────────────────────────────────────────────────────

_pos_history       = []
_stuck_timer       = 0.0
_stuck             = False
_stuck_dir_idx     = 0
_stuck_dir_timer   = 0.0
_STUCK_THRESHOLD   = 0.8
_STUCK_MOVE_MIN    = 10.0
_STUCK_DIR_DUR     = 0.3
_STUCK_DIRS        = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (-1, 1), (1, -1), (-1, -1),
]

# ── Obstacle routing state ──────────────────────────────────────────────────────

_routing_side      = None
_routing_side_lock = 0.0
_CORNER_HYSTERESIS = 30.0
_CORNER_EXTRA      = 25.0


# ── Public API ────────────────────────────────────────────────────────────────

def set_difficulty(difficulty):
    global _difficulty, _ai_state, _reaction_timer
    global _aim_offset, _aim_refresh_timer
    global _stuck, _stuck_dir_idx, _stuck_dir_timer, _pos_history
    _difficulty = difficulty if difficulty in DIFFICULTIES else "medium"
    _ai_state = "COLLECT"
    _reaction_timer = 0.0
    _aim_offset = 0.0
    _aim_refresh_timer = 0.0
    _stuck = False
    _stuck_dir_idx = 0
    _stuck_dir_timer = 0.0
    _pos_history.clear()


def reset_ai():
    global _ai_state, _reaction_timer
    global _aim_offset, _aim_refresh_timer
    global _stuck, _stuck_dir_idx, _stuck_dir_timer, _pos_history
    global _routing_side, _routing_side_lock
    _ai_state = "COLLECT"
    _reaction_timer = 0.0
    _aim_offset = 0.0
    _aim_refresh_timer = 0.0
    _stuck = False
    _stuck_dir_idx = 0
    _stuck_dir_timer = 0.0
    _routing_side = None
    _routing_side_lock = 0.0
    _pos_history.clear()


def update_ai(state, dt):
    global _reaction_timer, _ai_state
    global _aim_offset, _aim_refresh_timer
    global _stuck, _stuck_dir_idx, _stuck_dir_timer, _pos_history

    r = state.robot2
    if r is None:
        return

    profile = DIFFICULTIES[_difficulty]

    # Guard — timer not running or match finished
    if not state.timer_running or state.phase == "FINISHED":
        state.intake_active2 = False
        _stop_robot(r)
        return

    # Overheat guard — intake blocked, robot still moves
    if state.intake_overheated2:
        state.intake_active2 = False

    # Aim offset refresh
    _aim_refresh_timer -= dt
    if _aim_refresh_timer <= 0:
        error = profile["aim_error"]
        if error > 0:
            _aim_offset = math.radians(random.uniform(-error, error))
        else:
            _aim_offset = 0.0
        _aim_refresh_timer = random.uniform(0.5, 1.5)

    # Always rotate toward target unless in PARK state during endgame
    if _ai_state == "PARK" and state.timer < 5.0:
        # Do not rotate during the final 5 seconds
        pass
    elif _ai_state == "COLLECT":
        nearest_art = state.nearest_artifact(r.x, r.y, profile["radius"])
        if nearest_art is not None:
            _rotate_toward(r, nearest_art.x, nearest_art.y, dt)
    elif _ai_state == "GATE":
        gt = state.gate_rect()
        _rotate_toward(r, gt.centerx, gt.centery, dt)

    # Reaction timer — gates FSM state transitions only
    _reaction_timer -= dt
    if _reaction_timer > 0:
        r.x += r.vx * dt
        r.y += r.vy * dt
        half = CONFIG["robot_size"] // 2
        r.x = clamp(r.x, FX + half, FX + FS - half)
        r.y = clamp(r.y, FY + half, FY + FS - half)
        return

    # ── Unstuck detection ──────────────────────────────────────────────────
    _pos_history.append((r.x, r.y, state.timer))
    if len(_pos_history) > 90:
        _pos_history.pop(0)

    recent = [p for p in _pos_history if state.timer - p[2] < _STUCK_THRESHOLD]
    if len(recent) >= 2:
        dx = max(p[0] for p in recent) - min(p[0] for p in recent)
        dy = max(p[1] for p in recent) - min(p[1] for p in recent)
        moved = math.hypot(dx, dy) > _STUCK_MOVE_MIN
    else:
        moved = True

    if not moved and not _stuck:
        _stuck = True
        _stuck_dir_idx = 0
        _stuck_dir_timer = 0.0

    if _stuck:
        if moved:
            _stuck = False
            _pos_history.clear()
        else:
            half = CONFIG["robot_size"] // 2
            g = state.goal_rect()
            depot = state.depot_rect()
            obs = pygame.Rect(g.left, g.top, g.w, depot.bottom - g.top)
            _stuck_dir_timer -= dt
            if _stuck_dir_timer <= 0:
                for _ in range(len(_STUCK_DIRS)):
                    _stuck_dir_idx = (_stuck_dir_idx + 1) % len(_STUCK_DIRS)
                    dx, dy = _STUCK_DIRS[_stuck_dir_idx]
                    test_x = r.x + dx * r.speed * 0.7 * _STUCK_DIR_DUR
                    test_y = r.y + dy * r.speed * 0.7 * _STUCK_DIR_DUR
                    test_rect = pygame.Rect(test_x - half, test_y - half,
                                            CONFIG["robot_size"], CONFIG["robot_size"])
                    if not test_rect.colliderect(obs):
                        break
                _stuck_dir_timer = _STUCK_DIR_DUR
            dx, dy = _STUCK_DIRS[_stuck_dir_idx]
            r.vx = dx * r.speed * 0.7
            r.vy = dy * r.speed * 0.7
            r.x += r.vx * dt
            r.y += r.vy * dt
            half = CONFIG["robot_size"] // 2
            r.x = clamp(r.x, FX + half, FX + FS - half)
            r.y = clamp(r.y, FY + half, FY + FS - half)
            return

    # Endgame override — force park in last 5 seconds
    if state.timer < 5.0 and _ai_state != "PARK":
        _ai_state = "PARK"
        _stop_robot(r)

    # Dispatch FSM
    if _ai_state == "COLLECT":
        _state_collect(state, r, dt, profile)
    elif _ai_state == "NAVIGATE":
        _state_navigate(state, r, dt, profile)
    elif _ai_state == "LAUNCH":
        _state_launch(state, r, dt, profile)
    elif _ai_state == "PARK":
        _state_park(state, r, dt, profile)
    elif _ai_state == "GATE":
        _state_gate(state, r, dt, profile)

    _reaction_timer = 0.01 if _ai_state == "GATE" else profile["reaction"]

    # Field boundary clamp — never leave the arena
    half = CONFIG["robot_size"] // 2
    r.x = clamp(r.x, FX + half, FX + FS - half)
    r.y = clamp(r.y, FY + half, FY + FS - half)


# ── FSM state functions ───────────────────────────────────────────────────────

def _state_collect(state, r, dt, profile):
    global _ai_state

    if len(r.holding) > 0 and state.in_launch_zone2(r.x, r.y):
        _launch_held(state, r, state.team2)
        _stop_robot(r)
        return

    # Transition: enough held → navigate to launch
    if len(r.holding) >= profile["launch_hold_threshold"]:
        _ai_state = "NAVIGATE"
        _stop_robot(r)
        state.intake_active2 = False
        return

    g = state.goal_rect()
    d_rect = state.depot_rect()
    obs = pygame.Rect(g.left, g.top, g.w, d_rect.bottom - g.top)

    nearest = state.nearest_artifact(r.x, r.y, profile["radius"])

    if nearest is None:
        nearest = state.nearest_artifact(r.x, r.y, 1500)

    if nearest is not None:
        tx, ty = nearest.x, nearest.y
        d = math.hypot(tx - r.x, ty - r.y)
        _move_toward(r, tx, ty, r.speed * profile["speed_mult"], dt, obs, profile)
        if d < CONFIG["ai_intake_start_distance"]:
            state.intake_active2 = not state.intake_overheated2
            if not state.intake_overheated2 and r.can_pickup() and _in_front_cone(r, tx, ty):
                _try_pickup(state, r, lambda ax, ay: _in_front_cone(r, ax, ay))
        else:
            state.intake_active2 = False
        return

    state.intake_active2 = False
    _stop_robot(r)
    if len(r.holding) >= 1:
        _ai_state = "NAVIGATE"
    elif any(s is not None for s in state.team2.ramp):
        _ai_state = "GATE"
    return


def _clamp_to_rect(px, py, rect):
    return clamp(px, rect.left, rect.right), clamp(py, rect.top, rect.bottom)



def _point_in_triangle(pt, v1, v2, v3):
    x, y = pt
    x1, y1 = v1
    x2, y2 = v2
    x3, y3 = v3
    d1 = (x - x2) * (y1 - y2) - (x1 - x2) * (y - y2)
    d2 = (x - x3) * (y2 - y3) - (x2 - x3) * (y - y3)
    d3 = (x - x1) * (y3 - y1) - (x3 - x1) * (y - y1)
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (has_neg and has_pos)


def _nearest_launch_point(state, r):
    g = state.goal_rect()
    d = state.depot_rect()
    obs = pygame.Rect(g.left, g.top, g.w, d.bottom - g.top)
    half = CONFIG["robot_size"] // 2
    sz = CONFIG["robot_size"]

    candidates = []

    br = state.base_rect2()
    candidates.append((br.centerx, br.centery))

    target_fy = 260
    target_y = FY + target_fy
    left = 100 + 160 * (target_fy / 300)
    right = 620 - 160 * (target_fy / 300)
    cx = (left + right) / 2 + FX
    candidates.append((cx, target_y))

    top, bl, br_pt = state.shooting_zone_triangle()
    if _point_in_triangle((r.x, r.y), top, bl, br_pt):
        candidates.append((r.x, r.y))
    else:
        cx = (top[0] + bl[0] + br_pt[0]) / 3
        cy = (top[1] + bl[1] + br_pt[1]) / 3
        candidates.append((cx, cy))

    upper_half = r.y < FY + FS // 2
    best, best_d = None, float('inf')
    for cx, cy in candidates:
        d = math.hypot(cx - r.x, cy - r.y)
        if upper_half and (cx, cy) == (br.centerx, br.centery):
            d *= 1.5
        if d < best_d:
            best_d = d
            best = (cx, cy)
    return best


def _state_navigate(state, r, dt, profile):
    global _ai_state

    if len(r.holding) == 0:
        _ai_state = "COLLECT"
        return

    state.intake_active2 = False

    g = state.goal_rect()
    d_rect = state.depot_rect()
    obs = pygame.Rect(g.left, g.top, g.w, d_rect.bottom - g.top)

    tx, ty = _nearest_launch_point(state, r)
    _rotate_toward(r, tx, ty, dt)
    _move_toward(r, tx, ty, r.speed * profile["speed_mult"], dt, obs, profile)

    if state.in_launch_zone2(r.x, r.y):
        _ai_state = "LAUNCH"
        _stop_robot(r)


def _state_launch(state, r, dt, profile):
    global _ai_state

    state.intake_active2 = False

    if not state.in_launch_zone2(r.x, r.y):
        _ai_state = "NAVIGATE"
        return

    if len(r.holding) > 0:
        _launch_held(state, r, state.team2)
        _ai_state = "COLLECT"
        _stop_robot(r)
        return

    _ai_state = "COLLECT"


def _state_park(state, r, dt, profile):
    global _ai_state

    state.intake_active2 = False

    g = state.goal_rect()
    d_rect = state.depot_rect()
    obs = pygame.Rect(g.left, g.top, g.w, d_rect.bottom - g.top)

    br = state.base_rect2()
    tx, ty = br.centerx, br.centery
    _rotate_toward(r, tx, ty, dt)
    _move_toward(r, tx, ty, r.speed * profile["speed_mult"], dt, obs, profile)

    if len(r.holding) > 0 and state.in_launch_zone2(r.x, r.y):
        _launch_held(state, r, state.team2)
        _stop_robot(r)
        return

    if getattr(state, "park_status2", None) == "FULL":
        _stop_robot(r)


def _state_gate(state, r, dt, profile):
    global _ai_state

    state.intake_active2 = False

    gt = state.gate_rect()
    gate_d = math.hypot(gt.centerx - r.x, gt.centery - r.y)

    ai_gate_range = profile.get("gate_range", CONFIG["gate_range"])

    if gate_d < ai_gate_range:
        if not state.team2.gate_open:
            _toggle_gate(state, r, override_range=ai_gate_range)
        _ai_state = "COLLECT"
        _stop_robot(r)
        return

    half = CONFIG["robot_size"] // 2
    depot = state.depot_rect()
    g = state.goal_rect()
    obs = pygame.Rect(g.left, g.top, g.w, depot.bottom - g.top)

    # Approach safely from the right side of the obstacle, slightly further out
    approach_x = obs.right + half + 20
    approach_y = gt.centery

    # Prevent avoidance logic from fighting the approach if we are already safely on the right side
    active_obs = None if r.x > obs.right else obs

    # handles rotation natively, so the robot will now look at the gate while driving to it!
    _move_toward(r, approach_x, approach_y, r.speed * profile["speed_mult"], dt, active_obs)

    gate_d = math.hypot(gt.centerx - r.x, gt.centery - r.y)
    if gate_d < ai_gate_range:
        if not state.team2.gate_open:
            _toggle_gate(state, r, override_range=ai_gate_range)
        _ai_state = "COLLECT"
        _stop_robot(r)


# ── Movement utilities ────────────────────────────────────────────────────────

def _stop_robot(r):
    r.vx = 0.0
    r.vy = 0.0


def _line_crosses_rect(x1, y1, x2, y2, rect):
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return rect.collidepoint(x1, y1)
    t_min, t_max = 0.0, 1.0
    if dx != 0:
        t1 = (rect.left - x1) / dx
        t2 = (rect.right - x1) / dx
        if t1 > t2:
            t1, t2 = t2, t1
        t_min = max(t_min, t1)
        t_max = min(t_max, t2)
    else:
        if x1 < rect.left or x1 > rect.right:
            return False
    if dy != 0:
        t1 = (rect.top - y1) / dy
        t2 = (rect.bottom - y1) / dy
        if t1 > t2:
            t1, t2 = t2, t1
        t_min = max(t_min, t1)
        t_max = min(t_max, t2)
    else:
        if y1 < rect.top or y1 > rect.bottom:
            return False
    return t_min <= t_max


def _move_toward(r, tx, ty, speed, dt, obs_rect=None, profile=None):
    dx = tx - r.x
    dy = ty - r.y
    d = math.hypot(dx, dy)

    if d < 8.0:
        r.vx = 0.0
        r.vy = 0.0
        return True

    move = speed * dt
    if move >= d:
        r.x = tx
        r.y = ty
        r.vx = 0.0
        r.vy = 0.0
        return True

    # Default direct velocity toward target
    r.vx = (dx / d) * speed
    r.vy = (dy / d) * speed

    if obs_rect is not None:
        half = CONFIG["robot_size"] // 2

        # hard_obs: The absolute physical boundary where the robot's CENTER cannot go
        hard_obs = pygame.Rect(obs_rect.left - half, obs_rect.top - half,
                               obs_rect.w + 2 * half, obs_rect.h + 2 * half)

        # 1. Clamp target destination if it sits inside the wall's radius.
        ctx, cty = tx, ty
        if hard_obs.collidepoint(tx, ty):
            dl = tx - hard_obs.left
            dr = hard_obs.right - tx
            dt_top = ty - hard_obs.top
            db = hard_obs.bottom - ty
            min_d = min(dl, dr, dt_top, db)

            if min_d == dl:
                ctx = hard_obs.left
            elif min_d == dr:
                ctx = hard_obs.right
            elif min_d == dt_top:
                cty = hard_obs.top
            else:
                cty = hard_obs.bottom

        # 2. Check if the direct line to the clamped target clips the obstacle.
        # Shrink by 2px to allow sliding exactly on the edge without panicking.
        check_obs = pygame.Rect(hard_obs.left + 2, hard_obs.top + 2,
                                hard_obs.w - 4, hard_obs.h - 4)

        override_velocity = False
        safe_x, safe_y = ctx, cty

        if _line_crosses_rect(r.x, r.y, ctx, cty, check_obs):
            # We are going to snag the corner. Force an orthogonal route.
            clearance = 20
            safe_left = hard_obs.left - clearance
            safe_right = hard_obs.right + clearance
            safe_bottom = hard_obs.bottom + clearance

            target_is_left = ctx < obs_rect.centerx
            robot_is_left = r.x < obs_rect.centerx

            if target_is_left != robot_is_left:
                # CROSSING SIDES: The top is blocked by the arena wall.
                # We MUST route in a U-Shape underneath the obstacle.
                if r.y < safe_bottom - 5:
                    # Move straight down your current side until clear of the bottom
                    safe_x = safe_left if robot_is_left else safe_right
                    safe_y = safe_bottom
                    override_velocity = True
                else:
                    # Clear of the bottom! Now cross horizontally to the target's side
                    safe_x = safe_left if target_is_left else safe_right
                    safe_y = safe_bottom
                    override_velocity = True
            else:
                # SAME SIDE: We are just snagging the corner while reaching for a close artifact.
                if r.y < safe_bottom - 5 and cty > safe_bottom:
                    # Moving vertically down past the corner
                    safe_x = safe_left if robot_is_left else safe_right
                    safe_y = safe_bottom
                    override_velocity = True
                elif r.y > safe_bottom - 5 and cty < safe_bottom:
                    # Moving vertically up from below the corner
                    safe_x = safe_left if robot_is_left else safe_right
                    safe_y = safe_bottom
                    override_velocity = True
                else:
                    # Both are above safe_bottom, or both are below safe_bottom.
                    # Pull away from the wall horizontally to stop scraping.
                    safe_x = safe_left if robot_is_left else safe_right
                    safe_y = r.y
                    override_velocity = True

        # Apply override velocity if we are navigating around a corner
        if override_velocity:
            sdx = safe_x - r.x
            sdy = safe_y - r.y
            sd = math.hypot(sdx, sdy)
            # Only override if we aren't already at the safe waypoint
            if sd > 2.0:
                r.vx = (sdx / sd) * speed
                r.vy = (sdy / sd) * speed

    r.x += r.vx * dt
    r.y += r.vy * dt
    return False


def _rotate_toward(r, tx, ty, dt):
    target_angle = math.atan2(tx - r.x, -(ty - r.y)) + _aim_offset
    diff = (target_angle - r.angle + math.pi) % (2 * math.pi) - math.pi
    if abs(diff) < 1e-4:
        return True
    max_rot = math.radians(CONFIG["rotation_speed"]) * 2.5 * dt
    t = min(1.0, max_rot / abs(diff))
    r.angle += diff * t
    return abs(diff) < math.radians(20)


def _in_front_cone(r, tx, ty):
    target_angle = math.atan2(tx - r.x, -(ty - r.y))
    diff = abs((target_angle - r.angle + math.pi) % (2 * math.pi) - math.pi)
    return diff < math.radians(CONFIG["pickup_cone_angle"] / 2)