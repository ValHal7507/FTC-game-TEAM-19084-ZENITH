"""
FTC DECODE — Game state data classes.
"""

import random
import math
import copy
from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Tuple

import pygame
from config import (CONFIG, FX, FY, FS, dist,
                    DEFAULT_KEYBINDS, DEFAULT_KEYBINDS_P2,
                    load_keybinds, load_keybinds_p2)
from game_logic import rebuild_obstacle_cache


def _sign(p1, p2, p3):
    """Signed area of triangle (p1, p2, p3). Used for point-in-triangle test."""
    return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])


def _point_in_triangle(pt, v1, v2, v3):
    """Return True if pt is inside triangle defined by v1, v2, v3."""
    d1 = _sign(pt, v1, v2)
    d2 = _sign(pt, v2, v3)
    d3 = _sign(pt, v3, v1)
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (has_neg and has_pos)


@dataclass
class Artifact:
    """A single field artifact (purple or green)."""
    x: float
    y: float
    color: str
    vx: float = 0.0
    vy: float = 0.0
    on_field: bool = True
    zone: str = "spike"
    respawn_timer: float = 0.0
    index: int = 0


@dataclass
class FlyingArtifact:
    """An artifact in flight toward the goal."""
    x: float
    y: float
    target_x: float
    target_y: float
    color: str
    speed: float = CONFIG["flying_speed"]
    active: bool = True
    trail: List[Tuple[float, float]] = field(default_factory=list)
    scoring: bool = True
    full_set: bool = False
    team: str = "p1"   # "p1" or "p2" — which team scores this artifact

    MAX_TRAIL: ClassVar[int] = 18


@dataclass
class Robot:
    """The player-controlled robot."""
    x: float
    y: float
    speed: float = CONFIG["robot_speed"]
    angle: float = 0.0
    turret_angle: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    drive_mode: str = "field"
    holding: List[Artifact] = field(default_factory=list)
    start_x: float = 0.0
    start_y: float = 0.0
    alliance: str = "neutral"   # "neutral" | "blue" | "red"

    def __post_init__(self):
        self.start_x = self.x
        self.start_y = self.y

    def can_pickup(self):
        """Return True if the robot can carry more artifacts."""
        return len(self.holding) < CONFIG["max_hold"]


@dataclass
class GateClearAnim:
    x: float
    y: float
    target_x: float
    target_y: float
    color: str
    progress: float = 0.0
    active: bool = True


@dataclass
class TeamState:
    """Tracks scoring state for the alliance."""
    ramp: List[Optional[str]] = field(default_factory=lambda: [None] * 9)
    overflow_held: List[str] = field(default_factory=list)
    gate_open: bool = False
    gate_timer: float = 0.0
    classified: int = 0
    overflow: int = 0
    depot: int = 0
    pattern_pts: int = 0
    base_pts: int = 0

    def total_score(self, chaos_active=False):
        """Calculate the total score from all sources.
        Doubled during CHAOS MODE."""
        base = (self.classified * 3 + (self.overflow + self.depot) * 1 +
                self.pattern_pts + self.base_pts)
        return base * 2 if chaos_active else base

    def add_to_ramp(self, color: str) -> bool:
        """Place an artifact on the ramp. Returns True if it fit in a slot."""
        for i in range(CONFIG["ramp_slots"]):
            if self.ramp[i] is None:
                self.ramp[i] = color
                return True
        self.overflow_held.append(color)
        self.overflow += 1
        self.depot += 1
        return False

    def clear_ramp(self):
        """Remove all artifacts from the ramp. Returns list of colors."""
        cleared = [c for c in self.ramp if c is not None] + self.overflow_held
        self.ramp = [None] * CONFIG["ramp_slots"]
        self.overflow_held.clear()
        return cleared


