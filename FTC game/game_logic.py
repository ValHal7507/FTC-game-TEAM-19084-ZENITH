"""
FTC DECODE — Game logic: timer, scoring, physics updates.
"""

import math
import threading

import pygame
from config import CONFIG, FX, FY, FS, clamp


# ---------------------------------------------------------------------------
# Physics-thread infrastructure
# ---------------------------------------------------------------------------
_physics_lock = threading.Lock()
_physics_running = False
_physics_thread = None

# Cached merged goal+depot obstacle rect — rebuilt on game reset, not per frame.
_cached_obs_rect = None


def rebuild_obstacle_cache(state):
    """Recompute the merged goal+depot obstacle rect. Call on game reset only."""
    global _cached_obs_rect
    g = state.goal_rect()
    d = state.depot_rect()
    _cached_obs_rect = pygame.Rect(g.left, g.top, g.w, d.bottom - g.top)


def _get_obs_rect():
    """Return the cached obstacle rect, falling back to compute if unset."""
    if _cached_obs_rect is not None:
        return _cached_obs_rect
    # Fallback (should not happen after proper init)
    g = pygame.Rect(0, 0, 0, 0)
    d = pygame.Rect(0, 0, 0, 0)
    return pygame.Rect(g.left, g.top, g.w, d.bottom - g.top)


# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------
def update_timer(state, dt):
    """Decrement the match timer and handle phase transitions."""
    if state.phase == "FINISHED":
        return
    if not state.timer_running:
        return
    state.timer -= dt
    if state.phase == "TELEOP" and state.timer <= CONFIG["endgame_time"]:
        state.phase = "ENDGAME"
    elif state.phase == "ENDGAME" and state.timer <= 0:
        score_pattern(state)
        score_base(state)
        state.phase = "FINISHED"
        state.timer = 0


def score_pattern(state):
    """Score pattern matching: each ramp slot matching motif gets +2 points."""
    pts = 0
    motif = state.motif
    ramp = state.team.ramp
    for i in range(CONFIG["ramp_slots"]):
        if ramp[i] is not None and ramp[i] == motif[i % 3]:
            pts += 2
    state.team.pattern_pts = pts


def score_base(state):
    """Score base return: fully inside = +10, partial overlap = +5."""
    r = state.robot
    br = state.base_rect()
    sz = CONFIG["robot_size"]
    half = sz // 2
    rob_r = pygame.Rect(r.x - half, r.y - half, sz, sz)
    if br.contains(rob_r):
        state.team.base_pts = 10
    elif br.colliderect(rob_r):
        state.team.base_pts = 5


# ---------------------------------------------------------------------------
# Artifact physics (hot loop — heavily optimised)
# ---------------------------------------------------------------------------
_CONSTRAIN_MAX_ITER = 8


