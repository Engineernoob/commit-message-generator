"""
player.py

First-person ASCII player hands for the CommitQuest TUI.

Design goal: hands are BIG and anchored to the bottom corners of the screen,
exactly like Elder Scrolls: Arena.  The left hand occupies the lower-left,
right hand the lower-right.  The weapon hangs between them in the center.

Each hand is 10 chars wide × 7 rows tall so they fill a meaningful portion
of the viewport at the bottom.
"""

from typing import List, Optional, Tuple

# A hand frame is always a pair of (left_hand_lines, right_hand_lines)
HandFrame = Tuple[List[str], List[str]]

HUD_ROWS = 7   # height of every hand/weapon frame


class PlayerHUD:

    COMMIT_WEAPONS: dict[str, str] = {
        "feat":     "sword",
        "fix":      "dagger",
        "refactor": "staff",
        "docs":     "scroll",
        "test":     "hammer",
        "chore":    "dagger",
        "perf":     "sword",
        "style":    "scroll",
        "ci":       "hammer",
    }

    # ------------------------------------------------------------------
    # LEFT hand — occupies bottom-LEFT corner, knuckles facing right
    # Each line is 14 chars wide
    # ------------------------------------------------------------------
    LEFT_IDLE: List[str] = [
        r"    __        ",
        r"   /  \___    ",
        r"  | o   __\   ",
        r"  |    /      ",
        r"   \__/ \     ",
        r"    |    )    ",
        r"   /____/     ",
    ]

    LEFT_RAISED: List[str] = [
        r"      __      ",
        r"   __/  \     ",
        r"  /  o   |    ",
        r" |    ___/    ",
        r"  \__/        ",
        r"   |          ",
        r"  /___        ",
    ]

    LEFT_STRIKE: List[str] = [
        r"              ",
        r"  ___         ",
        r" /   \__      ",
        r"|  o    \___  ",
        r"|       /     ",
        r" \_____/      ",
        r"              ",
    ]

    LEFT_RECOIL: List[str] = [
        r"   __         ",
        r"  /  \__      ",
        r" | o    \     ",
        r" |      |     ",
        r"  \____/      ",
        r"   |  \       ",
        r"  /    \      ",
    ]

    # ------------------------------------------------------------------
    # RIGHT hand — occupies bottom-RIGHT corner, mirror of left
    # ------------------------------------------------------------------
    RIGHT_IDLE: List[str] = [
        r"        __    ",
        r"    ___/  \   ",
        r"   /__   o |  ",
        r"      \    |  ",
        r"     / \__/   ",
        r"    (    |    ",
        r"     \____\   ",
    ]

    RIGHT_RAISED: List[str] = [
        r"      __      ",
        r"     /  \__   ",
        r"    |   o  \  ",
        r"    \___    | ",
        r"        \__/  ",
        r"          |   ",
        r"        ___\  ",
    ]

    RIGHT_STRIKE: List[str] = [
        r"              ",
        r"         ___  ",
        r"      __/   \ ",
        r"  ___/    o  |",
        r"     \       |",
        r"      \_____/ ",
        r"              ",
    ]

    RIGHT_RECOIL: List[str] = [
        r"         __   ",
        r"      __/  \  ",
        r"     /    o | ",
        r"     |      | ",
        r"      \____/  ",
        r"       /  |   ",
        r"      /    \  ",
    ]

    # ------------------------------------------------------------------
    # Weapon art — centred between the two hands (7 rows tall)
    # ------------------------------------------------------------------
    WEAPON_ART: dict[str, List[str]] = {
        "sword": [
            r"   /\   ",
            r"   ||   ",
            r"  /||\  ",
            r"   ||   ",
            r" [====] ",
            r"   ||   ",
            r"   \/   ",
        ],
        "dagger": [
            r"   /\   ",
            r"   ||   ",
            r"   ||   ",
            r" [--||--]",
            r"   ||   ",
            r"   ||   ",
            r"   ()   ",
        ],
        "staff": [
            r"  (***) ",
            r"   |||  ",
            r"   |||  ",
            r"   |||  ",
            r"   |||  ",
            r"   |||  ",
            r"  _|||_ ",
        ],
        "scroll": [
            r" _______ ",
            r"/       \\",
            r"| - - - |",
            r"| - - - |",
            r"| - - - |",
            r"\______/ ",
            r"   ||    ",
        ],
        "hammer": [
            r" [=====] ",
            r" [=====] ",
            r"    ||   ",
            r"    ||   ",
            r"    ||   ",
            r"    ||   ",
            r"   _||_  ",
        ],
    }

    # ------------------------------------------------------------------
    # Animation frame sets  (left_frames, right_frames pairs)
    # ------------------------------------------------------------------
    SWORD_FRAMES: List[HandFrame] = [
        (LEFT_IDLE,   RIGHT_RAISED),
        (LEFT_IDLE,   RIGHT_STRIKE),
        (LEFT_STRIKE, RIGHT_STRIKE),
        (LEFT_RECOIL, RIGHT_RECOIL),
    ]

    DAGGER_FRAMES: List[HandFrame] = [
        (LEFT_IDLE,   RIGHT_RAISED),
        (LEFT_IDLE,   RIGHT_STRIKE),
        (LEFT_RECOIL, RIGHT_IDLE),
    ]

    STAFF_FRAMES: List[HandFrame] = [
        (LEFT_RAISED, RIGHT_RAISED),
        (LEFT_RAISED, RIGHT_RAISED),
        (LEFT_RAISED, RIGHT_RAISED),
        (LEFT_IDLE,   RIGHT_IDLE),
    ]

    HAMMER_FRAMES: List[HandFrame] = [
        (LEFT_IDLE,   RIGHT_RAISED),
        (LEFT_IDLE,   RIGHT_RAISED),
        (LEFT_STRIKE, RIGHT_STRIKE),
    ]

    SCROLL_FRAMES: List[HandFrame] = [
        (LEFT_RAISED, RIGHT_IDLE),
        (LEFT_RAISED, RIGHT_IDLE),
        (LEFT_RAISED, RIGHT_RAISED),
    ]

    _ATTACK_FRAME_MAP: dict[str, str] = {
        "sword":  "SWORD_FRAMES",
        "dagger": "DAGGER_FRAMES",
        "staff":  "STAFF_FRAMES",
        "scroll": "SCROLL_FRAMES",
        "hammer": "HAMMER_FRAMES",
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def weapon_for_commit(commit_type: str) -> str:
        return PlayerHUD.COMMIT_WEAPONS.get(commit_type.lower(), "sword")

    @staticmethod
    def idle() -> HandFrame:
        """Return (left_lines, right_lines) for the idle pose."""
        return (PlayerHUD.LEFT_IDLE, PlayerHUD.RIGHT_IDLE)

    @staticmethod
    def weapon_art(weapon: Optional[str] = None, commit_type: Optional[str] = None) -> List[str]:
        if commit_type and not weapon:
            weapon = PlayerHUD.weapon_for_commit(commit_type)
        return PlayerHUD.WEAPON_ART.get(weapon or "sword", PlayerHUD.WEAPON_ART["sword"])

    @staticmethod
    def attack_frames(weapon: Optional[str] = None, commit_type: Optional[str] = None) -> List[HandFrame]:
        """Return list of (left_lines, right_lines) animation frame pairs."""
        if commit_type and not weapon:
            weapon = PlayerHUD.weapon_for_commit(commit_type)
        attr = PlayerHUD._ATTACK_FRAME_MAP.get(weapon or "sword", "SWORD_FRAMES")
        return getattr(PlayerHUD, attr)

    @staticmethod
    def cast_frames() -> List[HandFrame]:
        return PlayerHUD.STAFF_FRAMES