class GameState:
    """Complete game state for one match."""

    def __init__(self, game_mode="solo"):
        self.game_mode = game_mode
        self._setup()

    def _setup(self):
        """Initialize all game state (called by __init__ and reset)."""
        self.phase = "TELEOP"
        self.timer = CONFIG["teleop_time"]
        self.timer_running = False
        self.intake_active = False
        self.intake_heat = 0.0
        self.intake_overheated = False
        self.intake_cooldown_timer = 0.0

        motifs = [["G", "P", "P"], ["P", "G", "P"], ["P", "P", "G"]]
        self.motif = random.choice(motifs)
        self.motif_name = "".join(self.motif)

        self.team = TeamState()
        self.robot = Robot(x=FX + 70, y=FY + FS // 2, angle=math.pi / 2)
        self.artifacts: List[Artifact] = []
        self.flying: List[FlyingArtifact] = []
        self.gate_clears: List[GateClearAnim] = []
        self.secret_tunnel = (FX + FS // 2, FY + FS // 2 + 60)
        self.scored = False
        self.park_status = "NONE"
        self.pause_menu_index = 0
        self.options_active = False
        self.options_page = 0
        self.options_index = 0
        self.options_rebinding = False
        self.keybinds = {page: dict(bindings) for page, bindings in DEFAULT_KEYBINDS.items()}
        if self.game_mode != "1v1":
            saved = load_keybinds()
            if saved:
                self.keybinds = saved

        # 1v1 fields
        self.robot2 = None
        self.team2 = None
        self.park_status2 = "NONE"
        self.keybinds_p2 = {page: dict(bindings) for page, bindings in DEFAULT_KEYBINDS_P2.items()}
        if self.game_mode != "1v1":
            saved_p2 = load_keybinds_p2()
            if saved_p2:
                self.keybinds_p2 = saved_p2
        self.p1_device = "keyboard"
        self.p2_device = "gamepad1"
        # P2 intake state
        self.intake_active2 = False
        self.intake_heat2 = 0.0
        self.intake_overheated2 = False
        self.intake_cooldown_timer2 = 0.0

        # Mode return signal (set by pause menu "Mode Select" action)
        self.pending_return = None

        # ── Chaos Mode ────────────────────────────────────────────────
        self.chaos_active        = False
        self.konami_progress     = 0
        self.chaos_activate_time = 0.0   # wall-clock seconds when chaos triggered
        self.chaos_particles     = []    # managed by drawing.py

        self._init_artifacts()

        # 1v1 setup
        if self.game_mode == "1v1":
            self.robot.alliance = "blue"
            p2x = FX + FS - 70
            p2y = FY + FS // 2
            self.robot2 = Robot(x=p2x, y=p2y, speed=CONFIG["robot_speed"],
                                angle=-math.pi / 2, drive_mode="field", alliance="red")
            self.team2 = TeamState()
            self.park_status2 = "NONE"
            self._add_1v1_artifacts()
        else:
            self.robot2 = None
            self.team2 = None
            self.robot.alliance = "neutral"

        rebuild_obstacle_cache(self)

    def reset(self):
        """Reset the game to initial state, preserving 1v1 settings."""
        from ai_controller import reset_ai
        saved_mode = self.game_mode
        saved_p1_dev = self.p1_device
        saved_p2_dev = self.p2_device
        # In 1v1, don't restore keybinds — always use defaults
        saved_p2_keybinds = copy.deepcopy(self.keybinds_p2) if self.game_mode != "1v1" else None
        if self.game_mode == "1v1":
            reset_ai()

        self.game_mode = saved_mode
        self._setup()
        self.game_mode = saved_mode
        self.p1_device = saved_p1_dev
        self.p2_device = saved_p2_dev
        if saved_p2_keybinds is not None:
            self.keybinds_p2 = saved_p2_keybinds

    def _init_artifacts(self):
        """Create all 18 starting artifacts."""
        idx = 0
        spike_arr = {0: ["G", "P", "P"], 1: ["P", "G", "P"], 2: ["P", "P", "G"]}
        cols = [FX + FS // 2 - 50]
        rows = [FY + 280, FY + 360, FY + 440]
        for ri, ry in enumerate(rows):
            for cx in cols:
                for ai, c in enumerate(spike_arr[ri]):
                    a = math.radians(ai * 120 + 60)
                    self.artifacts.append(Artifact(
                        cx + math.cos(a) * 16, ry + math.sin(a) * 16, c, zone="spike", index=idx
                    ))
                    idx += 1
        lx, ly = FX + 15, FY + 15
        for ai, c in enumerate(["P", "G", "P"]):
            self.artifacts.append(Artifact(lx + 20 + ai * 28, ly + 35, c, zone="loading", index=idx))
            idx += 1
        colors = ["P"] * 4 + ["G"] * 2
        random.shuffle(colors)
        for ai, c in enumerate(colors):
            self.artifacts.append(Artifact(
                FX + 6 + (ai % 3) * 24, FY + 180 + (ai // 3) * 26, c, zone="alliance", index=idx
            ))
            idx += 1

    def _add_1v1_artifacts(self):
        """Add mirrored spike, loading, and alliance artifacts for P2's side."""
        p2_extras = []
        for art in list(self.artifacts):
            if art.zone in ("spike", "loading"):
                mirrored_x = FX + FS - (art.x - FX)
                p2_extras.append(Artifact(
                    x=mirrored_x, y=art.y,
                    color=art.color, on_field=True,
                    zone=art.zone, index=art.index
                ))
        colors = ["P"] * 4 + ["G"] * 2
        random.shuffle(colors)
        for ai, c in enumerate(colors):
            p2_extras.append(Artifact(
                FX + FS - 6 - (ai % 3) * 24, FY + 180 + (ai // 3) * 26,
                c, zone="alliance", index=ai
            ))
        self.artifacts.extend(p2_extras)

    def goal_rect(self):
        """Return the goal rectangle."""
        return pygame.Rect(FX + FS // 2 - CONFIG["goal_w"] // 2, FY,
                           CONFIG["goal_w"], CONFIG["goal_h"])

    def ramp_rect(self):
        """Return the ramp rectangle below the goal."""
        g = self.goal_rect()
        return pygame.Rect(g.x, g.bottom + 5, g.w, CONFIG["ramp_h"])

    def depot_rect(self):
        """Return the depot rectangle below the ramp."""
        g = self.goal_rect()
        return pygame.Rect(g.x, g.bottom + 5 + CONFIG["ramp_h"] + 3, g.w, CONFIG["depot_h"])

    def gate_rect(self):
        """Return the gate rectangle on the right side of the ramp."""
        r = self.ramp_rect()
        return pygame.Rect(r.right - 18, r.y, 18, r.h)

    def loading_rect(self):
        """Return the loading zone rectangle."""
        return pygame.Rect(FX, FY, CONFIG["loading_zone_size"], CONFIG["loading_zone_size"])

    def base_rect(self):
        """Return the base/parking zone rectangle (left-center of field)."""
        return pygame.Rect(FX + 10, FY + FS // 2 - CONFIG["base_size"] // 2,
                           CONFIG["base_size"], CONFIG["base_size"])

    def base_rect2(self):
        """P2 base zone — horizontal mirror of base_rect() (right-center)."""
        r = self.base_rect()
        mirrored_left = FX + FS - (r.left - FX) - r.width
        return pygame.Rect(mirrored_left, r.top, r.width, r.height)

    def loading_rect2(self):
        """P2 loading zone — horizontal mirror of loading_rect() (top-right)."""
        r = self.loading_rect()
        mirrored_left = FX + FS - (r.left - FX) - r.width
        return pygame.Rect(mirrored_left, r.top, r.width, r.height)

    def in_launch_zone2(self, x, y):
        """Same logic as in_launch_zone but checks P2's mirrored zones (horizontal mirror)."""
        mirrored_x = FX + FS - (x - FX)
        return self.in_launch_zone(mirrored_x, y)

    def shooting_zone_triangle(self):
        """Return the three vertices of the shooting zone triangle (right-angle isosceles, hypotenuse at bottom)."""
        hyp = CONFIG["shooting_zone_size"]
        height = hyp / 2
        cx = FX + FS // 2
        cy = FY + FS - 5 - height / 3
        top = (cx, cy - 2 * height / 3)
        bl = (cx - hyp / 2, cy + height / 3)
        br = (cx + hyp / 2, cy + height / 3)
        return (top, bl, br)

    def in_launch_zone(self, x, y):
        """Check if a point is within the triangular launch zone, base/parking zone, or shooting zone."""
        if self.base_rect().collidepoint(x, y):
            return True
        fx, fy = x - FX, y - FY
        if 0 <= fy <= 300:
            left = 100 + (260 - 100) * (fy / 300)
            right = 620 - (620 - 460) * (fy / 300)
            if left <= fx <= right:
                return True
        top, bl, br = self.shooting_zone_triangle()
        if _point_in_triangle((x, y), top, bl, br):
            return True
        return False

    def nearest_artifact(self, x, y, radius):
        """Find the closest pickup-able artifact within radius."""
        best, best_d = None, radius
        for a in self.artifacts:
            if a.on_field and a.respawn_timer <= 0:
                d = dist((x, y), (a.x, a.y))
                if d < best_d:
                    best_d = d
                    best = a
        return best


def get_ramp_scatter_positions(state):
    """Return all scatter positions (spike-mark + loading zone for both sides)."""
    spike_positions = []
    cols = [FX + FS // 2 - 50]
    rows = [FY + 280, FY + 360, FY + 440]
    for ri, ry in enumerate(rows):
        for cx in cols:
            for ai in range(3):
                a = math.radians(ai * 120 + 60)
                spike_positions.append((cx + math.cos(a) * 16, ry + math.sin(a) * 16))
    lx, ly = FX + 15, FY + 15
    loading_positions = [(lx + 20 + ai * 28, ly + 35) for ai in range(3)]
    rx = FX + FS - 15 - 84
    loading_positions += [(rx + ai * 28 + 20, ly + 35) for ai in range(3)]
    return spike_positions + loading_positions
