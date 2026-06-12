"""
FTC DECODE — 1v1 local multiplayer game mode loop.
"""

import sys
import pygame
from config import CONFIG, VW, VH, BLACK
from drawing import (
    draw_field, draw_artifacts, draw_robot,
    draw_hud, draw_match_end, draw_match_end_buttons,
    draw_pause_menu, draw_options_screen,
)
from drawing_1v1 import draw_field_1v1_extras, draw_robot2
from game_logic import (
    update_timer, update_turret_angle, update_turret_angle_r,
    _physics_lock, start_physics_thread, stop_physics_thread,
)
from input_handler import handle_input
from input_handler_p2 import handle_input_p2


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


def run_1v1(screen, canvas, clock, state):
    """
    Runs the 1v1 match loop.

    Returns:
      "menu"  — player chose 'Mode Select' from the pause menu
      "quit"  — player pressed Exit (Esc / gamepad B at match end, or F10)
    The physics thread is already running when this is called.
    """
    start_physics_thread(state)
    end_menu_index = 0

    try:
        while True:
            # ── Check pending return (Mode Select from pause menu) ────────
            if state.pending_return:
                r = state.pending_return
                state.pending_return = None
                return r

            dt = min(clock.tick_busy_loop(CONFIG["fps"]) / 1000.0, 0.05)
            events = pygame.event.get()
            keys = pygame.key.get_pressed()

            for ev in events:
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.VIDEORESIZE:
                    pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)

            # ── Match finished: end-game navigation ──────────────────────
            if state.phase == "FINISHED":
                for ev in events:
                    if ev.type == pygame.KEYDOWN:
                        # F5/F10 always work (admin shortcuts)
                        if ev.key == pygame.K_F5:
                            with _physics_lock:
                                state.reset()
                            end_menu_index = 0
                        elif ev.key == pygame.K_F10:
                            pygame.quit()
                            sys.exit()
                        # Navigation via keyboard — always available
                        elif True:
                            if ev.key in (pygame.K_LEFT, pygame.K_KP4):
                                end_menu_index = (end_menu_index - 1) % 2
                            elif ev.key in (pygame.K_RIGHT, pygame.K_KP6):
                                end_menu_index = (end_menu_index + 1) % 2
                            elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                                if end_menu_index == 0:
                                    with _physics_lock:
                                        state.reset()
                                    end_menu_index = 0
                                else:
                                    return "quit"

                # Render match end
                with _physics_lock:
                    update_timer(state, dt)
                    canvas.fill(BLACK)
                    draw_field(canvas, state)
                    draw_field_1v1_extras(canvas, state)
                    draw_artifacts(canvas, state)
                    draw_robot(canvas, state)
                    draw_robot2(canvas, state)
                    draw_hud(canvas, state)
                    draw_match_end(canvas, state)
                    draw_match_end_buttons(canvas, state, end_menu_index)

                _blit_scaled(canvas, screen)
                pygame.display.flip()
                continue

            # ── Normal gameplay ──────────────────────────────────────────
            reset_requested = handle_input(state, dt, events)

            if reset_requested:
                with _physics_lock:
                    state.reset()
                end_menu_index = 0

            # P2 input (1v1 only, skip when AI-controlled)
            if state.robot2 is not None and state.p2_device != "ai":
                handle_input_p2(state, dt, events)

            update_turret_angle(state)
            if state.robot2 is not None:
                update_turret_angle_r(state, state.robot2)

            with _physics_lock:
                update_timer(state, dt)
                canvas.fill(BLACK)
                draw_field(canvas, state)
                draw_field_1v1_extras(canvas, state)
                draw_artifacts(canvas, state)
                draw_robot(canvas, state)
                draw_robot2(canvas, state)
                draw_hud(canvas, state)
                if not state.timer_running and state.phase != "FINISHED":
                    draw_pause_menu(canvas, state)
                if state.options_active:
                    draw_options_screen(canvas, state)

            _blit_scaled(canvas, screen)
            pygame.display.flip()

    finally:
        stop_physics_thread()
