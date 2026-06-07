"""
FTC DECODE — All drawing and rendering functions.
"""

import math
from collections import deque

import pygame
from config import (
    CONFIG, FX, FY, FS, HX, HW, W, H,
    BLACK, WHITE, GRAY, DARK_GRAY, BG_DARK, CHARCOAL, SOFT_WHITE,
    ROBOT_PURPLE, ROBOT_DARK, GLOW_PURPLE,
    GOAL_GOLD, GOAL_DARK, RAMP_DARK, SLOT_EMPTY, SLOT_BORDER,
    GATE_COLOR, GATE_OPEN_COLOR,
    PURPLE, GREEN, GOLD, ORANGE, RED_ACCENT, PARK_GREEN,
    lerp,
)

# ============================================================
# FONTS
# ============================================================
f_small = f_tiny = f_micro = f_hud = f_hud_s = f_timer = f_huge = None
_fonts_inited = False


def _make_font(name, size):
    """Create a system font with fallback to default."""
    try:
        return pygame.font.SysFont(name, size)
    except Exception:
        return pygame.font.Font(None, size)


def init_drawing():
    """Initialize all fonts. Call once after pygame.init()."""
    global f_small, f_tiny, f_micro, f_hud, f_hud_s, f_timer, f_huge, _fonts_inited
    if _fonts_inited:
        return
    name = "Segoe UI"
    f_micro = _make_font(name, 14)
    f_tiny = _make_font(name, 17)
    f_small = _make_font(name, 21)
    f_hud_s = _make_font(name, 26)
    f_hud = _make_font(name, 34)
    f_timer = _make_font(name, 56)
    f_huge = _make_font(name, 68)
    _fonts_inited = True


# Backward-compatible alias
init_fonts = init_drawing


# ============================================================
# HELPERS
# ============================================================
def _round_rect(surf, rect, color, r=6, width=0):
    """Draw a rounded rectangle."""
    pygame.draw.rect(surf, color, rect, width, border_radius=r)


# ============================================================
# FIELD — STATIC CACHE
# ============================================================
_field_surface = None
_field_cache_park = None