def update_artifact_physics(state, dt):
    """Update 2D physics for all field artifacts."""
    # --- local aliases for CONFIG values (avoid repeated dict lookups) ---
    R = CONFIG["artifact_radius"]
    field_left = FX + R
    field_right = FX + FS - R
    field_top = FY + R
    field_bottom = FY + FS - R
    friction = CONFIG["artifact_friction"] ** dt
    wall_bounce = CONFIG["artifact_bounce"]
    robot_bounce = CONFIG["artifact_robot_bounce"]
    artifact_bounce = CONFIG["artifact_artifact_bounce"]
    min_speed = CONFIG["artifact_min_speed"]
    push_force = CONFIG["robot_push_force"]
    rob_r = CONFIG["robot_size"] / 2
    min_d_robot = rob_r + R
    skip_d_sq = (min_d_robot + 20) ** 2
    min_d_art = 2 * R
    min_d_art_sq = min_d_art * min_d_art

    robot = state.robot
    robot_x = robot.x
    robot_y = robot.y
    robot_vx = robot.vx
    robot_vy = robot.vy

    obs_rect = _get_obs_rect()

    active = [a for a in state.artifacts if a.on_field and a.respawn_timer <= 0 and a not in robot.holding]

    # --- Phase 1: integrate, friction, walls, obstacle ---
    for a in active:
        ax = a.x
        ay = a.y
        avx = a.vx
        avy = a.vy

        # Early-exit: skip stationary artifacts far from robot
        if avx == 0.0 and avy == 0.0:
            rdx = ax - robot_x
            rdy = ay - robot_y
            if rdx * rdx + rdy * rdy > skip_d_sq:
                continue

        ax += avx * dt
        ay += avy * dt

        avx *= friction
        avy *= friction

        speed = math.hypot(avx, avy)
        if speed < min_speed:
            avx = 0.0
            avy = 0.0

        # Field wall bounce
        if ax < field_left:
            ax = field_left
            avx = abs(avx) * wall_bounce
        elif ax > field_right:
            ax = field_right
            avx = -abs(avx) * wall_bounce

        if ay < field_top:
            ay = field_top
            avy = abs(avy) * wall_bounce
        elif ay > field_bottom:
            ay = field_bottom
            avy = -abs(avy) * wall_bounce

        # Goal+depot obstacle (cached rect)
        rect = obs_rect
        if rect.collidepoint(ax, ay):
            dl = ax - rect.left
            dr = rect.right - ax
            dt_val = ay - rect.top
            db = rect.bottom - ay
            mind = min(dl, dr, dt_val, db)
            if mind == dl:
                ax = rect.left - R
                avx = -abs(avx) * wall_bounce
            elif mind == dr:
                ax = rect.right + R
                avx = abs(avx) * wall_bounce
            elif mind == dt_val:
                ay = rect.top - R
                avy = -abs(avy) * wall_bounce
            else:
                ay = rect.bottom + R
                avy = abs(avy) * wall_bounce
        else:
            cx = clamp(ax, rect.left, rect.right)
            cy = clamp(ay, rect.top, rect.bottom)
            gdx = ax - cx
            gdy = ay - cy
            gdist_sq = gdx * gdx + gdy * gdy
            if gdist_sq < R * R and gdist_sq > 0:
                gd = math.sqrt(gdist_sq)
                gnx, gny = gdx / gd, gdy / gd
                overlap = R - gd
                ax += gnx * overlap
                ay += gny * overlap
                gdot = avx * gnx + avy * gny
                if gdot < 0:
                    avx -= (1 + wall_bounce) * gdot * gnx
                    avy -= (1 + wall_bounce) * gdot * gny

        a.x = ax
        a.y = ay
        a.vx = avx
        a.vy = avy

    # --- Phase 2: artifact–artifact collisions ---
    n = len(active)
    for i in range(n):
        ai = active[i]
        ai_vx = ai.vx
        ai_vy = ai.vy
        ai_stationary = (ai_vx == 0.0 and ai_vy == 0.0)
        ai_x = ai.x
        ai_y = ai.y
        for j in range(i + 1, n):
            aj = active[j]
            # Skip if BOTH artifacts are stationary
            if ai_stationary and aj.vx == 0.0 and aj.vy == 0.0:
                continue
            dx = aj.x - ai_x
            dy = aj.y - ai_y
            dist_sq = dx * dx + dy * dy
            if dist_sq < min_d_art_sq and dist_sq > 0.0001:
                d = math.sqrt(dist_sq)
                nx, ny = dx / d, dy / d
                overlap = min_d_art - d
                half_ol = overlap * 0.5
                ai.x -= nx * half_ol
                ai.y -= ny * half_ol
                aj.x += nx * half_ol
                aj.y += ny * half_ol
                dvx = aj.vx - ai.vx
                dvy = aj.vy - ai.vy
                dot = dvx * nx + dvy * ny
                if dot < 0:
                    e = artifact_bounce
                    j_imp = -(1 + e) * dot * 0.5
                    ai.vx -= j_imp * nx
                    ai.vy -= j_imp * ny
                    aj.vx += j_imp * nx
                    aj.vy += j_imp * ny

    # --- Phase 3: robot–artifact push ---
    for a in active:
        rdx = a.x - robot_x
        rdy = a.y - robot_y
        rdist_sq = rdx * rdx + rdy * rdy
        if rdist_sq < min_d_robot * min_d_robot and rdist_sq > 0.0001:
            rdist = math.sqrt(rdist_sq)
            nx, ny = rdx / rdist, rdy / rdist
            overlap = min_d_robot - rdist
            a.x += nx * overlap
            a.y += ny * overlap
            relative_vx = a.vx - robot_vx
            relative_vy = a.vy - robot_vy
            dot = relative_vx * nx + relative_vy * ny
            if dot < 0:
                e = robot_bounce
                imp = -(1 + e) * dot
                a.vx += imp * nx
                a.vy += imp * ny
            spd = math.hypot(a.vx, a.vy)
            if spd < push_force * 0.1:
                a.vx += nx * push_force * dt
                a.vy += ny * push_force * dt


# ---------------------------------------------------------------------------
# Robot constraint
# ---------------------------------------------------------------------------
def constrain_robot(state):
    """Push the robot out of the goal+depot obstacle rect."""
    r = state.robot
    sz = CONFIG["robot_size"]
    half = sz // 2
    obs = _get_obs_rect()

    for _ in range(_CONSTRAIN_MAX_ITER):
        resolved = True
        rob_rect = pygame.Rect(r.x - half, r.y - half, sz, sz)
        if not rob_rect.colliderect(obs):
            break
        resolved = False
        ol = rob_rect.right - obs.left
        o_r = obs.right - rob_rect.left
        ot = rob_rect.bottom - obs.top
        ob = obs.bottom - rob_rect.top
        if min(ol, o_r) < min(ot, ob):
            r.x = obs.left - half if ol < o_r else obs.right + half
        else:
            r.y = obs.top - half if ot < ob else obs.bottom + half
        if resolved:
            break


