"""
FTC DECODE — Colors, configuration constants, and helpers.
"""

import math

# ============================================================
# COLORS
# ============================================================
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (140, 140, 150)
DARK_GRAY = (35, 35, 40)
BG_DARK = (22, 22, 28)
CHARCOAL = (50, 50, 56)
LIGHT_GRAY = (190, 190, 200)
SOFT_WHITE = (220, 220, 230)

ROBOT_PURPLE = (175, 60, 255)
ROBOT_DARK = (100, 20, 160)
GLOW_PURPLE = (200, 120, 255, 60)

GOAL_GOLD = (210, 170, 60)
GOAL_DARK = (140, 110, 30)
RAMP_DARK = (60, 55, 50)
SLOT_EMPTY = (45, 42, 38)
SLOT_BORDER = (70, 65, 58)
GATE_COLOR = (200, 170, 60)
GATE_OPEN_COLOR = (60, 200, 80)

PURPLE = (165, 40, 235)
GREEN = (55, 210, 85)
PURPLE_DIM = (100, 25, 140)
GREEN_DIM = (35, 130, 55)

GOLD = (255, 210, 40)
ORANGE = (255, 150, 20)
YELLOW_ACCENT = (255, 240, 120)
RED_ACCENT = (240, 70, 70)
TEAL_ACCENT = (40, 200, 210)
PARK_GREEN = (80, 220, 100)
HEAT_GREEN = (60, 200, 80)
HEAT_YELLOW = (230, 200, 40)
HEAT_ORANGE = (240, 140, 30)
HEAT_RED = (220, 50, 40)

# ============================================================
# CONFIG
# ============================================================
CONFIG = {
    "field_size_px": 720,
    "fps": 120,
    "teleop_time": 120,
    "endgame_time": 20,
    "robot_speed": 280,
    "robot_size": 60,
    "flying_speed": 350,
    "pickup_radius": 45,
    "pickup_cone_angle": 120,
    "rotation_speed": 300,
    "gate_range": 45,
    "gate_open_duration": 2.0,
    "spike_mark_count": 6,
    "ramp_slots": 9,
    "max_hold": 3,
    "respawn_delay": 5.0,
    "artifact_friction": 0.08,
    "artifact_bounce": 0.45,
    "artifact_robot_bounce": 0.90,
    "artifact_artifact_bounce": 0.50,
    "artifact_min_speed": 4.0,
    "robot_push_force": 600.0,
    "artifact_radius": 7,
    "goal_w": 130,
    "goal_h": 130,
    "loading_zone_size": 100,
    "base_size": 80,
    "spike_cols": 2,
    "spike_rows": 3,
    "ramp_h": 14,
    "depot_h": 20,
    "field_margin_left": 5,
    "field_margin_top": 5,
    "hud_width": 320,
    "hud_margin": 5,
    "intake_heat_time": 10.0,
    "intake_cool_time": 4.0,
    "intake_cooldown_time": 10.0,
}

# Derived layout constants
VW = CONFIG["field_size_px"] + CONFIG["field_margin_left"] + CONFIG["hud_margin"] + CONFIG["hud_width"]
VH = CONFIG["field_size_px"] + CONFIG["field_margin_top"] + 5
FX = CONFIG["field_margin_left"]
FY = CONFIG["field_margin_top"]
FS = CONFIG["field_size_px"]
HX = FX + FS + CONFIG["hud_margin"]
HW = CONFIG["hud_width"]

# Backward-compatible aliases
W, H = VW, VH

# Global render state
scale_factor = 1.0
render_surf = None

# ============================================================
# HELPERS
# ============================================================
def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def lerp(a, b, t):
    return a + (b - a) * t
