"""
FTC DECODE — P2 robot and 1v1 field rendering (multi-player only).
"""

import math

import pygame
import drawing as _d
from config import (
    CONFIG, FX, FY, FS,
    SOFT_WHITE, ALLIANCE_RED,
)
from drawing import (
    _build_robot_surface,
    _robot_cache_key,
    _robot_cache,
    _robot_cache_order,
    _ROBOT_CACHE_MAX,
)


def draw_robot2(screen, state):
    """Draw P2 robot in 1v1 mode."""
    if state.game_mode != "1v1" or state.robot2 is None:
        return
    r = state.robot2
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


def draw_field_1v1_extras(screen, state):
    """Draw P2 base zone and loading zone in 1v1 mode."""
    if state.game_mode != "1v1":
        return

    # P2 base zone (mirrored, right-center of field)
    br2 = state.base_rect2()
    base_fill = pygame.Surface((br2.w, br2.h), pygame.SRCALPHA)
    base_fill.fill((ALLIANCE_RED[0], ALLIANCE_RED[1], ALLIANCE_RED[2], 50))
    screen.blit(base_fill, (br2.x, br2.y))
    if state.park_status2 == "PARTIAL":
        t_ms = pygame.time.get_ticks()
        alpha = int(80 + 120 * (0.5 + 0.5 * math.sin(t_ms * 2 * math.pi / 1500)))
        pulse_s = pygame.Surface((br2.w + 8, br2.h + 8), pygame.SRCALPHA)
        pygame.draw.rect(pulse_s, (*ALLIANCE_RED, alpha), (0, 0, br2.w + 8, br2.h + 8), 3, border_radius=4)
        screen.blit(pulse_s, (br2.x - 4, br2.y - 4))
    elif state.park_status2 == "FULL":
        glow_s = pygame.Surface((br2.w, br2.h), pygame.SRCALPHA)
        glow_s.fill((*ALLIANCE_RED, 60))
        screen.blit(glow_s, (br2.x, br2.y))
    pygame.draw.rect(screen, ALLIANCE_RED, br2, 2, border_radius=3)
    lbl = _d.f_small.render("BASE", True, ALLIANCE_RED)
    screen.blit(lbl, (br2.centerx - lbl.get_width() // 2, br2.centery - lbl.get_height() // 2))

    # P2 loading zone (mirrored, top-right — white like P1's)
    lr2 = state.loading_rect2()
    s2 = pygame.Surface((lr2.w, lr2.h), pygame.SRCALPHA)
    s2.fill((60, 60, 70, 60))
    screen.blit(s2, (lr2.x, lr2.y))
    pygame.draw.rect(screen, SOFT_WHITE, lr2, 2, border_radius=3)
    lbl = _d.f_tiny.render("LOAD ZONE", True, SOFT_WHITE)
    screen.blit(lbl, (lr2.centerx - lbl.get_width() // 2, lr2.centery - lbl.get_height() // 2))
