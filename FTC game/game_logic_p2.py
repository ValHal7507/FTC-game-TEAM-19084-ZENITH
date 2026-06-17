"""
FTC DECODE — P2 physics, scoring, and robot constraints (multi-player only).
"""

import math

import pygame
from config import CONFIG, FX, FY, FS, clamp


# ---------------------------------------------------------------------------
# Cached obstacle rects (kept in sync by game_logic.rebuild_obstacle_cache)
# ---------------------------------------------------------------------------
_cached_obs_rect = None
_cached_obs_rects = []


def _set_obs_rect(rect):
    """Update the cached obstacle rect. Called by game_logic.rebuild_obstacle_cache."""
    global _cached_obs_rect
    _cached_obs_rect = rect


def _set_obs_rects(rects):
    """Update the cached obstacle rect list. Called by game_logic.rebuild_obstacle_cache."""
    global _cached_obs_rects
    _cached_obs_rects = rects


def _get_obs_rect():
    """Return the cached obstacle rect, falling back to zero-size if unset."""
    if _cached_obs_rect is not None:
        return _cached_obs_rect
    return pygame.Rect(0, 0, 0, 0)


def _get_obs_rects():
    """Return the cached list of obstacle rects."""
    return _cached_obs_rects


# ---------------------------------------------------------------------------
# Robot constraint
# ---------------------------------------------------------------------------
_CONSTRAIN_MAX_ITER = 8


def constrain_robot_r(state, robot):
    """Push the robot out of all obstacle rects."""
    sz = CONFIG["robot_size"]
    half = sz // 2
    obs_list = _get_obs_rects()

    for _ in range(_CONSTRAIN_MAX_ITER):
        resolved = True
        rob_rect = pygame.Rect(robot.x - half, robot.y - half, sz, sz)
        for obs in obs_list:
            if not rob_rect.colliderect(obs):
                continue
            resolved = False
            ol = rob_rect.right - obs.left
            o_r = obs.right - rob_rect.left
            ot = rob_rect.bottom - obs.top
            ob = obs.bottom - rob_rect.top
            if min(ol, o_r) < min(ot, ob):
                robot.x = obs.left - half if ol < o_r else obs.right + half
            else:
                robot.y = obs.top - half if ot < ob else obs.bottom + half
            rob_rect = pygame.Rect(robot.x - half, robot.y - half, sz, sz)
        if resolved:
            break


# ---------------------------------------------------------------------------
# Robot–robot collision
# ---------------------------------------------------------------------------
def constrain_robot_robot(state):
    """Push both robots apart if their 60×60 rects overlap."""
    if state.robot2 is None:
        return
    sz = CONFIG["robot_size"]
    half = sz // 2
    r1, r2 = state.robot, state.robot2
    for _ in range(_CONSTRAIN_MAX_ITER):
        r1_rect = pygame.Rect(r1.x - half, r1.y - half, sz, sz)
        r2_rect = pygame.Rect(r2.x - half, r2.y - half, sz, sz)
        if not r1_rect.colliderect(r2_rect):
            break
        ol = r1_rect.right - r2_rect.left
        o_r = r2_rect.right - r1_rect.left
        ot = r1_rect.bottom - r2_rect.top
        ob = r2_rect.bottom - r1_rect.top
        if min(ol, o_r) < min(ot, ob):
            if ol < o_r:
                push = ol / 2
                r1.x -= push
                r2.x += push
            else:
                push = o_r / 2
                r1.x += push
                r2.x -= push
        else:
            if ot < ob:
                push = ot / 2
                r1.y -= push
                r2.y += push
            else:
                push = ob / 2
                r1.y += push
                r2.y -= push
        r1.x = clamp(r1.x, FX + 30, FX + FS - 30)
        r1.y = clamp(r1.y, FY + 30, FY + FS - 30)
        r2.x = clamp(r2.x, FX + 30, FX + FS - 30)
        r2.y = clamp(r2.y, FY + 30, FY + FS - 30)


# ---------------------------------------------------------------------------
# Turret angle update (must run on main thread every frame)
# ---------------------------------------------------------------------------
def update_turret_angle_r(state, robot):
    """Snap turret angle to point at goal for an arbitrary robot."""
    if state.game_mode == "1v1" and state.robot2 is not None and robot is state.robot2:
        gr = state.goal_rect_p2()
    else:
        gr = state.goal_rect()
    gx = gr.centerx - robot.x
    gy = gr.centery - robot.y
    target = math.atan2(gx, -gy)
    current = robot.turret_angle
    diff = (target - current + math.pi) % (2 * math.pi) - math.pi
    robot.turret_angle = current + diff


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def score_pattern2(state):
    """Score pattern matching for P2: each ramp slot matching motif gets +2 points."""
    pts = 0
    motif = state.motif
    ramp = state.team2.ramp
    for i in range(CONFIG["ramp_slots"]):
        if ramp[i] is not None and ramp[i] == motif[i % 3]:
            pts += 2
    state.team2.pattern_pts = pts


def score_base2(state):
    """Parking score for P2 at match end, using base_rect2."""
    if state.park_status2 == "FULL":
        state.team2.base_pts = 10
    elif state.park_status2 == "PARTIAL":
        state.team2.base_pts = 5


# ---------------------------------------------------------------------------
# Intake heat management
# ---------------------------------------------------------------------------
def update_intake_heat_p2(state, dt):
    """Update P2 intake motor temperature (mirrors update_intake_heat for P2 fields)."""
    if state.intake_overheated2:
        state.intake_cooldown_timer2 -= dt
        state.intake_heat2 = max(0.0, state.intake_cooldown_timer2 / CONFIG["intake_cooldown_time"])
        if state.intake_cooldown_timer2 <= 0:
            state.intake_overheated2 = False
            state.intake_cooldown_timer2 = 0.0
            state.intake_heat2 = 0.0
        return
    if state.intake_active2:
        state.intake_heat2 += dt / CONFIG["intake_heat_time"]
        if state.intake_heat2 >= 1.0:
            state.intake_heat2 = 1.0
            state.intake_overheated2 = True
            state.intake_cooldown_timer2 = CONFIG["intake_cooldown_time"]
            state.intake_active2 = False
    elif state.intake_heat2 > 0:
        state.intake_heat2 -= dt / CONFIG["intake_cool_time"]
        state.intake_heat2 = max(0.0, state.intake_heat2)


# ---------------------------------------------------------------------------
# Park status
# ---------------------------------------------------------------------------
def update_park_status2(state):
    """Update P2 park status using base_rect2."""
    if state.robot2 is None:
        return
    r = state.robot2
    base = state.base_rect2()
    sz = CONFIG["robot_size"]
    half = sz // 2
    robot_rect = pygame.Rect(r.x - half, r.y - half, sz, sz)
    if base.contains(robot_rect):
        state.park_status2 = "FULL"
    elif base.colliderect(robot_rect):
        state.park_status2 = "PARTIAL"
    else:
        state.park_status2 = "NONE"