# ---------------------------------------------------------------------------
# Turret angle update (must run on main thread every frame)
# ---------------------------------------------------------------------------
def update_turret_angle(state):
    """Snap turret angle to point at goal. Called on the main thread each frame."""
    gr = state.goal_rect()
    gx = gr.centerx - state.robot.x
    gy = gr.centery - state.robot.y
    target = math.atan2(gx, -gy)
    current = state.robot.turret_angle
    diff = (target - current + math.pi) % (2 * math.pi) - math.pi
    state.robot.turret_angle = current + diff


# ---------------------------------------------------------------------------
# Flying artifacts + gate timer (runs on physics thread under lock)
# ---------------------------------------------------------------------------
def _update_flying_and_gate(state, dt):
    """Update flying artifact positions and gate auto-close timer."""
    for fa in state.flying[:]:
        if not fa.active:
            continue
        dx, dy = fa.target_x - fa.x, fa.target_y - fa.y
        d = math.hypot(dx, dy)
        if d < 8:
            fa.active = False
            if fa.scoring:
                in_slot = state.team.add_to_ramp(fa.color)
                if in_slot:
                    state.team.classified += 1
            else:
                placed = False
                ramp = state.team.ramp
                for i in range(CONFIG["ramp_slots"]):
                    if ramp[i] is None:
                        ramp[i] = fa.color
                        placed = True
                        break
                if not placed:
                    state.team.overflow_held.append(fa.color)
        else:
            move = fa.speed * dt
            fa.x += (dx / d) * move
            fa.y += (dy / d) * move
            fa.trail.append((fa.x, fa.y))
            if len(fa.trail) > fa.MAX_TRAIL:
                fa.trail.pop(0)
    state.flying = [f for f in state.flying if f.active]

    if state.team.gate_open:
        state.team.gate_timer -= dt
        if state.team.gate_timer <= 0:
            state.team.gate_open = False
            state.team.gate_timer = 0.0


# ---------------------------------------------------------------------------
# Intake heat management
# ---------------------------------------------------------------------------
def update_intake_heat(state, dt):
    """Update intake motor temperature. Heats when running, cools when idle."""
    if state.intake_overheated:
        state.intake_cooldown_timer -= dt
        state.intake_heat = max(0.0, state.intake_cooldown_timer / CONFIG["intake_cooldown_time"])
        if state.intake_cooldown_timer <= 0:
            state.intake_overheated = False
            state.intake_cooldown_timer = 0.0
            state.intake_heat = 0.0
        return
    if state.intake_active:
        state.intake_heat += dt / CONFIG["intake_heat_time"]
        if state.intake_heat >= 1.0:
            state.intake_heat = 1.0
            state.intake_overheated = True
            state.intake_cooldown_timer = CONFIG["intake_cooldown_time"]
            state.intake_active = False
    elif state.intake_heat > 0:
        state.intake_heat -= dt / CONFIG["intake_cool_time"]
        state.intake_heat = max(0.0, state.intake_heat)


# ---------------------------------------------------------------------------
# Combined physics update (called from physics thread)
# ---------------------------------------------------------------------------
def update_physics(state, dt):
    """Run one frame of physics simulation (called under _physics_lock)."""
    update_park_status(state)
    if not state.timer_running:
        return
    constrain_robot(state)
    update_intake_heat(state, dt)
    update_artifact_physics(state, dt)
    _update_flying_and_gate(state, dt)


# ---------------------------------------------------------------------------
# Park status
# ---------------------------------------------------------------------------
def get_park_status(state):
    """Return NONE, PARTIAL, or FULL based on robot position in base."""
    r = state.robot
    br = state.base_rect()
    sz = CONFIG["robot_size"]
    half = sz // 2
    rob_r = pygame.Rect(r.x - half, r.y - half, sz, sz)
    if br.contains(rob_r):
        return "FULL"
    elif br.colliderect(rob_r):
        return "PARTIAL"
    return "NONE"


def update_park_status(state):
    """Update the park_status field on state."""
    state.park_status = get_park_status(state)


# ---------------------------------------------------------------------------
# Physics background thread
# ---------------------------------------------------------------------------
def _physics_thread_target(state):
    """Background physics loop. Runs until _physics_running is False."""
    global _physics_running
    phys_clock = pygame.time.Clock()
    while _physics_running:
        dt = min(phys_clock.tick(60) / 1000.0, 0.05)
        with _physics_lock:
            update_physics(state, dt)


def start_physics_thread(state):
    """Spawn the background physics thread and return it."""
    global _physics_running, _physics_thread
    _physics_running = True
    _physics_thread = threading.Thread(
        target=_physics_thread_target, args=(state,), daemon=True
    )
    _physics_thread.start()
    return _physics_thread


def stop_physics_thread():
    """Signal the physics thread to stop and wait for it."""
    global _physics_running, _physics_thread
    _physics_running = False
    if _physics_thread is not None:
        _physics_thread.join(timeout=2.0)
        _physics_thread = None
