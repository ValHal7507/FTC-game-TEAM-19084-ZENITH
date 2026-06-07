"""
FTC DECODE — Game state data classes.
"""

import random
import math
from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Tuple

import pygame
from config import CONFIG, FX, FY, FS, dist
from game_logic import rebuild_obstacle_cache


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

    def total_score(self):
        """Calculate the total score from all sources."""
        return (self.classified * 3 + (self.overflow + self.depot) * 1 +
                self.pattern_pts + self.base_pts)

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

    def __init__(self):
        self._setup()

    def _setup(self):
        """Initialize all game state (called by __init__ and reset)."""
        self.phase = "TELEOP"
        self.timer = CONFIG["teleop_time"]
        self.timer_running = False
        self.intake_active = False

        motifs = [["G", "P", "P"], ["P", "G", "P"], ["P", "P", "G"]]
        self.motif = random.choice(motifs)
        self.motif_name = "".join(self.motif)

        self.team = TeamState()
        self.robot = Robot(x=FX + FS // 2, y=FY + FS - 70)
        self.artifacts: List[Artifact] = []
        self.flying: List[FlyingArtifact] = []
        self.gate_clears: List[GateClearAnim] = []
        self.secret_tunnel = (FX + FS // 2, FY + FS // 2 + 60)
        self.scored = False
        self.park_status = "NONE"
        self._init_artifacts()
        rebuild_obstacle_cache(self)

    def reset(self):
        """Reset the game to initial state."""
        self._setup()

    def _init_artifacts(self):
        """Create all 27 starting artifacts."""
        idx = 0
        spike_arr = {0: ["G", "P", "P"], 1: ["P", "G", "P"], 2: ["P", "P", "G"]}
        cols = [FX + 300, FX + 400]
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

    def goal_rect(self):
        """Return the goal rectangle."""
        return pygame.Rect(FX + FS // 2 - CONFIG["goal_w"] // 2, FY + 12,
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
        """Return the base/parking zone rectangle."""
        return pygame.Rect(FX + FS // 2 - CONFIG["base_size"] // 2,
                           FY + FS - CONFIG["base_size"], CONFIG["base_size"], CONFIG["base_size"])

    def in_launch_zone(self, x, y):
        """Check if a point is within the triangular launch zone."""
        fx, fy = x - FX, y - FY
        if 0 <= fy <= 300:
            left = 100 + (260 - 100) * (fy / 300)
            right = 620 - (620 - 460) * (fy / 300)
            if left <= fx <= right:
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
    """Return all 21 scatter positions (18 spike-mark + 3 loading zone)."""
    spike_positions = []
    cols = [FX + 300, FX + 400]
    rows = [FY + 280, FY + 360, FY + 440]
    for ri, ry in enumerate(rows):
        for cx in cols:
            for ai in range(3):
                a = math.radians(ai * 120 + 60)
                spike_positions.append((cx + math.cos(a) * 16, ry + math.sin(a) * 16))
    lx, ly = FX + 15, FY + 15
    loading_positions = [(lx + 20 + ai * 28, ly + 35) for ai in range(3)]
    return spike_positions + loading_positions