def _build_field_surface():
    """Render all static field elements onto a cached surface."""
    global _field_surface, _field_cache_park
    surf = pygame.Surface((W, H))

    rect = pygame.Rect(FX, FY, FS, FS)
    _round_rect(surf, rect, CHARCOAL, 4)
    pygame.draw.rect(surf, GRAY, rect, 2, border_radius=4)

    for i in range(1, 6):
        x = FX + i * (FS // 6)
        pygame.draw.line(surf, DARK_GRAY, (x, FY), (x, FY + FS), 1)
        y = FY + i * (FS // 6)
        pygame.draw.line(surf, DARK_GRAY, (FX, y), (FX + FS, y), 1)

    lr = pygame.Rect(FX, FY, CONFIG["loading_zone_size"], CONFIG["loading_zone_size"])
    s = pygame.Surface((lr.w, lr.h), pygame.SRCALPHA)
    s.fill((60, 60, 70, 60))
    surf.blit(s, (lr.x, lr.y))
    pygame.draw.rect(surf, SOFT_WHITE, lr, 2, border_radius=3)
    lbl = f_tiny.render("LOAD ZONE", True, SOFT_WHITE)
    surf.blit(lbl, (lr.centerx - lbl.get_width() // 2, lr.centery - lbl.get_height() // 2))

    br = pygame.Rect(FX + FS // 2 - CONFIG["base_size"] // 2,
                     FY + FS - CONFIG["base_size"], CONFIG["base_size"], CONFIG["base_size"])
    pygame.draw.rect(surf, ROBOT_PURPLE, br, 2, border_radius=3)
    lbl = f_small.render("BASE", True, ROBOT_PURPLE)
    surf.blit(lbl, (br.centerx - lbl.get_width() // 2, br.centery - lbl.get_height() // 2))

    gr = pygame.Rect(FX + FS // 2 - CONFIG["goal_w"] // 2, FY + 12,
                     CONFIG["goal_w"], CONFIG["goal_h"])
    pygame.draw.rect(surf, GOAL_DARK, gr, border_radius=4)
    pygame.draw.rect(surf, GOAL_GOLD, gr, 2, border_radius=4)
    lbl = f_small.render("GOAL", True, GOAL_GOLD)
    surf.blit(lbl, (gr.centerx - lbl.get_width() // 2, gr.centery - lbl.get_height() // 2))

    rr = pygame.Rect(gr.x, gr.bottom + 5, gr.w, CONFIG["ramp_h"])
    pygame.draw.rect(surf, RAMP_DARK, rr, border_radius=2)
    pygame.draw.rect(surf, GRAY, rr, 1, border_radius=2)

    gt = pygame.Rect(rr.right - 18, rr.y, 18, rr.h)
    pygame.draw.rect(surf, GATE_COLOR, gt, border_radius=2)
    pygame.draw.rect(surf, WHITE, gt, 1, border_radius=2)
    lbl = f_tiny.render("GATE", True, GOLD)
    surf.blit(lbl, (gt.centerx - lbl.get_width() // 2, gt.y - 13))

    dr = pygame.Rect(gr.x, gr.bottom + 5 + CONFIG["ramp_h"] + 3, gr.w, CONFIG["depot_h"])
    pygame.draw.rect(surf, (40, 38, 35), dr, border_radius=2)
    pygame.draw.rect(surf, GRAY, dr, 1, border_radius=2)
    lbl = f_tiny.render("DEPOT", True, GRAY)
    surf.blit(lbl, (dr.centerx - lbl.get_width() // 2, dr.centery - lbl.get_height() // 2))

    cols = [FX + 300, FX + 400]
    rows = [FY + 280, FY + 360, FY + 440]
    labels = ["NEAR (GPP)", "MID (PGP)", "FAR (PPG)"]
    for ri, ry in enumerate(rows):
        for cx in cols:
            r = pygame.Rect(cx - 22, ry - 4, 44, 8)
            pygame.draw.rect(surf, SOFT_WHITE, r, border_radius=2)
        lbl = f_micro.render(labels[ri], True, GRAY)
        surf.blit(lbl, (cols[0] - 22, rows[ri] + 10))

    lz = pygame.Surface((FS, FS), pygame.SRCALPHA)
    pts = [(FX + 100, FY), (FX + FS - 100, FY), (FX + FS // 2, FY + 300)]
    pygame.draw.polygon(lz, (255, 255, 255, 20), [(p[0] - FX, p[1] - FY) for p in pts])
    surf.blit(lz, (FX, FY))
    pygame.draw.polygon(surf, SOFT_WHITE, pts, 1)

    _field_surface = surf
    _field_cache_park = None


def _invalidate_field_cache():
    """Force the field cache to rebuild on next draw."""
    global _field_surface, _field_cache_park
    _field_surface = None
    _field_cache_park = None


# ============================================================
# FIELD — DYNAMIC OVERLAY + DRAW
# ============================================================
def draw_field(screen, state):
    """Draw the field: cached static layer + dynamic per-frame elements."""
    global _field_surface, _field_cache_park

    if _field_surface is None:
        _build_field_surface()

    screen.blit(_field_surface, (0, 0))

    # --- Drive mode badge (always dynamic) ---
    mode = state.robot.drive_mode.upper()
    mc = GOLD if mode == "FIELD" else SOFT_WHITE
    lbl = f_tiny.render(f"DRIVE: {mode}", True, mc)
    pygame.draw.rect(screen, BG_DARK, (FX + 4, FY + 4, lbl.get_width() + 8, lbl.get_height() + 4), border_radius=3)
    screen.blit(lbl, (FX + 8, FY + 6))

    # --- Base zone park status ---
    br = state.base_rect()
    base_fill = pygame.Surface((br.w, br.h), pygame.SRCALPHA)
    base_fill.fill((ROBOT_PURPLE[0], ROBOT_PURPLE[1], ROBOT_PURPLE[2], 50))
    screen.blit(base_fill, (br.x, br.y))
    if state.park_status == "PARTIAL":
        t_ms = pygame.time.get_ticks()
        alpha = int(80 + 120 * (0.5 + 0.5 * math.sin(t_ms * 2 * math.pi / 1500)))
        pulse_s = pygame.Surface((br.w + 8, br.h + 8), pygame.SRCALPHA)
        pygame.draw.rect(pulse_s, (*GOAL_GOLD, alpha), (0, 0, br.w + 8, br.h + 8), 3, border_radius=4)
        screen.blit(pulse_s, (br.x - 4, br.y - 4))
    elif state.park_status == "FULL":
        glow_s = pygame.Surface((br.w, br.h), pygame.SRCALPHA)
        glow_s.fill((*PARK_GREEN, 60))
        screen.blit(glow_s, (br.x, br.y))
        pygame.draw.rect(screen, PARK_GREEN, br, 3, border_radius=3)

    # --- Ramp slot fill ---
    rr = state.ramp_rect()
    slot_w = (rr.w - 8) // CONFIG["ramp_slots"]
    for i in range(CONFIG["ramp_slots"]):
        sx = rr.x + 4 + i * slot_w
        sr = pygame.Rect(sx, rr.y + 1, slot_w - 1, rr.h - 2)
        if state.team.ramp[i] is not None:
            c = GREEN if state.team.ramp[i] == "G" else PURPLE
            pygame.draw.rect(screen, c, sr, border_radius=2)
        else:
            pygame.draw.rect(screen, SLOT_EMPTY, sr, border_radius=2)
        pygame.draw.rect(screen, SLOT_BORDER, sr, 1, border_radius=2)

    # --- Gate state ---
    gt = state.gate_rect()
    gc = GATE_OPEN_COLOR if state.team.gate_open else GATE_COLOR
    pygame.draw.rect(screen, gc, gt, border_radius=2)
    pygame.draw.rect(screen, WHITE, gt, 1, border_radius=2)
    gl = "OPEN" if state.team.gate_open else "GATE"
    gc2 = GATE_OPEN_COLOR if state.team.gate_open else GOLD
    lbl = f_tiny.render(gl, True, gc2)
    screen.blit(lbl, (gt.centerx - lbl.get_width() // 2, gt.y - 13))


# ============================================================
# ARTIFACTS
# ============================================================
def draw_artifacts(screen, state):
    """Draw field artifacts and flying artifact trails."""
    r = CONFIG["artifact_radius"]
    for a in state.artifacts:
        if not a.on_field or a.respawn_timer > 0:
            continue
        c = GREEN if a.color == "G" else PURPLE
        if math.hypot(a.vx, a.vy) > 30:
            ghost_x = a.x - a.vx * 0.015
            ghost_y = a.y - a.vy * 0.015
            gs = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(gs, (c[0], c[1], c[2], 80), (r + 2, r + 2), r)
            screen.blit(gs, (int(ghost_x - r - 2), int(ghost_y - r - 2)))
        pygame.draw.circle(screen, (c[0], c[1], c[2], 40), (int(a.x), int(a.y)), r + 3)
        pygame.draw.circle(screen, c, (int(a.x), int(a.y)), r)
        pygame.draw.circle(screen, WHITE, (int(a.x), int(a.y)), r, 1)

    for fa in state.flying:
        if not fa.active:
            continue
        c = GREEN if fa.color == "G" else PURPLE
        trail_len = len(fa.trail)
        for ti, (tx, ty) in enumerate(fa.trail):
            alpha = int(160 * (ti / max(trail_len, 1)))
            sz = max(1, int(r * (ti / max(trail_len, 1))))
            ts = pygame.Surface((sz * 2 + 2, sz * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(ts, (c[0], c[1], c[2], alpha), (sz + 1, sz + 1), sz)
            screen.blit(ts, (int(tx - sz - 1), int(ty - sz - 1)))
        pygame.draw.circle(screen, c, (int(fa.x), int(fa.y)), r + 2)
        pygame.draw.circle(screen, WHITE, (int(fa.x), int(fa.y)), r + 2, 1)


# ============================================================
# ROBOT — ZENITH (FTC 19084) DECODE Season Design
# ============================================================
_ROBOT_CACHE_MAX = 360
_robot_cache = {}
_robot_cache_order = deque()


def _robot_cache_key(r):
    """Build a cache key from the robot's visual state."""
    angle_deg = int(-math.degrees(r.angle)) % 360
    turret_deg = int(math.degrees(r.turret_angle) / 2) * 2 % 360
    held = tuple(held.color for held in r.holding)
    return (angle_deg, turret_deg, held)


def _build_robot_surface(r):
    """Render the full 96x96 robot SRCALPHA surface."""
    cs = 96
    half = cs // 2
    surf = pygame.Surface((cs, cs), pygame.SRCALPHA)

    def l2s(lx, ly):
        return (half + lx, half + ly)

    # Layer 1: Drop shadow
    shadow = pygame.Surface((68, 16), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 55), (0, 0, 68, 16))
    surf.blit(shadow, (half - 34, half + 5))
    pygame.draw.ellipse(shadow, (0, 0, 0, 40), (2, 1, 64, 14))
    surf.blit(shadow, (half - 34, half + 5))

    # Layer 2: Four mecanum wheels
    wpos = [(-28, -22), (28, -22), (-28, 22), (28, 22)]
    for wx, wy in wpos:
        lx, ly = half + wx, half + wy
        pygame.draw.ellipse(surf, (40, 40, 50), (lx - 5, ly - 10, 11, 20))
        for off in range(-6, 7, 3):
            pygame.draw.line(surf, (30, 100, 220),
                             (lx - 5 + off, ly - 10),
                             (lx + 5 - off, ly + 10), 2)
        pygame.draw.ellipse(surf, (30, 100, 220), (lx - 5, ly - 10, 11, 20), 1)

    # Layer 3: Open truss frame
    fx, fy = -27, -25
    fw, fh = 54, 50
    silver = (190, 195, 200)
    pygame.draw.rect(surf, silver, (half + fx, half + fy, fw, fh), 3)
    pygame.draw.line(surf, silver, (half + fx, half + fy), (half + fx + fw, half + fy + fh), 1)
    pygame.draw.line(surf, silver, (half + fx, half + fy + fh), (half + fx + fw, half + fy), 1)
    mid_x = half + fx + fw // 2
    mid_y = half + fy + fh // 2
    pygame.draw.line(surf, silver, (mid_x - 8, half + fy), (mid_x + 8, half + fy + fh), 1)
    pygame.draw.line(surf, silver, (half + fx, mid_y - 6), (half + fx + fw, mid_y + 6), 1)
    pygame.draw.line(surf, (170, 175, 180), (half + fx + 6, half + fy), (half + fx + 6, half + fy + fh), 1)
    pygame.draw.line(surf, (170, 175, 180), (half + fx + fw - 6, half + fy), (half + fx + fw - 6, half + fy + fh), 1)

    # Layer 4: Purple infill panels
    purple_panel = (120, 60, 200, 179)
    pygame.draw.rect(surf, purple_panel, (half + fx + 3, half + fy + fh - 14, fw - 6, 12), border_radius=2)
    pygame.draw.rect(surf, purple_panel, (half + fx + 3, half + fy + 2, fw - 6, 12), border_radius=2)
    pygame.draw.rect(surf, purple_panel, (half + fx + 2, half + fy + 16, 10, fh - 34), border_radius=2)
    pygame.draw.rect(surf, purple_panel, (half + fx + fw - 12, half + fy + 16, 10, fh - 34), border_radius=2)

    # Layer 5: Blue LED glow
    led_blue = (60, 80, 255, 80)
    pygame.draw.line(surf, led_blue, (half + fx + 2, half + fy + 2), (half + fx + fw - 2, half + fy + 2), 1)
    pygame.draw.line(surf, led_blue, (half + fx + 2, half + fy + fh - 2), (half + fx + fw - 2, half + fy + fh - 2), 1)

    # Layer 6: Green status LED
    gx, gy = half - 18, half + 8
    glow = pygame.Surface((12, 12), pygame.SRCALPHA)
    pygame.draw.circle(glow, (0, 255, 60, 50), (6, 6), 6)
    surf.blit(glow, (gx - 6, gy - 6))
    pygame.draw.circle(surf, (0, 255, 60), (gx, gy), 3)
    pygame.draw.circle(surf, (150, 255, 180), (gx, gy), 3, 1)

    # Layer 7: Black corrugated intake hose
    hose_pts = [(0, 22), (4, 18), (7, 12), (8, 6), (6, 0), (4, -4), (0, -8)]
    for i in range(len(hose_pts) - 1):
        x1, y1 = l2s(*hose_pts[i])
        x2, y2 = l2s(*hose_pts[i + 1])
        pygame.draw.line(surf, (25, 25, 28), (x1, y1), (x2, y2), 5)
        pygame.draw.line(surf, (50, 48, 52), (x1, y1), (x2, y2), 2)

    # Layer 8: Front intake rollers
    ix, iy = half, half + 24
    pygame.draw.rect(surf, (20, 20, 25), (ix - 15, iy - 4, 30, 8))
    for rx_off in [-8, 0, 8]:
        pygame.draw.circle(surf, (30, 100, 220), (ix + rx_off, iy), 4)
        pygame.draw.circle(surf, WHITE, (ix + rx_off, iy), 4, 1)

    # Layer 9: Turret base ring
    pygame.draw.circle(surf, (50, 50, 58), (half, half), 10)
    pygame.draw.circle(surf, (130, 130, 140), (half, half), 10, 2)

    # Layer 10: Turret (goal-tracking)
    turret_local_deg = math.degrees(r.angle - r.turret_angle)
    t_surf = pygame.Surface((30, 24), pygame.SRCALPHA)
    pygame.draw.rect(t_surf, (45, 45, 52), (3, 2, 24, 20), border_radius=3)
    pygame.draw.circle(t_surf, (120, 60, 200), (15, 12), 7)
    pygame.draw.circle(t_surf, (160, 100, 240), (15, 12), 7, 1)
    pygame.draw.circle(t_surf, (20, 18, 25), (15, 12), 2)
    pygame.draw.rect(t_surf, (235, 235, 235), (9, 0, 12, 6), border_radius=2)
    pygame.draw.rect(t_surf, WHITE, (9, 0, 12, 6), 1, border_radius=2)
    pygame.draw.circle(t_surf, (180, 180, 190), (6, 6), 1)
    pygame.draw.circle(t_surf, (180, 180, 190), (24, 6), 1)
    pygame.draw.circle(t_surf, (180, 180, 190), (6, 18), 1)
    pygame.draw.circle(t_surf, (180, 180, 190), (24, 18), 1)
    t_rot = pygame.transform.rotozoom(t_surf, turret_local_deg, 1.0)
    surf.blit(t_rot, t_rot.get_rect(center=(half, half)))

    # Layer 11: Team label
    f_zenith = _make_font("Segoe UI", 6)
    f_zenith.set_bold(True)
    lbl = f_zenith.render("ZENITH", True, (220, 220, 255))
    surf.blit(lbl, (half - lbl.get_width() // 2, half + 10))
    f_num = _make_font("Segoe UI", 5)
    lbl2 = f_num.render("19084", True, (120, 60, 200))
    surf.blit(lbl2, (half - lbl2.get_width() // 2, half + 16))

    # Layer 12: Forward direction triangle
    tri = [(half, half - 26), (half - 3, half - 22), (half + 3, half - 22)]
    pygame.draw.polygon(surf, (255, 220, 0), tri)
    pygame.draw.polygon(surf, WHITE, tri, 1)

    # Held artifacts (baked into robot, rotate with body)
    if r.holding:
        count = len(r.holding)
        for hi, held in enumerate(r.holding):
            spread = (hi - (count - 1) / 2) * 12
            lx = spread
            ly = -22
            sx, sy = l2s(lx, ly)
            c = GREEN if held.color == "G" else PURPLE
            bg_s = pygame.Surface((12, 12), pygame.SRCALPHA)
            bg_s.fill((0, 0, 0, 160))
            surf.blit(bg_s, (sx - 6, sy - 6))
            pygame.draw.circle(surf, c, (sx, sy), 5)
            pygame.draw.circle(surf, WHITE, (sx, sy), 5, 1)

    return surf


def draw_robot(screen, state):
    """Draw the robot with render caching."""
    r = state.robot
    key = _robot_cache_key(r)

    if key not in _robot_cache:
        if len(_robot_cache) >= _ROBOT_CACHE_MAX:
            old_key = _robot_cache_order.popleft()
            _robot_cache.pop(old_key, None)
        _robot_cache[key] = _build_robot_surface(r)
        _robot_cache_order.append(key)

    cached = _robot_cache[key]
    angle_deg = -math.degrees(r.angle)
    rotated = pygame.transform.rotozoom(cached, angle_deg, 1.0)
    screen.blit(rotated, rotated.get_rect(center=(int(r.x), int(r.y))))


# ============================================================
# HUD
# ============================================================
def draw_hud(screen, state):
    """Draw the heads-up display panel."""
    panel = pygame.Rect(HX, FY - 5, HW, FS + 10)
    _round_rect(screen, panel, BG_DARK, 6)
    pygame.draw.rect(screen, GRAY, panel, 2, border_radius=6)

    y = FY + 20

    pc = WHITE
    pt = "TELEOP"
    if state.phase == "ENDGAME":
        pt = "ENDGAME" if int(state.timer * 3) % 2 == 0 else ""
        pc = ORANGE
    lbl = f_hud.render(pt, True, pc)
    screen.blit(lbl, (HX + HW // 2 - lbl.get_width() // 2, y))
    y += f_hud.get_height() + 4

    if state.phase != "FINISHED" and not state.timer_running:
        badge_bg = (100, 30, 30) if state.timer == CONFIG["teleop_time"] else (100, 60, 10)
        badge_txt = "STOPPED" if state.timer == CONFIG["teleop_time"] else "PAUSED"
        badge_surf = f_micro.render(f" {badge_txt} ", True, WHITE)
        bw, bh = badge_surf.get_width(), badge_surf.get_height()
        badge_rect = pygame.Rect(HX + HW // 2 - bw // 2 - 4, y, bw + 8, bh + 4)
        pygame.draw.rect(screen, badge_bg, badge_rect, border_radius=4)
        screen.blit(badge_surf, (HX + HW // 2 - bw // 2, y + 2))
        y += bh + 10
    else:
        y += 4

    t = max(0, int(state.timer))
    ts = f"{t // 60}:{t % 60:02d}"
    if not state.timer_running and state.phase != "FINISHED":
        tc = (120, 120, 120)
    elif state.phase == "ENDGAME" and int(state.timer * 4) % 2 == 0:
        tc = ORANGE
    else:
        tc = WHITE
    lbl = f_timer.render(ts, True, tc)
    screen.blit(lbl, (HX + HW // 2 - lbl.get_width() // 2, y))
    y += f_timer.get_height() + 12

    lbl = f_small.render("MOTIF", True, GRAY)
    screen.blit(lbl, (HX + 18, y))
    y += f_small.get_height() + 4
    for mi, c in enumerate(state.motif):
        mx = HX + 22 + mi * 48
        clr = GREEN if c == "G" else PURPLE
        pygame.draw.circle(screen, clr, (mx, y + 12), 12)
        pygame.draw.circle(screen, WHITE, (mx, y + 12), 12, 2)
        lbl = f_small.render(c, True, WHITE)
        screen.blit(lbl, (mx - lbl.get_width() // 2, y + 28))
    y += 70

    in_zone = state.in_launch_zone(state.robot.x, state.robot.y)
    ztxt = "IN LAUNCH ZONE" if in_zone else "OUTSIDE ZONE"
    zsym = "\u2713" if in_zone else "\u2717"
    zc = GREEN if in_zone else GRAY
    lbl = f_tiny.render(f"{zsym} {ztxt}", True, zc)
    screen.blit(lbl, (HX + 18, y))
    y += f_tiny.get_height() + 4

    intake_txt = "INTAKE: ON" if state.intake_active else "INTAKE: OFF"
    intake_clr = GREEN if state.intake_active else GRAY
    lbl = f_tiny.render(intake_txt, True, intake_clr)
    screen.blit(lbl, (HX + 18, y))
    y += f_tiny.get_height() + 8

    pygame.draw.line(screen, DARK_GRAY, (HX + 15, y), (HX + HW - 15, y), 2)
    y += 10

    team = state.team
    lbl = f_hud_s.render("SCORE", True, SOFT_WHITE)
    screen.blit(lbl, (HX + 18, y))
    y += f_hud_s.get_height() + 6
    lines = [
        f"Total:  {team.total_score()}",
        f"Classified:  {team.classified}  (+{team.classified * 3})",
        f"Overflow:  {team.overflow}",
        f"Depot:  {team.depot}",
        f"Pattern:  {team.pattern_pts}",
        f"Base:  {team.base_pts}",
    ]
    for line in lines:
        lbl = f_tiny.render(line, True, WHITE)
        screen.blit(lbl, (HX + 20, y))
        y += f_tiny.get_height() + 2
    y += 8

    pygame.draw.line(screen, DARK_GRAY, (HX + 15, y), (HX + HW - 15, y), 2)
    y += 8
    lbl = f_small.render("RAMP", True, SOFT_WHITE)
    screen.blit(lbl, (HX + 18, y))
    y += f_small.get_height() + 6
    slot_sz = 22
    gap = 3
    total_w = CONFIG["ramp_slots"] * slot_sz + (CONFIG["ramp_slots"] - 1) * gap
    start_x = HX + (HW - total_w) // 2
    for i in range(CONFIG["ramp_slots"]):
        sx = start_x + i * (slot_sz + gap)
        sr = pygame.Rect(sx, y, slot_sz, slot_sz)
        if team.ramp[i] is not None:
            c = GREEN if team.ramp[i] == "G" else PURPLE
            pygame.draw.rect(screen, c, sr, border_radius=3)
        else:
            pygame.draw.rect(screen, SLOT_EMPTY, sr, border_radius=3)
        pygame.draw.rect(screen, SLOT_BORDER, sr, 1, border_radius=3)
    y += slot_sz + 14

    gc = GATE_OPEN_COLOR if team.gate_open else GATE_COLOR
    gtxt = "GATE: OPEN" if team.gate_open else "GATE: CLOSED"
    lbl = f_small.render(gtxt, True, gc)
    screen.blit(lbl, (HX + 18, y))
    y += f_small.get_height() + 12

    pygame.draw.line(screen, DARK_GRAY, (HX + 15, y), (HX + HW - 15, y), 2)
    y += 8

    PARK_NONE_CLR = DARK_GRAY
    PARK_NONE_LBL = (100, 100, 105)
    PARK_PARTIAL_CLR = GOAL_GOLD
    PARK_FULL_CLR = PARK_GREEN
    cell_w, cell_h = 24, 14
    cell_gap = 3
    bar_x = HX + 22

    ps = state.park_status
    bar_y = y

    for ci in range(3):
        cx = bar_x + ci * (cell_w + cell_gap)
        if ps == "FULL":
            cell_clr = PARK_FULL_CLR
        elif ps == "PARTIAL" and ci < 2:
            cell_clr = PARK_PARTIAL_CLR
        else:
            cell_clr = (40, 40, 45)
        pygame.draw.rect(screen, cell_clr, (cx, bar_y, cell_w, cell_h), border_radius=3)
        pygame.draw.rect(screen, SLOT_BORDER, (cx, bar_y, cell_w, cell_h), 1, border_radius=3)

    if ps == "FULL":
        status_txt = "FULLY PARKED"
        status_clr = PARK_FULL_CLR
    elif ps == "PARTIAL":
        status_txt = "PARTIAL"
        status_clr = PARK_PARTIAL_CLR
    else:
        status_txt = "NOT PARKED"
        status_clr = PARK_NONE_LBL
    lbl = f_tiny.render(status_txt, True, status_clr)
    screen.blit(lbl, (bar_x + 3 * (cell_w + cell_gap) + 8, bar_y + cell_h // 2 - lbl.get_height() // 2))

    y = bar_y + cell_h + 8

    pygame.draw.line(screen, DARK_GRAY, (HX + 15, y), (HX + HW - 15, y), 2)


# ============================================================
# MATCH END OVERLAY
# ============================================================
_end_overlay = None


def _build_end_overlay(state):
    """Render the match-end overlay onto a cached surface."""
    global _end_overlay
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 200))

    cx, cy = W // 2, H // 2 - 30

    lbl = f_huge.render("MATCH OVER", True, GOLD)
    surf.blit(lbl, (cx - lbl.get_width() // 2, cy - 50))
    cy += 20

    t = state.team
    lbl = f_hud.render(f"FINAL SCORE: {t.total_score()}", True, WHITE)
    surf.blit(lbl, (cx - lbl.get_width() // 2, cy))
    cy += 40

    breakdown = [
        f"Classified: {t.classified} pts  |  Overflow: {t.overflow}  |  Depot: {t.depot}",
        f"Pattern: {t.pattern_pts} pts",
    ]
    for line in breakdown:
        lbl = f_small.render(line, True, SOFT_WHITE)
        surf.blit(lbl, (cx - lbl.get_width() // 2, cy))
        cy += 22

    ps = state.park_status
    if ps == "FULL":
        park_txt = "Fully parked: +10"
        park_clr = PARK_GREEN
    elif ps == "PARTIAL":
        park_txt = "Partially parked: +5"
        park_clr = GOAL_GOLD
    else:
        park_txt = "Not parked: +0"
        park_clr = RED_ACCENT
    lbl = f_small.render(park_txt, True, park_clr)
    surf.blit(lbl, (cx - lbl.get_width() // 2, cy))
    cy += 22
    cy += 30

    lbl = f_small.render("F5 to reset  |  ESC to quit", True, WHITE)
    surf.blit(lbl, (cx - lbl.get_width() // 2, cy))

    _end_overlay = surf


def draw_match_end(screen, state):
    """Draw the match-end overlay with caching."""
    global _end_overlay
    if state.phase != "FINISHED":
        _end_overlay = None
        return
    if _end_overlay is None:
        _build_end_overlay(state)
    screen.blit(_end_overlay, (0, 0))
