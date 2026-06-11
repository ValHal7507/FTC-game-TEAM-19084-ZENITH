"""
FTC DECODE — Colors, configuration constants, and helpers.
"""

import json
import math
import os
import sys

import pygame

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

ROBOT_PURPLE = (69, 23, 163)     # Team ZENITH official brand color
ROBOT_DARK = (100, 20, 160)
GLOW_PURPLE = (160, 100, 255)   # Brighter glow variant of team purple

# ── Team ZENITH 19084 brand colors ──────────────────────────────────────────
ZENITH_PURPLE  = (69,  23, 163)   # #4517a3 — official team primary color
ZENITH_ACCENT  = (180, 140, 255)  # soft lavender — light text on dark bg
ZENITH_DARK    = (25,   8,  60)   # near-black deep purple — header bg
ZENITH_LABEL   = "ZENITH  19084"  # full display string
ZENITH_TAG     = "Visions above ground"  # team tagline

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

PAUSE_OVERLAY = (0, 0, 0, 180)
MENU_BG = (30, 30, 36)
MENU_BORDER = (69, 23, 163)         # ZENITH_PURPLE
MENU_HIGHLIGHT_BG = (40, 18, 95)    # dark purple for selected button
MENU_HIGHLIGHT_BORDER = (180, 140, 255)  # ZENITH_ACCENT lavender
MENU_TEXT = (220, 220, 230)
MENU_TITLE = (180, 140, 255)        # ZENITH_ACCENT lavender
OPTIONS_REBIND = (255, 100, 60)
OPTIONS_BIND = (100, 200, 140)

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
    "shooting_zone_size": 220,
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
VH = CONFIG["field_size_px"] + CONFIG["field_margin_top"] + 5 + 48
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


# ============================================================
# KEYBINDS
# ============================================================
GAMEPAD_NAMES = {
    ("button", 0): "A",
    ("button", 1): "B",
    ("button", 2): "X",
    ("button", 3): "Y",
    ("button", 4): "LB",
    ("button", 5): "RB",
    ("button", 6): "Back",
    ("button", 7): "Start",
    ("button", 8): "LS",
    ("button", 9): "RS",
    ("axis", 0): "Left Stick X",
    ("axis", 1): "Left Stick Y",
    ("axis", 2): "Right Stick X",
    ("axis", 3): "Right Stick Y",
    ("axis", 4): "LT (axis 4)",
    ("axis", 5): "RT (axis 5)",
}

KEYBIND_ACTIONS_KEYBOARD = [
    "Move Forward",
    "Move Backward",
    "Strafe Left",
    "Strafe Right",
    "Rotate Left",
    "Rotate Right",
    "Toggle Intake",
    "Launch Artifacts",
    "Toggle Gate",
    "Drive Mode",
]

KEYBIND_ACTIONS_GAMEPAD = [
    "Launch",
    "Intake",
    "Gate",
    "Pause",
    "Drive Mode",
]

DEFAULT_KEYBINDS = {
    "keyboard": {
        "Move Forward": ("key", pygame.K_w),
        "Move Backward": ("key", pygame.K_s),
        "Strafe Left": ("key", pygame.K_a),
        "Strafe Right": ("key", pygame.K_d),
        "Rotate Left": ("key", pygame.K_LEFT),
        "Rotate Right": ("key", pygame.K_RIGHT),
        "Toggle Intake": ("key", pygame.K_e),
        "Launch Artifacts": ("key", pygame.K_q),
        "Toggle Gate": ("key", pygame.K_t),
        "Drive Mode": ("key", pygame.K_r),
    },
    "gamepad": {
        "Launch": ("axis", 4),
        "Intake": ("axis", 5),
        "Gate": ("button", 2),
        "Pause": ("button", 3),
        "Drive Mode": ("button", 4),
        "Reset": ("button", 6),
    },
}

LOCKED_KEYBINDS = {"keyboard": set(), "gamepad": {"Reset"}}


# ============================================================
# KEYBIND PERSISTENCE
# ============================================================
def _game_dir():
    """Return the directory containing the main script or executable."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


_KEYBINDS_FILE = os.path.join(_game_dir(), "keybinds.json")


def save_keybinds(keybinds):
    """Write current keybinds to keybinds.json. Never raises."""
    try:
        data = {}
        for page, bindings in keybinds.items():
            data[page] = {action: list(binding) if binding else None
                          for action, binding in bindings.items()}
        with open(_KEYBINDS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_keybinds():
    """Load keybinds from keybinds.json. Returns dict or None on failure."""
    try:
        with open(_KEYBINDS_FILE, "r") as f:
            data = json.load(f)
        if "keyboard" not in data or "gamepad" not in data:
            return None
        result = {}
        for page in ("keyboard", "gamepad"):
            result[page] = {action: tuple(binding) if binding else None
                            for action, binding in data[page].items()}
        return result
    except Exception:
        print("  [keybinds] No saved keybinds found, using defaults")
        return None
