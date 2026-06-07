"""
FTC DECODE (2025-2026) Match Simulator — Entry point.
One purple robot collecting artifacts, classifying them into a goal.
"""

import pygame
from config import CONFIG, VW, VH, BLACK, render_surf
from drawing import init_drawing, draw_field, draw_artifacts, draw_robot, draw_hud, draw_match_end
from game_logic import (
    update_timer, update_turret_angle,
    _physics_lock, start_physics_thread, stop_physics_thread,
)
from input_handler import handle_input, init_joysticks
from game_state import GameState


def main():
    pygame.init()
    global render_surf
    win = pygame.display.set_mode((VW, VH), pygame.RESIZABLE)
    pygame.display.set_caption("FTC DECODE — Robot simulator by TEAM ZENITH 19084")
    render_surf = pygame.Surface((VW, VH))
    clock = pygame.time.Clock()
    init_drawing()

    gpad_count = pygame.joystick.get_count()
    print(f"Detected {gpad_count} gamepad(s)")
    init_joysticks()

    state = GameState()

    # Start background physics thread
    start_physics_thread(state)

    try:
        while True:
            dt = min(clock.tick_busy_loop(CONFIG["fps"]) / 1000.0, 0.05)

            # Input + timer + turret all run on main thread.
            # handle_input may request a reset; if so we re-sync under lock.
            reset_requested = handle_input(state, dt)

            if reset_requested:
                # Physics thread must not touch state during reset
                with _physics_lock:
                    state.reset()
                # Re-sync: the physics thread will pick up the fresh state
                # on its next iteration.

            update_timer(state, dt)
            update_turret_angle(state)

            # Render under lock so physics thread doesn't mutate state mid-draw
            with _physics_lock:
                render_surf.fill(BLACK)
                draw_field(render_surf, state)
                draw_artifacts(render_surf, state)
                draw_robot(render_surf, state)
                draw_hud(render_surf, state)
                if state.phase == "FINISHED":
                    draw_match_end(render_surf, state)

            win_w, win_h = win.get_size()
            sx = win_w / VW
            sy = win_h / VH
            sf = min(sx, sy)
            scaled_w = int(VW * sf)
            scaled_h = int(VH * sf)
            ox = (win_w - scaled_w) // 2
            oy = (win_h - scaled_h) // 2

            scaled = pygame.transform.smoothscale(render_surf, (scaled_w, scaled_h))
            win.fill(BLACK)
            win.blit(scaled, (ox, oy))
            pygame.display.flip()
    except SystemExit:
        pass
    finally:
        stop_physics_thread()
        pygame.quit()


if __name__ == "__main__":
    main()
