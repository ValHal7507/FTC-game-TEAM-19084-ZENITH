"""
FTC DECODE (2025-2026) Match Simulator — Entry point.
Thin dispatcher: init, menu routing, dispatch to mode files.
"""

import ctypes
import os
import sys
import pygame
import menu as menu_mod
import mode_solo
import mode_1v1
from config import CONFIG, VW, VH, BG_DARK, BLACK, render_surf
from drawing import init_drawing
from game_logic import rebuild_obstacle_cache
from input_handler import init_joysticks
from game_state import GameState


def _blit_scaled(canvas, screen):
    """Scale the virtual canvas to the window, preserving aspect ratio with letterbox."""
    win_w, win_h = screen.get_size()
    sx = win_w / VW
    sy = win_h / VH
    sf = min(sx, sy)
    scaled_w = int(VW * sf)
    scaled_h = int(VH * sf)
    ox = (win_w - scaled_w) // 2
    oy = (win_h - scaled_h) // 2
    scaled = pygame.transform.smoothscale(canvas, (scaled_w, scaled_h))
    screen.fill(BLACK)
    screen.blit(scaled, (ox, oy))


def main():
    pygame.init()
    global render_surf
    _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Zenith_logo.png")
    if os.path.isfile(_icon_path):
        try:
            pygame.display.set_icon(pygame.image.load(_icon_path))
        except Exception:
            pass
    win = pygame.display.set_mode((VW, VH), pygame.RESIZABLE)
    pygame.display.set_caption("FTC DECODE — Robot simulator by TEAM ZENITH 19084")
    ctypes.windll.user32.ShowWindow(pygame.display.get_wm_info()['window'], 3)
    render_surf = pygame.Surface((VW, VH))
    clock = pygame.time.Clock()
    init_drawing()

    gpad_count = pygame.joystick.get_count()
    print(f"Detected {gpad_count} gamepad(s)")
    init_joysticks()

    # ── App-level screen state ──────────────────────────────────────────
    app_screen = "mode_select"   # "mode_select" | "controller_assign" | "game"
    menu_selected = 0
    ca_p1 = 0
    ca_p2 = 1
    ca_col = 0
    chosen_mode = "solo"
    state = None

    t = 0.0
    try:
        while True:
            # ── OUTER LOOP: mode select + controller assign ─────────────
            while app_screen in ("mode_select", "controller_assign"):
                dt_menu = clock.tick_busy_loop(60) / 1000.0
                t += dt_menu
                events = pygame.event.get()
                keys = pygame.key.get_pressed()

                for ev in events:
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if ev.type == pygame.VIDEORESIZE:
                        pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)

                if app_screen == "mode_select":
                    menu_selected, result = menu_mod.handle_mode_select(events, keys, menu_selected)
                    if result == "solo":
                        chosen_mode = "solo"
                        state = GameState(game_mode="solo")
                        rebuild_obstacle_cache(state)
                        app_screen = "game"
                    elif result == "1v1":
                        chosen_mode = "1v1"
                        num_joy = pygame.joystick.get_count()
                        if num_joy >= 2:
                            ca_p1 = 0  # Gamepad 1
                            ca_p2 = 1  # Gamepad 2
                        else:
                            ca_p1 = 0  # Gamepad 1
                            ca_p2 = 2  # AI
                        app_screen = "controller_assign"

                elif app_screen == "controller_assign":
                    num_joy = pygame.joystick.get_count()
                    ca_p1, ca_p2, ca_col, result = menu_mod.handle_controller_assign(
                        events, keys, ca_p1, ca_p2, ca_col, num_joy,
                        game_mode=chosen_mode)
                    if result == "back":
                        app_screen = "mode_select"
                    elif result is not None:
                        p1_dev, p2_dev = result
                        state = GameState(game_mode=chosen_mode)
                        state.p1_device = p1_dev
                        state.p2_device = p2_dev
                        rebuild_obstacle_cache(state)
                        app_screen = "game"

                # Draw menu screens
                render_surf.fill(BG_DARK)
                if app_screen == "mode_select":
                    menu_mod.draw_mode_select(render_surf, menu_selected, t)
                elif app_screen == "controller_assign":
                    conflict = (ca_p1 == ca_p2)
                    menu_mod.draw_controller_assign(render_surf, ca_p1, ca_p2,
                                                    pygame.joystick.get_count(), conflict,
                                                    game_mode=chosen_mode, ca_col=ca_col)
                _blit_scaled(render_surf, win)
                pygame.display.flip()

            if app_screen != "game":
                break

            # ── Dispatch to mode ────────────────────────────────────────
            if state.game_mode == "solo":
                result = mode_solo.run_solo(win, render_surf, clock, state)
            elif state.game_mode == "1v1":
                result = mode_1v1.run_1v1(win, render_surf, clock, state)
            else:
                result = "quit"

            if result == "quit":
                break
            elif result == "menu":
                app_screen = "mode_select"

    except SystemExit:
        pass
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()