"""
FTC DECODE — Mode-select and controller-assignment screens.
"""

import math
import pygame
import drawing as _drawing
from config import (
    W, H, BG_DARK, GRAY, SOFT_WHITE, GOLD, ORANGE, RED_ACCENT,
    ZENITH_PURPLE, ZENITH_ACCENT, ZENITH_DARK, ZENITH_LABEL, ZENITH_TAG,
    ALLIANCE_BLUE, ALLIANCE_RED,
    MENU_BG, MENU_BORDER, MENU_HIGHLIGHT_BG, MENU_HIGHLIGHT_BORDER, MENU_TEXT,
    MENU_TITLE,
)

_MENU_NAV_DELAY_MS = 200
_mode_nav_cooldown = {}


def draw_mode_select(screen, selected_index):
    """Draw the mode-select screen onto the virtual canvas."""
    screen.fill(BG_DARK)

    cx = W // 2
    cy = H // 2 - 40

    lbl = _drawing.f_huge.render("FTC DECODE", True, ZENITH_ACCENT)
    screen.blit(lbl, (cx - lbl.get_width() // 2, cy - 80))

    sub = _drawing.f_small.render("MATCH SIMULATOR  —  TEAM ZENITH 19084", True, SOFT_WHITE)
    screen.blit(sub, (cx - sub.get_width() // 2, cy - 10))

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

        if i == selected_index:
            pygame.draw.rect(screen, MENU_HIGHLIGHT_BG, rect, border_radius=8)
            pygame.draw.rect(screen, MENU_HIGHLIGHT_BORDER, rect, 2, border_radius=8)
            txt = _drawing.f_small.render(label, True, MENU_HIGHLIGHT_BORDER)
        else:
            pygame.draw.rect(screen, MENU_BG, rect, border_radius=8)
            pygame.draw.rect(screen, MENU_BORDER, rect, 1, border_radius=8)
            txt = _drawing.f_small.render(label, True, MENU_TEXT)

        screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                          rect.centery - txt.get_height() // 2))

    hint = _drawing.f_tiny.render("Up/Down: navigate    Enter: select", True, GRAY)
    screen.blit(hint, (cx - hint.get_width() // 2, H - 60))

    wm = _drawing.f_micro.render(ZENITH_LABEL, True, ZENITH_PURPLE)
    wm.set_alpha(80)
    screen.blit(wm, (cx - wm.get_width() // 2, H - 35))


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



