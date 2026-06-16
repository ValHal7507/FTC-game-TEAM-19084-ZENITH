"""
FTC DECODE — All drawing and rendering functions.
"""

import math
import random
from collections import deque

import pygame
from config import (
    CONFIG, FX, FY, FS, HX, HW, W, H,
    BLACK, WHITE, GRAY, DARK_GRAY, BG_DARK, CHARCOAL, SOFT_WHITE,
    ROBOT_PURPLE, ROBOT_DARK, GLOW_PURPLE,
    ZENITH_PURPLE, ZENITH_ACCENT, ZENITH_DARK, ZENITH_LABEL, ZENITH_TAG,
    GOAL_GOLD, GOAL_DARK, RAMP_DARK, SLOT_EMPTY, SLOT_BORDER,
    GATE_COLOR, GATE_OPEN_COLOR,
    PURPLE, GREEN, GOLD, ORANGE, RED_ACCENT, PARK_GREEN,
    HEAT_GREEN, HEAT_YELLOW, HEAT_ORANGE, HEAT_RED,
    PAUSE_OVERLAY, MENU_BG, MENU_BORDER, MENU_HIGHLIGHT_BG,
    MENU_HIGHLIGHT_BORDER, MENU_TEXT, MENU_TITLE,
    OPTIONS_REBIND, OPTIONS_BIND,
    GAMEPAD_NAMES, LOCKED_KEYBINDS,
    ALLIANCE_BLUE, ALLIANCE_BLUE_DIM, ALLIANCE_RED, ALLIANCE_RED_DIM,
    lerp,
    VW, VH,
    CHAOS_BG, CHAOS_GRID, CHAOS_STREAK, CHAOS_FLASH, CHAOS_ZONE_TINT,
    CHAOS_TEXT_A, CHAOS_TEXT_B,
    CHAOS_PARTICLE_A, CHAOS_PARTICLE_B,
    CHAOS_DOT_FILLED, CHAOS_DOT_EMPTY,
    CHAOS_SEQUENCE,
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

_chaos_font_lg = None
_chaos_font_sm = None


def _init_chaos_fonts():
    global _chaos_font_lg, _chaos_font_sm
    if _chaos_font_lg is None:
        _chaos_font_lg = pygame.font.SysFont("Impact", 54)
    if _chaos_font_sm is None:
        _chaos_font_sm = pygame.font.SysFont("Arial", 15, bold=True)


# ============================================================
# HELPERS
# ============================================================
def _round_rect(surf, rect, color, r=6, width=0):
    """Draw a rounded rectangle."""
    pygame.draw.rect(surf, color, rect, width, border_radius=r)


# ============================================================
# CHAOS MODE — PARTICLES
# ============================================================
def spawn_chaos_particles(state):
    """Burst-spawn 60 particles on chaos activation. Public — imported
    by mode files."""
    state.chaos_particles.clear()
    for _ in range(60):
        state.chaos_particles.append({
            "x":   random.uniform(VW * 0.05, VW * 0.95),
            "y":   random.uniform(VH * 0.05, VH * 0.88),
            "vx":  random.uniform(-130, 130),
            "vy":  random.uniform(-160, -30),
            "life": random.uniform(0.9, 2.4),
            "max":  1.0,
            "r":   random.randint(3, 7),
            "col": random.choice([CHAOS_PARTICLE_A, CHAOS_PARTICLE_B]),
        })


def update_chaos_particles(state, dt):
    """Advance particles and trickle-spawn replacements. Public."""
    survivors = []
    for p in state.chaos_particles:
        p["x"]    += p["vx"] * dt
        p["y"]    += p["vy"] * dt
        p["vy"]   += 90 * dt          # gentle gravity
        p["life"] -= dt
        if p["life"] > 0:
            survivors.append(p)
    state.chaos_particles = survivors
    if len(state.chaos_particles) < 25 and random.random() < 0.5:
        state.chaos_particles.append({
            "x":   random.uniform(VW * 0.05, VW * 0.95),
            "y":   VH * 0.88,
            "vx":  random.uniform(-90, 90),
            "vy":  random.uniform(-190, -80),
            "life": random.uniform(0.6, 1.8),
            "max":  1.0,
            "r":   random.randint(2, 5),
            "col": random.choice([CHAOS_PARTICLE_A, CHAOS_PARTICLE_B]),
        })


def draw_chaos_particles(surf, state):
    for p in state.chaos_particles:
        alpha = max(0.0, min(1.0, p["life"] / p["max"]))
        col = (max(0, min(255, int(p["col"][0]*alpha))),
               max(0, min(255, int(p["col"][1]*alpha))),
               max(0, min(255, int(p["col"][2]*alpha))))
        pygame.draw.circle(surf, col, (int(p["x"]), int(p["y"])), p["r"])


# ============================================================
# CHAOS MODE — BACKGROUND
# ============================================================
def draw_chaos_background(surf, t):
    """Dark crimson-purple grid field. Call INSTEAD of the normal
    background fill."""
    surf.fill(CHAOS_BG)

    pulse = 0.5 + 0.5 * math.sin(t * 3.0)
    grid_col = (
        int(CHAOS_GRID[0] + 40 * pulse),
        CHAOS_GRID[1],
        int(CHAOS_GRID[2] + 50 * pulse),
    )
    spacing = 48
    for gx in range(0, VW, spacing):
        pygame.draw.line(surf, grid_col, (gx, 0), (gx, VH), 1)
    for gy in range(0, VH, spacing):
        pygame.draw.line(surf, grid_col, (0, gy), (VW, gy), 1)

    # Speed-line streaks scrolling diagonally
    for i in range(10):
        bx = int((VW * i / 10 + t * 70) % (VW + 60))
        pygame.draw.line(surf, CHAOS_STREAK, (bx, 0), (bx - 50, VH), 1)


def draw_chaos_zone_tint(surf):
    """Overlay a red tint across the entire field area to tint zones.
    Call AFTER zone shapes are drawn, BEFORE robots/artifacts."""
    tint = pygame.Surface((VW, VH), pygame.SRCALPHA)
    tint.fill(CHAOS_ZONE_TINT)
    surf.blit(tint, (0, 0))


# ============================================================
# CHAOS MODE — HUD
# ============================================================
def draw_chaos_hud(surf, state, t):
    """Flash, splash title, mascot backflip cameo, and persistent badge.
    Call AFTER all normal HUD elements so chaos draws on top."""
    _init_chaos_fonts()
    age = t - state.chaos_activate_time

    # Activation screen flash (first 0.35 s)
    if age < 0.35:
        a = int(220 * (1.0 - age / 0.35))
        flash_surf = pygame.Surface((VW, VH), pygame.SRCALPHA)
        flash_surf.fill((*CHAOS_FLASH, a))
        surf.blit(flash_surf, (0, 0))

    # "⚡ CHAOS MODE ⚡" splash that scales in then fades (0 – 2.0 s)
    if age < 2.0:
        scale = min(1.0, age / 0.22)
        fade  = max(0.0, 1.0 - (age - 1.1) / 0.9) if age > 1.1 else 1.0
        txt   = _chaos_font_lg.render("⚡ CHAOS MODE ⚡", True, CHAOS_TEXT_A)
        if scale < 1.0:
            w = max(1, int(txt.get_width()  * scale))
            h = max(1, int(txt.get_height() * scale))
            txt = pygame.transform.smoothscale(txt, (w, h))
        alpha_s = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
        alpha_s.blit(txt, (0, 0))
        alpha_s.set_alpha(int(255 * fade))
        surf.blit(alpha_s, (VW//2 - alpha_s.get_width()//2,
                             VH//2 - alpha_s.get_height()//2))

    # Mascot backflip cameo (bottom-right corner, 0 – 2.0 s)
    if age < 2.0:
        try:
            from menu import draw_mascot   # lazy import; avoids circular dep
            mascot_buf = pygame.Surface((200, 260), pygame.SRCALPHA)
            draw_mascot(mascot_buf, 100, 130, t)
            small = pygame.transform.smoothscale(mascot_buf, (80, 104))
            # Full 360° rotation completes in 0.65 s, then stays upright
            angle = min(360.0, (age / 0.65) * 360.0)
            rotated = pygame.transform.rotate(small, angle)
            fade = max(0.0, 1.0 - (age - 1.3) / 0.7) if age > 1.3 else 1.0
            rotated.set_alpha(int(255 * fade))
            bx = VW - rotated.get_width()  - 12
            by = VH - rotated.get_height() - 12
            surf.blit(rotated, (bx, by))
        except ImportError:
            pass   # draw_mascot not yet implemented — skip silently

    # Persistent pulsing "⚡ CHAOS MODE" badge (top-centre, after flash)
    if age >= 0.35:
        pulse = 0.65 + 0.35 * math.sin(t * 5.0)
        col   = (int(CHAOS_TEXT_A[0]*pulse), int(CHAOS_TEXT_A[1]*pulse),
                 int(CHAOS_TEXT_A[2]*pulse))
        badge = _chaos_font_sm.render("⚡  CHAOS MODE  ⚡", True, col)
        surf.blit(badge, (VW//2 - badge.get_width()//2, 5))


def draw_konami_progress(surf, state):
    """Dot row in top-right corner while the sequence is being entered.
    Filled purple dot = correct key entered. Grey ring = still needed.
    Self-guards: does nothing when chaos is active or no keys pressed."""
    if state.chaos_active or state.konami_progress == 0:
        return
    _init_chaos_fonts()
    n     = len(CHAOS_SEQUENCE)
    r     = 5
    gap   = 14
    sx    = VW - n * gap - 10
    sy    = 8
    for i in range(n):
        cx = sx + i * gap + r
        cy = sy + r
        if i < state.konami_progress:
            pygame.draw.circle(surf, CHAOS_DOT_FILLED, (cx, cy), r)
        else:
            pygame.draw.circle(surf, CHAOS_DOT_EMPTY, (cx, cy), r, 1)


# ============================================================
# FIELD — STATIC CACHE
# ============================================================
_field_surface = None
_field_cache_park = None


def _build_field_surface():
    """Render all static field elements onto a cached surface.
    Background is NOT included — drawn separately by draw_field()."""
    global _field_surface, _field_cache_park
    surf = pygame.Surface((W, H), pygame.SRCALPHA)

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

    br = pygame.Rect(FX + 10, FY + FS // 2 - CONFIG["base_size"] // 2,
                     CONFIG["base_size"], CONFIG["base_size"])
    pygame.draw.rect(surf, ROBOT_PURPLE, br, 2, border_radius=3)
    lbl = f_small.render("BASE", True, ROBOT_PURPLE)
    surf.blit(lbl, (br.centerx - lbl.get_width() // 2, br.centery - lbl.get_height() // 2))

    # Shooting zone triangle (right-angle isosceles, hypotenuse at bottom)
    _hyp = CONFIG["shooting_zone_size"]
    _ht = _hyp / 2
    _cx = FX + FS // 2
    _cy = FY + FS - 5 - _ht / 3
    shoot_pts = [
        (_cx, _cy - 2 * _ht / 3),
        (_cx - _hyp / 2, _cy + _ht / 3),
        (_cx + _hyp / 2, _cy + _ht / 3),
    ]
    shoot_surface = pygame.Surface((FS, FS), pygame.SRCALPHA)
    pygame.draw.polygon(shoot_surface, (255, 255, 255, 20),
                        [(p[0] - FX, p[1] - FY) for p in shoot_pts])
    surf.blit(shoot_surface, (FX, FY))
    pygame.draw.polygon(surf, SOFT_WHITE, shoot_pts, 1)
    shoot_lbl = f_tiny.render("SHOOT", True, SOFT_WHITE)
    surf.blit(shoot_lbl, (_cx - shoot_lbl.get_width() // 2, int(_cy + _ht / 3) - shoot_lbl.get_height() - 4))

    gr = pygame.Rect(FX + FS // 2 - CONFIG["goal_w"] // 2, FY,
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

    cols = [FX + FS // 2 - 50]
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
    """Draw the field: background + cached static elements + dynamic overlays."""
    global _field_surface, _field_cache_park

    if _field_surface is None:
        _build_field_surface()

    # ── Background: normal charcoal floor or chaos grid ───────────────
    if state.chaos_active:
        t = pygame.time.get_ticks() / 1000.0
        draw_chaos_background(screen, t)
    else:
        rect = pygame.Rect(FX, FY, FS, FS)
        _round_rect(screen, rect, CHARCOAL, 4)
        pygame.draw.rect(screen, GRAY, rect, 2, border_radius=4)

    # ── Static field elements (zones, goal, ramp, labels, etc.) ──────
    screen.blit(_field_surface, (0, 0))

    # --- Drive mode badge (always dynamic) ---
    mode = state.robot.drive_mode.upper()
    lbl = f_tiny.render(f"DRIVE: {mode}", True, ZENITH_ACCENT)
    badge_rect = pygame.Rect(FX + 4, FY + 4, lbl.get_width() + 8, lbl.get_height() + 4)
    pygame.draw.rect(screen, ZENITH_DARK, badge_rect, border_radius=3)
    pygame.draw.rect(screen, ZENITH_PURPLE, badge_rect, 1, border_radius=3)
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
    team2 = state.team2
    gate_open = state.team.gate_open
    if state.game_mode == "1v1" and team2 is not None:
        gate_open = state.team.gate_open or team2.gate_open
    gc = GATE_OPEN_COLOR if gate_open else GATE_COLOR
    pygame.draw.rect(screen, gc, gt, border_radius=2)
    pygame.draw.rect(screen, WHITE, gt, 1, border_radius=2)
    gl = "OPEN" if gate_open else "GATE"
    gc2 = GATE_OPEN_COLOR if gate_open else GOLD
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
    return (angle_deg, turret_deg, held, r.alliance)


def _build_robot_surface(r):
    """Render the full 96x96 robot SRCALPHA surface."""
    cs = 96
    half = cs // 2
    surf = pygame.Surface((cs, cs), pygame.SRCALPHA)

    # Resolve alliance colors
    if r.alliance == "blue":
        led_color = ALLIANCE_BLUE
        roller_color = ALLIANCE_BLUE_DIM
    elif r.alliance == "red":
        led_color = ALLIANCE_RED
        roller_color = ALLIANCE_RED_DIM
    else:
        led_color = (0, 200, 100)
        roller_color = (80, 120, 200)

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
            pygame.draw.line(surf, roller_color,
                             (lx - 5 + off, ly - 10),
                             (lx + 5 - off, ly + 10), 2)
        pygame.draw.ellipse(surf, roller_color, (lx - 5, ly - 10, 11, 20), 1)

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
    pygame.draw.circle(glow, (*led_color, 50), (6, 6), 6)
    surf.blit(glow, (gx - 6, gy - 6))
    pygame.draw.circle(surf, led_color, (gx, gy), 3)
    lighter = tuple(min(255, c + 100) for c in led_color)
    pygame.draw.circle(surf, lighter, (gx, gy), 3, 1)

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
        pygame.draw.circle(surf, roller_color, (ix + rx_off, iy), 4)
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
    lbl = f_zenith.render("ZENITH", True, ZENITH_ACCENT)
    surf.blit(lbl, (half - lbl.get_width() // 2, half + 10))
    f_num = _make_font("Segoe UI", 5)
    lbl2 = f_num.render("19084", True, ZENITH_ACCENT)
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
def draw_hud(screen, state, t=0.0):
    """Draw the heads-up display panel."""
    if state.game_mode == "1v1" and state.robot2 is not None:
        _draw_hud_1v1(screen, state, t)
    else:
        _draw_hud_solo(screen, state, t)


def _draw_hud_1v1(screen, state, t=0.0):
    """Split HUD for 1v1 mode: P1 top half, timer middle, P2 bottom half."""
    panel = pygame.Rect(HX, FY - 5, HW, H - FY + 5)
    _round_rect(screen, panel, BG_DARK, 6)
    pygame.draw.rect(screen, GRAY, panel, 2, border_radius=6)

    # ── Team ZENITH branding header ──────────────────────────────────────────
    strip_rect = pygame.Rect(HX, FY, HW, 30)
    pygame.draw.rect(screen, ZENITH_DARK, strip_rect)
    pygame.draw.line(screen, ZENITH_PURPLE, (HX, FY + 30), (HX + HW, FY + 30), 1)
    label_surf = f_small.render(ZENITH_LABEL, True, ZENITH_ACCENT)
    label_rect = label_surf.get_rect(center=(HX + HW // 2, FY + 15))
    screen.blit(label_surf, label_rect)
    tag_surf = f_micro.render(ZENITH_TAG, True, ZENITH_ACCENT)
    tag_surf.set_alpha(150)
    tag_rect = tag_surf.get_rect(center=(HX + HW // 2, FY + 30 + 9))
    screen.blit(tag_surf, tag_rect)
    # ──────────────────────────────────────────────────────────────────────────

    y = FY + 50

    # Phase label
    pc = WHITE
    pt = "TELEOP"
    if state.phase == "ENDGAME":
        pt = "ENDGAME" if int(state.timer * 3) % 2 == 0 else ""
        pc = ORANGE
    lbl = f_hud_s.render(pt, True, pc)
    screen.blit(lbl, (HX + HW // 2 - lbl.get_width() // 2, y))
    y += f_hud_s.get_height() + 4

    # Timer (compact)
    t = max(0, int(state.timer))
    ts = f"{t // 60}:{t % 60:02d}"
    if not state.timer_running and state.phase != "FINISHED":
        tc = (120, 120, 120)
    elif state.phase == "ENDGAME" and int(state.timer * 4) % 2 == 0:
        tc = ORANGE
    else:
        tc = WHITE
    lbl = f_hud_s.render(ts, True, tc)
    screen.blit(lbl, (HX + HW // 2 - lbl.get_width() // 2, y))
    y += f_hud_s.get_height() + 6

    # Motif (compact)
    for mi, c in enumerate(state.motif):
        mx = HX + 30 + mi * 36
        clr = GREEN if c == "G" else PURPLE
        pygame.draw.circle(screen, clr, (mx, y + 8), 8)
        pygame.draw.circle(screen, WHITE, (mx, y + 8), 8, 1)
    y += 24

    pygame.draw.line(screen, DARK_GRAY, (HX + 15, y), (HX + HW - 15, y), 2)
    y += 6

    # ── Shared gate (between P1 and P2) ─────────────────────────────────────
    team2 = state.team2
    gate_open = state.team.gate_open
    if state.game_mode == "1v1" and team2 is not None:
        gate_open = state.team.gate_open or team2.gate_open
    gtxt = "GATE: OPEN" if gate_open else "GATE: CLOSED"
    gc = GATE_OPEN_COLOR if gate_open else GATE_COLOR
    lbl = f_tiny.render(gtxt, True, gc)
    screen.blit(lbl, (HX + 18, y))
    y += f_tiny.get_height() + 6

    # ── P1 panel (BLUE) ──────────────────────────────────────────────────────
    lbl = f_small.render("P1 — BLUE", True, ALLIANCE_BLUE)
    screen.blit(lbl, (HX + 18, y))
    y += f_small.get_height() + 4

    p1_in_zone = state.in_launch_zone(state.robot.x, state.robot.y)
    after_p1 = _draw_player_hud_section(screen, state.team, state.robot, state.park_status,
                             state.intake_active, state.intake_heat,
                             state.intake_overheated, state.intake_cooldown_timer,
                             state, y, ALLIANCE_BLUE, in_zone=p1_in_zone)

    # ── P2 panel (RED) ───────────────────────────────────────────────────────
    y = after_p1 + 4
    lbl = f_small.render("P2 — RED", True, ALLIANCE_RED)
    screen.blit(lbl, (HX + 18, y))
    y += f_small.get_height() + 4

    p2_in_zone = state.in_launch_zone2(state.robot2.x, state.robot2.y)
    after_p2 = _draw_player_hud_section(screen, state.team2, state.robot2, state.park_status2,
                             state.intake_active2, state.intake_heat2,
                             state.intake_overheated2, state.intake_cooldown_timer2,
                             state, y, ALLIANCE_RED, in_zone=p2_in_zone)

    # Winner indicator at match end
    if state.phase == "FINISHED":
        s1 = state.team.total_score(state.chaos_active)
        s2 = state.team2.total_score(state.chaos_active)
        if s1 > s2:
            winner, wclr = "P1 WINS", ALLIANCE_BLUE
        elif s2 > s1:
            winner, wclr = "P2 WINS", ALLIANCE_RED
        else:
            winner, wclr = "TIE", GOLD
        lbl = f_small.render(winner, True, wclr)
        screen.blit(lbl, (HX + HW // 2 - lbl.get_width() // 2, FY + 50 + f_hud_s.get_height() + f_hud_s.get_height() + 30))


def _draw_player_hud_section(screen, team, robot, park_status,
                             intake_active, intake_heat, intake_overheated, intake_cooldown_timer,
                             state, y, accent_color, in_zone=False):
    """Draw a compact single-player HUD section."""
    ztxt = "IN ZONE" if in_zone else "OUTSIDE"
    zsym = "\u2713" if in_zone else "\u2717"
    zc = GREEN if in_zone else GRAY
    lbl = f_tiny.render(f"{zsym} {ztxt}", True, zc)
    screen.blit(lbl, (HX + 18, y))
    y += f_tiny.get_height() + 3

    # Intake status
    if intake_overheated:
        itxt, iclr = "INTAKE: COOLDOWN", HEAT_RED
    elif intake_active:
        itxt, iclr = "INTAKE: ON", GREEN
    else:
        itxt, iclr = "INTAKE: OFF", GRAY
    lbl = f_tiny.render(itxt, True, iclr)
    screen.blit(lbl, (HX + 18, y))
    y += f_tiny.get_height() + 3

    # Heat bar
    bar_x, bar_y = HX + 18, y
    bar_w, bar_h = HW - 36, 8
    pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
    if intake_heat > 0:
        fill_w = int(bar_w * intake_heat)
        if intake_heat < 0.5:
            t = intake_heat / 0.5
            bar_clr = (int(lerp(60, 230, t)), int(lerp(200, 200, t)), int(lerp(80, 40, t)))
        elif intake_heat < 0.8:
            t = (intake_heat - 0.5) / 0.3
            bar_clr = (int(lerp(230, 240, t)), int(lerp(200, 140, t)), int(lerp(40, 30, t)))
        else:
            t = (intake_heat - 0.8) / 0.2
            bar_clr = (int(lerp(240, 220, t)), int(lerp(140, 50, t)), int(lerp(30, 40, t)))
        pygame.draw.rect(screen, bar_clr, (bar_x, bar_y, fill_w, bar_h), border_radius=3)
    if intake_overheated:
        cd_txt = f_tiny.render(f"{intake_cooldown_timer:.1f}s", True, HEAT_RED)
        screen.blit(cd_txt, (bar_x + bar_w + 6, bar_y - 1))
    y += bar_h + 6

    # Score (compact)
    lbl = f_tiny.render(f"Score: {team.total_score(state.chaos_active)}  |  Cls: {team.classified}  |  Ovf: {team.overflow}  |  Pt: {team.pattern_pts}  |  Base: {team.base_pts}", True, WHITE)
    screen.blit(lbl, (HX + 18, y))
    y += f_tiny.get_height() + 4

    # Ramp (compact)
    slot_sz = 18
    gap = 2
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
    y += slot_sz + 6

    # Park status
    PARK_NONE_CLR = DARK_GRAY
    PARK_NONE_LBL = (100, 100, 105)
    PARK_PARTIAL_CLR = GOAL_GOLD
    PARK_FULL_CLR = PARK_GREEN
    cell_w, cell_h = 20, 12
    cell_gap = 2
    bar_x = HX + 22
    for ci in range(3):
        cx = bar_x + ci * (cell_w + cell_gap)
        if park_status == "FULL":
            cell_clr = PARK_FULL_CLR
        elif park_status == "PARTIAL" and ci < 2:
            cell_clr = PARK_PARTIAL_CLR
        else:
            cell_clr = (40, 40, 45)
        pygame.draw.rect(screen, cell_clr, (cx, y, cell_w, cell_h), border_radius=3)
        pygame.draw.rect(screen, SLOT_BORDER, (cx, y, cell_w, cell_h), 1, border_radius=3)
    if park_status == "FULL":
        stxt, sclr = "FULLY PARKED", PARK_FULL_CLR
    elif park_status == "PARTIAL":
        stxt, sclr = "PARTIAL", PARK_PARTIAL_CLR
    else:
        stxt, sclr = "NOT PARKED", PARK_NONE_LBL
    lbl = f_tiny.render(stxt, True, sclr)
    screen.blit(lbl, (bar_x + 3 * (cell_w + cell_gap) + 6, y + cell_h // 2 - lbl.get_height() // 2))

    pygame.draw.line(screen, DARK_GRAY, (HX + 15, y + cell_h + 6), (HX + HW - 15, y + cell_h + 6), 2)
    return y + cell_h + 6


def _draw_hud_solo(screen, state, t=0.0):
    """Solo-mode HUD (unchanged from original)."""
    HUD_BRAND_H = 48

    panel = pygame.Rect(HX, FY - 5, HW, H - FY + 5)
    _round_rect(screen, panel, BG_DARK, 6)
    pygame.draw.rect(screen, GRAY, panel, 2, border_radius=6)

    # ── Team ZENITH branding header ──────────────────────────────────────────
    strip_rect = pygame.Rect(HX, FY, HW, 30)
    pygame.draw.rect(screen, ZENITH_DARK, strip_rect)
    pygame.draw.line(screen, ZENITH_PURPLE, (HX, FY + 30), (HX + HW, FY + 30), 1)

    label_surf = f_small.render(ZENITH_LABEL, True, ZENITH_ACCENT)
    label_rect = label_surf.get_rect(center=(HX + HW // 2, FY + 15))
    screen.blit(label_surf, label_rect)

    tag_surf = f_micro.render(ZENITH_TAG, True, ZENITH_ACCENT)
    tag_surf.set_alpha(150)
    tag_rect = tag_surf.get_rect(center=(HX + HW // 2, FY + 30 + 9))
    screen.blit(tag_surf, tag_rect)
    # ──────────────────────────────────────────────────────────────────────────

    y = FY + HUD_BRAND_H + 20

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

    if state.intake_overheated:
        intake_txt = "INTAKE: COOLDOWN"
        intake_clr = HEAT_RED
    elif state.intake_active:
        intake_txt = "INTAKE: ON"
        intake_clr = GREEN
    else:
        intake_txt = "INTAKE: OFF"
        intake_clr = GRAY
    lbl = f_tiny.render(intake_txt, True, intake_clr)
    screen.blit(lbl, (HX + 18, y))
    y += f_tiny.get_height() + 4

    bar_x, bar_y = HX + 18, y
    bar_w, bar_h = HW - 36, 10
    pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
    heat = state.intake_heat
    if heat > 0:
        fill_w = int(bar_w * heat)
        if heat < 0.5:
            t2 = heat / 0.5
            bar_clr = (int(lerp(60, 230, t2)), int(lerp(200, 200, t2)), int(lerp(80, 40, t2)))
        elif heat < 0.8:
            t2 = (heat - 0.5) / 0.3
            bar_clr = (int(lerp(230, 240, t2)), int(lerp(200, 140, t2)), int(lerp(40, 30, t2)))
        else:
            t2 = (heat - 0.8) / 0.2
            bar_clr = (int(lerp(240, 220, t2)), int(lerp(140, 50, t2)), int(lerp(30, 40, t2)))
        pygame.draw.rect(screen, bar_clr, (bar_x, bar_y, fill_w, bar_h), border_radius=3)
    if state.intake_overheated:
        cd_txt = f_tiny.render(f"{state.intake_cooldown_timer:.1f}s", True, HEAT_RED)
        screen.blit(cd_txt, (bar_x + bar_w + 6, bar_y - 1))
    y += bar_h + 8

    pygame.draw.line(screen, DARK_GRAY, (HX + 15, y), (HX + HW - 15, y), 2)
    y += 10

    team = state.team
    team2 = state.team2
    lbl = f_hud_s.render("SCORE", True, SOFT_WHITE)
    screen.blit(lbl, (HX + 18, y))
    y += f_hud_s.get_height() + 6
    lines = [
        f"Total:  {team.total_score(state.chaos_active)}",
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

    # Gate status
    gate_open = team.gate_open
    if state.game_mode == "1v1" and team2 is not None:
        gate_open = team.gate_open or team2.gate_open
    gc = GATE_OPEN_COLOR if gate_open else GATE_COLOR
    gtxt = "GATE: OPEN" if gate_open else "GATE: CLOSED"
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

    cx, cy = W // 2, H // 2 - 60
    overlay_cx = cx

    lbl = f_huge.render("MATCH OVER", True, GOLD)
    surf.blit(lbl, (cx - lbl.get_width() // 2, cy - 50))
    cy += 20

    # ── Team ZENITH branding between heading and score ───────────────────────
    brand_offset = f_small.get_height() + f_micro.get_height() + 20

    brand_surf = f_small.render(ZENITH_LABEL, True, ZENITH_PURPLE)
    brand_rect = brand_surf.get_rect(center=(overlay_cx, cy + 12))
    surf.blit(brand_surf, brand_rect)

    tag_surf = f_micro.render(ZENITH_TAG, True, ZENITH_ACCENT)
    tag_surf.set_alpha(160)
    tag_rect = tag_surf.get_rect(center=(overlay_cx, brand_rect.bottom + 8))
    surf.blit(tag_surf, tag_rect)

    pygame.draw.line(surf, ZENITH_PURPLE,
        (overlay_cx - 90, tag_rect.bottom + 6),
        (overlay_cx + 90, tag_rect.bottom + 6), 1)

    cy += brand_offset
    # ─────────────────────────────────────────────────────────────────────────

    if state.game_mode == "1v1" and state.team2 is not None:
        # 1v1: show both scores side by side
        s1 = state.team.total_score(state.chaos_active)
        s2 = state.team2.total_score(state.chaos_active)

        # P1 score (left)
        lbl = f_small.render("P1 — BLUE", True, ALLIANCE_BLUE)
        surf.blit(lbl, (cx - 200 - lbl.get_width() // 2, cy))
        lbl = f_hud.render(str(s1), True, ALLIANCE_BLUE)
        surf.blit(lbl, (cx - 200 - lbl.get_width() // 2, cy + 24))

        # P2 score (right)
        lbl = f_small.render("P2 — RED", True, ALLIANCE_RED)
        surf.blit(lbl, (cx + 200 - lbl.get_width() // 2, cy))
        lbl = f_hud.render(str(s2), True, ALLIANCE_RED)
        surf.blit(lbl, (cx + 200 - lbl.get_width() // 2, cy + 24))

        cy += 80

        # Winner
        if s1 > s2:
            winner, wclr = "P1 WINS", ALLIANCE_BLUE
        elif s2 > s1:
            winner, wclr = "P2 WINS", ALLIANCE_RED
        else:
            winner, wclr = "TIE", GOLD
        lbl = f_hud.render(winner, True, wclr)
        surf.blit(lbl, (cx - lbl.get_width() // 2, cy))
        cy += f_hud.get_height() + 16

        # Breakdowns side by side
        bx1 = cx - 200
        bx2 = cx + 200
        for team, bx, color in [(state.team, bx1, ALLIANCE_BLUE), (state.team2, bx2, ALLIANCE_RED)]:
            lines = [
                f"Cls: {team.classified}  Ovf: {team.overflow}  Depot: {team.depot}",
                f"Pattern: {team.pattern_pts}  Base: {team.base_pts}",
            ]
            for i, line in enumerate(lines):
                lbl = f_tiny.render(line, True, color)
                surf.blit(lbl, (bx - lbl.get_width() // 2, cy + i * 18))
        cy += 40
    else:
        # Solo: original layout
        t = state.team
        lbl = f_hud.render(f"FINAL SCORE: {t.total_score(state.chaos_active)}", True, WHITE)
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
        cy += 20

    # Buttons
    btn_w = 200
    btn_h = 44
    btn_gap = 30
    btn_y = H - 100
    _end_btn_rects[0] = pygame.Rect(cx - btn_w - btn_gap // 2, btn_y, btn_w, btn_h)
    _end_btn_rects[1] = pygame.Rect(cx + btn_gap // 2, btn_y, btn_w, btn_h)

    for i, (label, rect) in enumerate(zip(["RESTART", "EXIT TO MENU"], _end_btn_rects)):
        pygame.draw.rect(surf, MENU_BG, rect, border_radius=6)
        pygame.draw.rect(surf, MENU_BORDER, rect, 1, border_radius=6)
        lbl = f_small.render(label, True, MENU_TEXT)
        surf.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                        rect.centery - lbl.get_height() // 2))

    _end_overlay = surf


_end_btn_rects = [None, None]


def draw_match_end(screen, state):
    """Draw the match-end overlay with caching."""
    global _end_overlay
    if state.phase != "FINISHED":
        _end_overlay = None
        return
    if _end_overlay is None:
        _build_end_overlay(state)
    screen.blit(_end_overlay, (0, 0))


def draw_match_end_buttons(screen, state, end_menu_index):
    """Draw highlight on top of the already-blitted match-end overlay."""
    if state.phase != "FINISHED":
        return
    if _end_btn_rects[0] is None:
        return
    rect = _end_btn_rects[end_menu_index]
    if rect is not None:
        pygame.draw.rect(screen, MENU_HIGHLIGHT_BORDER, rect, 3, border_radius=6)


# ============================================================
# PAUSE MENU
# ============================================================
_PAUSE_MENU_BUTTONS = ["Resume", "Restart Game", "Detect Gamepads", "Options", "Mode Select", "Quit"]
_pause_menu_rects = []


def draw_pause_menu(screen, state):
    """Draw the pause menu overlay with selectable buttons."""
    global _pause_menu_rects

    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill(PAUSE_OVERLAY)
    screen.blit(overlay, (0, 0))

    panel_w, panel_h = 320, 442
    # Shrink panel when Options is hidden (1v1)
    if state.game_mode == "1v1":
        panel_h -= 52
    panel_x = (W - panel_w) // 2
    panel_y = (H - panel_h) // 2

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((*MENU_BG, 240))
    pygame.draw.rect(panel, MENU_BORDER, (0, 0, panel_w, panel_h), 2, border_radius=8)
    screen.blit(panel, (panel_x, panel_y))

    title = f_hud.render("PAUSED", True, MENU_TITLE)
    screen.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 20))

    pygame.draw.line(screen, MENU_BORDER, (panel_x + 20, panel_y + 65), (panel_x + panel_w - 20, panel_y + 65), 1)

    _pause_menu_rects = []
    btn_w = 240
    btn_h = 42
    btn_x = panel_x + (panel_w - btn_w) // 2
    start_y = panel_y + 85
    gap = 52

    # In 1v1, hide the Options button (keybinds are locked to defaults)
    buttons = [b for b in _PAUSE_MENU_BUTTONS if b != "Options" or state.game_mode != "1v1"]

    for i, label in enumerate(buttons):
        btn_y = start_y + i * gap
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        _pause_menu_rects.append(btn_rect)

        if i == state.pause_menu_index:
            pygame.draw.rect(screen, MENU_HIGHLIGHT_BG, btn_rect, border_radius=6)
            pygame.draw.rect(screen, MENU_HIGHLIGHT_BORDER, btn_rect, 2, border_radius=6)
            txt = f_small.render(label, True, MENU_HIGHLIGHT_BORDER)
        else:
            pygame.draw.rect(screen, (*MENU_BG, 200), btn_rect, border_radius=6)
            pygame.draw.rect(screen, (*MENU_BORDER, 120), btn_rect, 1, border_radius=6)
            txt = f_small.render(label, True, MENU_TEXT)

        screen.blit(txt, (btn_rect.centerx - txt.get_width() // 2,
                          btn_rect.centery - txt.get_height() // 2))

    hint = f_tiny.render("Up/Down: navigate  Enter: select", True, GRAY)
    screen.blit(hint, (panel_x + panel_w // 2 - hint.get_width() // 2,
                       panel_y + panel_h - 40))

    # ── Team ZENITH watermark ────────────────────────────────────────────────
    wm_surf = f_micro.render(ZENITH_LABEL, True, ZENITH_PURPLE)
    wm_surf.set_alpha(80)
    wm_rect = wm_surf.get_rect(center=(panel_x + panel_w // 2, panel_y + panel_h - 14))
    screen.blit(wm_surf, wm_rect)
    # ─────────────────────────────────────────────────────────────────────────


# ============================================================
# OPTIONS SCREEN
# ============================================================
def draw_options_screen(screen, state):
    """Full-screen overlay for keybind customization."""
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill(PAUSE_OVERLAY)
    screen.blit(overlay, (0, 0))

    panel_w, panel_h = 700, 520
    panel_x = (W - panel_w) // 2
    panel_y = (H - panel_h) // 2
    pygame.draw.rect(screen, MENU_BG, (panel_x, panel_y, panel_w, panel_h), border_radius=10)
    pygame.draw.rect(screen, MENU_BORDER, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

    title = f_hud.render("OPTIONS", True, MENU_TITLE)
    screen.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 16))

    pygame.draw.line(screen, MENU_BORDER,
                     (panel_x + 20, panel_y + 60),
                     (panel_x + panel_w - 20, panel_y + 60), 1)

    tab_labels = ["KEYBOARD", "GAMEPAD"]
    tab_w = 140
    tab_h = 30
    tab_gap = 20
    tabs_total_w = len(tab_labels) * tab_w + (len(tab_labels) - 1) * tab_gap
    tab_start_x = panel_x + (panel_w - tabs_total_w) // 2
    tab_y = panel_y + 72

    for i, label in enumerate(tab_labels):
        tx = tab_start_x + i * (tab_w + tab_gap)
        rect = pygame.Rect(tx, tab_y, tab_w, tab_h)
        if i == state.options_page:
            pygame.draw.rect(screen, MENU_HIGHLIGHT_BG, rect, border_radius=5)
            pygame.draw.rect(screen, MENU_HIGHLIGHT_BORDER, rect, 2, border_radius=5)
            txt = f_tiny.render(label, True, MENU_HIGHLIGHT_BORDER)
        else:
            pygame.draw.rect(screen, (*MENU_BG, 200), rect, border_radius=5)
            pygame.draw.rect(screen, (*MENU_BORDER, 120), rect, 1, border_radius=5)
            txt = f_tiny.render(label, True, MENU_TEXT)
        screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                          rect.centery - txt.get_height() // 2))

    if state.options_page == 0:
        from config import KEYBIND_ACTIONS_KEYBOARD
        actions = KEYBIND_ACTIONS_KEYBOARD
    else:
        from config import KEYBIND_ACTIONS_GAMEPAD
        actions = KEYBIND_ACTIONS_GAMEPAD

    page_name = "keyboard" if state.options_page == 0 else "gamepad"
    binds = state.keybinds.get(page_name, {})
    num_rows = len(actions) + 1  # +1 for Reset to Default row

    row_y = tab_y + 48
    row_h = 32
    col_action_x = panel_x + 30
    col_bind_x = panel_x + panel_w - 200

    dup_actions = set()
    binding_to_actions = {}
    for a in actions:
        b = binds.get(a)
        if b:
            binding_to_actions.setdefault(b, []).append(a)
    for b, acts in binding_to_actions.items():
        if len(acts) > 1:
            dup_actions.update(acts)

    for i, action in enumerate(actions):
        ry = row_y + i * row_h
        is_selected = (i == state.options_index)

        if is_selected:
            sel_rect = pygame.Rect(panel_x + 15, ry - 2, panel_w - 30, row_h)
            if state.options_rebinding:
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.006)) * 0.4 + 0.6
                c = tuple(int(v * pulse) for v in OPTIONS_REBIND)
                pygame.draw.rect(screen, c, sel_rect, border_radius=4)
            else:
                pygame.draw.rect(screen, MENU_HIGHLIGHT_BG, sel_rect, border_radius=4)

        action_txt = f_tiny.render(action, True, MENU_HIGHLIGHT_BORDER if is_selected else MENU_TEXT)
        screen.blit(action_txt, (col_action_x, ry + 6))

        binding = binds.get(action)
        if binding:
            if binding[0] == "key":
                key_name = pygame.key.name(binding[1]).upper()
                bind_str = key_name
            elif binding[0] == "button":
                bind_str = GAMEPAD_NAMES.get(binding, f"Btn {binding[1]}")
            elif binding[0] == "axis":
                bind_str = GAMEPAD_NAMES.get(binding, f"Axis {binding[1]}")
            else:
                bind_str = "?"
        else:
            bind_str = "—"

        if state.options_rebinding and is_selected:
            bind_color = OPTIONS_REBIND
            bind_str = "..."
        elif is_selected:
            bind_color = OPTIONS_BIND
        else:
            bind_color = GRAY

        if action in LOCKED_KEYBINDS.get(page_name, set()):
            bind_str = "(Fixed)"
            bind_color = GRAY

        bind_txt = f_tiny.render(bind_str, True, bind_color)
        screen.blit(bind_txt, (col_bind_x, ry + 6))

        if action in dup_actions:
            warn = f_tiny.render("!", True, RED_ACCENT)
            screen.blit(warn, (col_bind_x - 20, ry + 6))

    reset_y = row_y + (num_rows - 1) * row_h + 4
    is_reset_selected = (state.options_index == num_rows - 1)
    if is_reset_selected:
        reset_rect = pygame.Rect(panel_x + 15, reset_y - 2, panel_w - 30, row_h)
        pygame.draw.rect(screen, MENU_HIGHLIGHT_BG, reset_rect, border_radius=4)
    reset_label = "Reset to Default"
    reset_color = MENU_HIGHLIGHT_BORDER if is_reset_selected else MENU_TEXT
    reset_txt = f_tiny.render(reset_label, True, reset_color)
    screen.blit(reset_txt, (col_action_x, reset_y + 6))
    if is_reset_selected:
        reset_hint = f_tiny.render("(press Enter)", True, OPTIONS_BIND)
        screen.blit(reset_hint, (col_bind_x, reset_y + 6))

    hint_y = panel_y + panel_h - 32
    hint1 = f_tiny.render("Up/Down: navigate  Enter/A: rebind/select  Backspace/B: back", True, GRAY)
    screen.blit(hint1, (panel_x + panel_w // 2 - hint1.get_width() // 2, hint_y))
