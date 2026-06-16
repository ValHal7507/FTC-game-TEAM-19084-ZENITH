"""
FTC DECODE — Mode-select and controller-assignment screens.
"""

import math
import pygame
import drawing as _drawing
from config import (
    W, H, VW, VH, BG_DARK, GRAY, SOFT_WHITE, GOLD, ORANGE, RED_ACCENT,
    ZENITH_PURPLE, ZENITH_ACCENT, ZENITH_DARK, ZENITH_LABEL, ZENITH_TAG,
    ALLIANCE_BLUE, ALLIANCE_RED,
    MENU_BG, MENU_BORDER, MENU_HIGHLIGHT_BG, MENU_HIGHLIGHT_BORDER, MENU_TEXT,
    MENU_TITLE,
    MC_NAVY, MC_MID_BLUE, MC_LIGHT_BLUE, MC_PURPLE, MC_LAVENDER, MC_WHITE_ARM,
    MC_CAPE, MC_FL_BLUE, MC_FL_PURPLE, MC_FL_GREEN, MC_FL_YELLOW,
)

_MENU_NAV_DELAY_MS = 200
_mode_nav_cooldown = {}

_bubble_font = None


def draw_mascot(surf, cx, cy, t):
    """Draw the procedural ZENITH mascot (chibi robot-knight), torso-center at (cx, cy)."""
    bob = int(math.sin(t * 2.0) * 4)
    fw  = math.sin(t * 3.5) * 6
    cs  = math.sin(t * 1.8) * 3

    def y(off): return cy + off + bob

    # CAPE (behind everything)
    cape_l = [(cx-18, y(-45)), (cx-44+cs, y(-25)), (cx-60+cs, y(12)),
              (cx-50+cs, y(58)), (cx-20, y(68)), (cx-8, y(18))]
    cape_r = [(cx+16, y(-45)), (cx+32, y(-32)), (cx+30, y(32)),
              (cx+16, y(68)), (cx+6, y(18))]
    for pts in (cape_l, cape_r):
        pygame.draw.polygon(surf, MC_CAPE, pts)
        pygame.draw.polygon(surf, MC_NAVY, pts, 2)

    # THIGHS
    pygame.draw.rect(surf, MC_NAVY, (cx-26, y(30), 20, 30))
    pygame.draw.rect(surf, MC_NAVY, (cx+6,  y(30), 20, 30))

    # SHIN GUARDS
    for sx in (cx-28, cx+6):
        pygame.draw.rect(surf, MC_WHITE_ARM, (sx, y(58), 22, 32), border_radius=4)
        pygame.draw.rect(surf, MC_NAVY,      (sx, y(58), 22, 32), 2, border_radius=4)

    # FEET
    for fx in (cx-32, cx+4):
        pygame.draw.ellipse(surf, MC_NAVY,  (fx, y(87), 28, 14))
        pygame.draw.rect(surf,   MC_PURPLE, (fx+2, y(89), 24, 5))

    # TORSO
    torso = pygame.Rect(cx-28, y(-40), 56, 58)
    pygame.draw.rect(surf, MC_WHITE_ARM, torso, border_radius=8)
    pygame.draw.rect(surf, MC_NAVY,      torso, 2, border_radius=8)

    # Atom symbol on chest (3 rotated ellipses + center dot)
    acx, acy = cx, y(-12)
    for deg in (0, 60, 120):
        es = pygame.Surface((30, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(es, MC_LIGHT_BLUE, es.get_rect(), 2)
        rs = pygame.transform.rotate(es, deg)
        surf.blit(rs, (acx - rs.get_width()//2, acy - rs.get_height()//2))
    pygame.draw.circle(surf, MC_PURPLE, (acx, acy), 5)

    # WAIST
    pygame.draw.rect(surf, MC_PURPLE, (cx-18, y(18), 36, 14), border_radius=3)

    # LEFT ARM
    pygame.draw.rect(surf,   MC_NAVY,   (cx-46, y(-30), 18, 40), border_radius=4)
    pygame.draw.circle(surf, MC_PURPLE, (cx-37, y(12)), 7)
    pygame.draw.rect(surf,   MC_NAVY,   (cx-48, y(18), 22, 14), border_radius=3)

    # RIGHT ARM (flag side)
    pygame.draw.rect(surf,   MC_NAVY,   (cx+28, y(-28), 18, 44), border_radius=4)
    pygame.draw.circle(surf, MC_PURPLE, (cx+37, y(18)), 7)
    pygame.draw.rect(surf,   MC_NAVY,   (cx+36, y(22), 18, 12), border_radius=3)

    # FLAGPOLE
    pygame.draw.line(surf, MC_PURPLE, (cx+50, y(28)), (cx+50, y(-85)), 3)
    pygame.draw.circle(surf, MC_LAVENDER, (cx+50, y(-86)), 5)

    # FLAG (animated wave)
    flag_pts = [(cx+50, y(-85)),
                (cx+92, int(y(-80)+fw)),
                (cx+90, int(y(-65)+fw*0.7)),
                (cx+50, y(-60))]
    pygame.draw.polygon(surf, MC_PURPLE, flag_pts)
    pygame.draw.polygon(surf, MC_NAVY,   flag_pts, 2)
    # Atom on flag
    fax = cx + 72 + int(fw * 0.3)
    fay = y(-72)
    for deg in (0, 60, 120):
        es = pygame.Surface((18, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(es, MC_LIGHT_BLUE, es.get_rect(), 1)
        rs = pygame.transform.rotate(es, deg)
        surf.blit(rs, (fax - rs.get_width()//2, fay - rs.get_height()//2))
    pygame.draw.circle(surf, MC_FL_PURPLE, (fax, fay), 3)

    # SHOULDER PADS
    for spx in (cx-32, cx+32):
        pygame.draw.circle(surf, MC_MID_BLUE, (spx, y(-32)), 16)
        pygame.draw.circle(surf, MC_LAVENDER, (spx, y(-32)), 16, 2)
    pygame.draw.circle(surf, MC_LIGHT_BLUE, (cx-32, y(-32)), 5, 1)  # atom on left pad

    # HEAD dome
    pygame.draw.circle(surf, MC_MID_BLUE, (cx, y(-70)), 30)
    pygame.draw.circle(surf, MC_NAVY,     (cx, y(-70)), 30, 2)

    # EARS (cat, dark navy outer / white inner tip)
    el = [(cx-12, y(-92)), (cx-26, y(-116)), (cx-2,  y(-112))]
    er = [(cx+12, y(-92)), (cx+26, y(-116)), (cx+2,  y(-112))]
    il = [(cx-14, y(-97)), (cx-22, y(-110)), (cx-7,  y(-107))]
    ir = [(cx+14, y(-97)), (cx+22, y(-110)), (cx+7,  y(-107))]
    for pts, col in [(el, MC_MID_BLUE), (er, MC_MID_BLUE),
                     (il, MC_WHITE_ARM), (ir, MC_WHITE_ARM)]:
        pygame.draw.polygon(surf, col, pts)
    for pts in (el, er):
        pygame.draw.polygon(surf, MC_NAVY, pts, 2)

    # VISOR
    vr = pygame.Rect(cx-22, y(-82), 44, 20)
    pygame.draw.rect(surf, MC_LIGHT_BLUE, vr, border_radius=5)
    pygame.draw.rect(surf, MC_NAVY,       vr, 2, border_radius=5)
    if (t % 4.0) < 0.15:   # blink
        pygame.draw.rect(surf, MC_MID_BLUE, vr, border_radius=5)
    else:                   # happy squint lines
        pygame.draw.line(surf, MC_NAVY, (cx-14, y(-72)), (cx-4,  y(-72)), 3)
        pygame.draw.line(surf, MC_NAVY, (cx+4,  y(-72)), (cx+14, y(-72)), 3)

    # CHIN GUARD (3 vertical slits)
    pygame.draw.rect(surf, MC_NAVY, (cx-16, y(-62), 32, 12), border_radius=3)
    for i in range(3):
        sx = cx - 8 + i * 8
        pygame.draw.line(surf, MC_LIGHT_BLUE, (sx, y(-61)), (sx, y(-52)), 2)

    # FLOWER CROWN
    crown = [(cx-20, y(-108), MC_FL_BLUE),   (cx-8, y(-113), MC_FL_PURPLE),
             (cx,    y(-116), MC_FL_BLUE),   (cx+8, y(-113), MC_FL_PURPLE),
             (cx+20, y(-108), MC_FL_BLUE)]
    for fx, fy, fc in crown:
        for i in range(5):
            a = math.radians(i * 72)
            pygame.draw.circle(surf, fc, (int(fx+math.cos(a)*5), int(fy+math.sin(a)*5)), 4)
        pygame.draw.circle(surf, MC_FL_YELLOW, (fx, fy), 3)
    for lx, ly in [(cx-14, y(-111)), (cx+14, y(-111))]:
        pygame.draw.ellipse(surf, MC_FL_GREEN, (lx-4, ly-3, 8, 6))


def draw_speech_bubble(surf, bx, by, t):
    """Draw a typewriter-effect speech bubble. bx = horizontal center, by = bottom edge (tail tip)."""
    global _bubble_font
    if _bubble_font is None:
        _bubble_font = pygame.font.SysFont("Arial", 17)
    font = _bubble_font

    full = "Hi! I am the mascot of Team 19084 ZENITH, enjoy our game!"
    chars = min(len(full), int((t % 5.5) * 28))
    displayed = full[:chars]

    # Word-wrap to 260px
    words = displayed.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= 260:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    if not lines: lines = [""]

    pad = 12
    lh  = font.get_linesize()
    bw  = 284
    bh  = lh * len(lines) + pad * 2
    rx  = bx - bw // 2
    ry  = by - bh

    pygame.draw.rect(surf, MC_WHITE_ARM, (rx, ry, bw, bh), border_radius=10)
    pygame.draw.rect(surf, MC_PURPLE,   (rx, ry, bw, bh), 2, border_radius=10)
    tail = [(bx-8, ry+bh), (bx-22, ry+bh+14), (bx+8, ry+bh)]
    pygame.draw.polygon(surf, MC_WHITE_ARM, tail)
    pygame.draw.lines(surf, MC_PURPLE, False, [tail[0], tail[1], tail[2]], 2)
    for i, line in enumerate(lines):
        ts = font.render(line, True, MC_NAVY)
        surf.blit(ts, (bx - ts.get_width()//2, ry + pad + i * lh))


def draw_mode_select(surf, menu_selected, t=0.0):
    """Draw the mode-select screen onto the virtual canvas."""
    surf.fill(BG_DARK)

    cx = int(W * 0.33)
    cy = H // 2 - 40

    lbl = _drawing.f_huge.render("FTC DECODE", True, ZENITH_ACCENT)
    surf.blit(lbl, (cx - lbl.get_width() // 2, cy - 80))

    sub = _drawing.f_small.render("MATCH SIMULATOR  —  TEAM ZENITH 19084", True, SOFT_WHITE)
    surf.blit(sub, (cx - sub.get_width() // 2, cy - 10))

    modes = [
        ("SOLO PRACTICE", 0),
        ("1v1 LOCAL", 1),
        # ("vs AI", 2),  # temporarily disabled
    ]

    btn_w = 400
    btn_h = 64
    btn_gap = 20
    total_h = len(modes) * btn_h + (len(modes) - 1) * btn_gap
    start_y = cy + 50

    for i, (label, idx) in enumerate(modes):
        bx = cx - btn_w // 2
        by = start_y + i * (btn_h + btn_gap)
        rect = pygame.Rect(bx, by, btn_w, btn_h)

        if i == menu_selected:
            pygame.draw.rect(surf, MENU_HIGHLIGHT_BG, rect, border_radius=8)
            pygame.draw.rect(surf, MENU_HIGHLIGHT_BORDER, rect, 2, border_radius=8)
            txt = _drawing.f_small.render(label, True, MENU_HIGHLIGHT_BORDER)
        else:
            pygame.draw.rect(surf, MENU_BG, rect, border_radius=8)
            pygame.draw.rect(surf, MENU_BORDER, rect, 1, border_radius=8)
            txt = _drawing.f_small.render(label, True, MENU_TEXT)

        surf.blit(txt, (rect.centerx - txt.get_width() // 2,
                          rect.centery - txt.get_height() // 2))

    hint = _drawing.f_tiny.render("Up/Down: navigate    Enter: select", True, GRAY)
    surf.blit(hint, (cx - hint.get_width() // 2, H - 60))

    wm = _drawing.f_micro.render(ZENITH_LABEL, True, ZENITH_PURPLE)
    wm.set_alpha(80)
    surf.blit(wm, (cx - wm.get_width() // 2, H - 35))

    mascot_cx = int(VW * 0.78)
    mascot_cy = int(VH * 0.56)
    draw_mascot(surf, mascot_cx, mascot_cy, t)
    bubble_y = mascot_cy - 108 + int(math.sin(t * 2.0) * 4)
    draw_speech_bubble(surf, mascot_cx - 20, bubble_y, t)


def handle_mode_select(events, keys, selected_index):
    """Process input for mode-select screen.

    Returns (new_selected_index, chosen_mode | None).
    """
    chosen = None
    now = pygame.time.get_ticks()
    last = _mode_nav_cooldown.get("mode", 0)
    if now - last < _MENU_NAV_DELAY_MS:
        return selected_index, chosen

    for e in events:
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w, pygame.K_KP8):
                selected_index = (selected_index - 1) % 2
                _mode_nav_cooldown["mode"] = now
                return selected_index, chosen
            elif e.key in (pygame.K_DOWN, pygame.K_s, pygame.K_KP2):
                selected_index = (selected_index + 1) % 2
                _mode_nav_cooldown["mode"] = now
                return selected_index, chosen
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                if selected_index == 0:
                    chosen = "solo"
                elif selected_index == 1:
                    chosen = "1v1"
                return selected_index, chosen

    return selected_index, chosen


def draw_controller_assign(screen, selected_p1, selected_p2, num_joysticks, conflict,
                           game_mode="1v1"):
    """Draw the controller-assignment screen for 1v1 mode."""
    screen.fill(BG_DARK)

    cx = W // 2
    title = _drawing.f_hud.render("ASSIGN CONTROLLERS", True, ZENITH_ACCENT)
    screen.blit(title, (cx - title.get_width() // 2, 80))

    col_w = 260
    col_gap = 80
    left_x = cx - col_w - col_gap // 2
    right_x = cx + col_gap // 2

    p1_hdr = _drawing.f_small.render("PLAYER 1", True, ALLIANCE_BLUE)
    screen.blit(p1_hdr, (left_x + col_w // 2 - p1_hdr.get_width() // 2, 150))

    p2_hdr = _drawing.f_small.render("PLAYER 2", True, ALLIANCE_RED)
    screen.blit(p2_hdr, (right_x + col_w // 2 - p2_hdr.get_width() // 2, 150))

    p1_devices = ["Gamepad 1", "Gamepad 2"]
    p2_devices = ["Gamepad 1", "Gamepad 2", "AI"]
    p1_found = [num_joysticks >= 1, num_joysticks >= 2]
    p2_found = [num_joysticks >= 1, num_joysticks >= 2, True]

    btn_h = 44
    btn_gap = 12
    row_y = 195

    cols_to_draw = [
        (selected_p1, ALLIANCE_BLUE, left_x, p1_devices, p1_found),
        (selected_p2, ALLIANCE_RED, right_x, p2_devices, p2_found),
    ]

    for sel, hdr_color, base_x, devices, found in cols_to_draw:
        for i, dev_label in enumerate(devices):
            ry = row_y + i * (btn_h + btn_gap)
            rect = pygame.Rect(base_x, ry, col_w, btn_h)

            if not found[i]:
                pygame.draw.rect(screen, (25, 25, 30), rect, border_radius=6)
                pygame.draw.rect(screen, (40, 40, 45), rect, 1, border_radius=6)
                lbl = _drawing.f_tiny.render(f"{dev_label}  (not found)", True, (80, 80, 85))
                screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                                  rect.centery - lbl.get_height() // 2))
            elif i == sel:
                pygame.draw.rect(screen, MENU_HIGHLIGHT_BG, rect, border_radius=6)
                pygame.draw.rect(screen, hdr_color, rect, 2, border_radius=6)
                lbl = _drawing.f_tiny.render(dev_label, True, hdr_color)
                screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                                  rect.centery - lbl.get_height() // 2))
            else:
                pygame.draw.rect(screen, MENU_BG, rect, border_radius=6)
                pygame.draw.rect(screen, MENU_BORDER, rect, 1, border_radius=6)
                lbl = _drawing.f_tiny.render(dev_label, True, MENU_TEXT)
                screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                                  rect.centery - lbl.get_height() // 2))

    if conflict:
        warn = _drawing.f_tiny.render("! Both players cannot share the same gamepad", True, RED_ACCENT)
        screen.blit(warn, (cx - warn.get_width() // 2, row_y + 3 * (btn_h + btn_gap) + 20))

    hint = _drawing.f_tiny.render(
        "Left/Right: switch player    Up/Down: select device    Enter: confirm",
        True, GRAY)
    screen.blit(hint, (cx - hint.get_width() // 2, H - 80))

    back_lbl = _drawing.f_tiny.render("ESC: back", True, GRAY)
    screen.blit(back_lbl, (40, H - 40))


def handle_controller_assign(events, keys, selected_p1, selected_p2, focused_col, num_joysticks,
                             game_mode="1v1"):
    """Process input for controller-assign screen.

    Returns (new_p1, new_p2, new_focused_col, result).
    result is None | "back" | (p1_device_str, p2_device_str).
    P1 devices: gamepad0, gamepad1.  P2 devices: gamepad0, gamepad1, ai.
    """
    result = None
    now = pygame.time.get_ticks()
    last = _mode_nav_cooldown.get("ca", 0)
    if now - last < _MENU_NAV_DELAY_MS:
        return selected_p1, selected_p2, focused_col, result

    p1_found = [num_joysticks >= 1, num_joysticks >= 2]
    p2_found = [num_joysticks >= 1, num_joysticks >= 2, True]
    p1_dev_names = ["gamepad0", "gamepad1"]
    p2_dev_names = ["gamepad0", "gamepad1", "ai"]
    p1_max = len(p1_dev_names) - 1
    p2_max = len(p2_dev_names) - 1

    for e in events:
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                return selected_p1, selected_p2, focused_col, "back"
            elif e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_KP4):
                focused_col = 0
                _mode_nav_cooldown["ca"] = now
                return selected_p1, selected_p2, focused_col, result
            elif e.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_KP6):
                focused_col = 1
                _mode_nav_cooldown["ca"] = now
                return selected_p1, selected_p2, focused_col, result
            elif e.key in (pygame.K_UP, pygame.K_w, pygame.K_KP8):
                if focused_col == 0:
                    selected_p1 = max(0, selected_p1 - 1)
                else:
                    selected_p2 = max(0, selected_p2 - 1)
                _mode_nav_cooldown["ca"] = now
                return selected_p1, selected_p2, focused_col, result
            elif e.key in (pygame.K_DOWN, pygame.K_s, pygame.K_KP2):
                if focused_col == 0:
                    selected_p1 = min(p1_max, selected_p1 + 1)
                else:
                    selected_p2 = min(p2_max, selected_p2 + 1)
                _mode_nav_cooldown["ca"] = now
                return selected_p1, selected_p2, focused_col, result
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                if not p1_found[selected_p1] or not p2_found[selected_p2]:
                    return selected_p1, selected_p2, focused_col, result
                if selected_p1 == selected_p2:
                    return selected_p1, selected_p2, focused_col, result
                result = (p1_dev_names[selected_p1], p2_dev_names[selected_p2])
                return selected_p1, selected_p2, focused_col, result

    return selected_p1, selected_p2, focused_col, result