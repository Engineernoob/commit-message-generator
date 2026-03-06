"""
app.py

Commit Quest TUI — a first-person dungeon crawler where your git diffs spawn
enemies that you defeat by crafting and committing well-formed commit messages.
"""

from __future__ import annotations

import os
import asyncio
import random
import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input, Markdown, Static

from commit_core import (
    ensure_git_repo,
    ensure_project_dir,
    generate_commit_message,
    get_changes_summary,
    load_config,
    maybe_auto_commit,
    save_config,
)

from enemies import enemy_kinds_for_files, get_enemy
from dungeon import build_dungeon, lore_name, render_map, render_room
from player import PlayerHUD, HandFrame, HUD_ROWS

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")


@dataclass
class Player:
    xp: int = 0
    enemies_defeated: int = 0
    floor: int = 1

    @property
    def level(self) -> int:
        return max(1, self.xp // 250 + 1)

    @property
    def title(self) -> str:
        if self.level < 3:
            return "Wanderer"
        if self.level < 6:
            return "Commit Squire"
        if self.level < 10:
            return "Patch Wizard"
        return "Legendary Maintainer"


@dataclass
class Enemy:
    kind: str
    hp: int
    files: List[str]
    insertions: int
    deletions: int
    diff_mode: str

    # Friendly display name per enemy kind
    _NAME_MAP: Dict[str, str] = field(default_factory=lambda: {
        "python": "Python Serpent",
        "js":     "JavaScript Gremlin",
        "ts":     "TypeScript Warden",
        "docs":   "Documentation Lich",
        "config": "Config Golem",
        "boss":   "Diff Dragon",
        "generic": "Repo Imp",
    }, repr=False)

    @property
    def name(self) -> str:
        return self._NAME_MAP.get(self.kind, "Repo Imp")

    @property
    def threat(self) -> int:
        return self.insertions + self.deletions


BANNER = r"""
   ______     ______     __    __     __    __     __     ______   ______     __  __     ______     ______     ______  
/\  ___\   /\  __ \   /\ "-./  \   /\ "-./  \   /\ \   /\__  _\ /\  __ \   /\ \/\ \   /\  ___\   /\  ___\   /\__  _\ 
\ \ \____  \ \ \/\ \  \ \ \-./\ \  \ \ \-./\ \  \ \ \  \/_/\ \/ \ \ \/\_\  \ \ \_\ \  \ \  __\   \ \___  \  \/_/\ \/ 
 \ \_____\  \ \_____\  \ \_\ \ \_\  \ \_\ \ \_\  \ \_\    \ \_\  \ \___\_\  \ \_____\  \ \_____\  \/\_____\    \ \_\ 
  \/_____/   \/_____/   \/_/  \/_/   \/_/  \/_/   \/_/     \/_/   \/___/_/   \/_____/   \/_____/   \/_____/     \/_/ 
"""


def ensure_config(project_dir: str) -> Dict[str, Any]:
    cfg = load_config(project_dir)
    if cfg:
        cfg["provider"] = "ollama"
        cfg["model"] = cfg.get("model") or DEFAULT_MODEL
        save_config(project_dir, cfg)
        return cfg

    cfg = {
        "language":       "Unknown",
        "framework":      "Unknown",
        "specialization": "Generalist",
        "provider":       "ollama",
        "model":          DEFAULT_MODEL,
    }
    save_config(project_dir, cfg)
    return cfg


def enemy_hp(files: List[str], ins: int, dels: int, kind: str) -> int:
    base = max(10, (ins + dels) // 10 + len(files) * 2)
    if kind == "boss":
        return max(70, base * 3)
    return base


class CommitQuest(App[None]):
    CSS_PATH = "ascii.tcss"
    arena_status: reactive[str] = reactive("")
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("escape", "focus_cmd", "Command"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.player = Player()
        self.project_dir = ensure_project_dir(".")
        self.cfg: Dict[str, Any] = ensure_config(self.project_dir)
        self.repo = ensure_git_repo(self.project_dir)

        self.dungeon: Dict[str, List[str]] = build_dungeon(self.project_dir)
        self.current_room: str = "root"

        self.last_message: str = ""
        self.last_commit_type: str = "feat"
        self.last_summary: Dict[str, Any] = {
            "mode":         "unstaged",
            "files":        [],
            "insertions":   0,
            "deletions":    0,
            "summary_text": "general updates",
        }

        self.enemies: List[Enemy] = []
        self.enemy_index: int = 0

        self._log_md: str = ""

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Container(id="root"):
            # Banner is hidden via CSS; kept in the DOM so `display: block`
            # in the tcss can re-enable it without a code change.
            yield Static(BANNER, id="banner")
            yield Static("", id="arena")
            with Vertical(id="console"):
                with VerticalScroll(id="log"):
                    yield Markdown("", id="log_md")
                with Horizontal(id="cmdrow"):
                    yield Static("> ", id="prompt")
                    yield Input(placeholder="> type a command…", id="cmd")
        yield Footer()

    def on_mount(self) -> None:
        self._write_log(self._intro_text())
        self._update_status()
        # Defer the first arena render until after the layout pass so
        # content_size is populated and the corridor fills the full widget.
        self.call_after_refresh(self._render_arena)
        self.query_one("#cmd", Input).focus()

    def on_resize(self) -> None:
        """Redraw the arena whenever the terminal is resized."""
        self._render_arena()

    def action_focus_cmd(self) -> None:
        self.query_one("#cmd", Input).focus()

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    def _intro_text(self) -> str:
        repo_status = "FOUND" if self.repo is not None else "NOT FOUND"
        return (
            "### 🏰 You awaken in the Repo Dungeon...\n\n"
            f"- **Dungeon:** `{self.project_dir}`\n"
            f"- **Git:** `{repo_status}`\n"
            f"- **Ollama Model:** `{self.cfg.get('model', DEFAULT_MODEL)}`\n\n"
            "Type `map` to reveal rooms.\n"
            "Type `enter <room>` to explore a room.\n"
            "Type `scan` to search for enemies.\n"
            "Type `gen feat` to craft a spell.\n"
            "Type `commit` to strike.\n"
        )

    def _write_log(self, md: str) -> None:
        if self._log_md:
            self._log_md += "\n\n---\n\n" + md
        else:
            self._log_md = md
        self.query_one("#log_md", Markdown).update(self._log_md)

    @staticmethod
    def _parse(raw: str) -> List[str]:
        return [p for p in raw.strip().split() if p]

    # ------------------------------------------------------------------
    # Enemy / player helpers
    # ------------------------------------------------------------------

    def _current_enemy(self) -> Optional[Enemy]:
        if 0 <= self.enemy_index < len(self.enemies):
            return self.enemies[self.enemy_index]
        return None

    def _update_status(self) -> None:
        cur = self._current_enemy()
        enemy_txt = (
            f"{cur.name}({cur.kind}) HP:{cur.hp} [{self.enemy_index + 1}/{len(self.enemies)}]"
            if cur else "None"
        )
        self.arena_status = (
            f"FLOOR {self.player.floor} ({self.current_room}) | "
            f"Lv {self.player.level} ({self.player.title}) | "
            f"XP {self.player.xp} | "
            f"Defeated {self.player.enemies_defeated} | "
            f"Mode {self.last_summary.get('mode', 'unstaged')} | "
            f"Enemy {enemy_txt}"
        )

    def _damage(self) -> int:
        msg_bonus = min(10, len(self.last_message) // 12) if self.last_message else 0
        return random.randint(10, 22) + (self.player.level - 1) * 2 + msg_bonus

    # ------------------------------------------------------------------
    # Room / diff helpers
    # ------------------------------------------------------------------

    def _apply_room_filter(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of summary filtered to files under current_room."""
        if self.current_room == "root":
            return summary

        prefix = f"{self.current_room}/"
        files: List[str] = list(summary.get("files", []))
        kept = [f for f in files if f.startswith(prefix)]

        frac = len(kept) / max(1, len(files)) if files else 0.0
        ins  = int(round(int(summary.get("insertions", 0)) * frac))
        dels = int(round(int(summary.get("deletions",  0)) * frac))

        return {
            **summary,
            "files":        kept,
            "insertions":   ins,
            "deletions":    dels,
            "summary_text": f"Room '{self.current_room}': {len(kept)} file(s) changed",
        }

    # ------------------------------------------------------------------
    # Arena rendering  —  full first-person perspective like Arena/Daggerfall
    # ------------------------------------------------------------------

    # Corridor perspective layers, outermost → innermost.
    # Each tuple: (left_wall, right_wall, ceiling_fill, floor_fill)
    _CORRIDOR: List[tuple[str, str, str, str]] = [
        (r"| ",        r" |",        "▓", "▓"),   # far walls
        (r"|  \  ",    r"  /  |",    "▒", "▒"),
        (r"|   |  ",   r"  |   |",   "░", "░"),
        (r"|   |   ",  r"   |   |",  " ", " "),   # near — open space
    ]

    def _arena_seed(self) -> int:
        files = ",".join(list(self.last_summary.get("files", []))[:50])
        sig = (
            f"{self.project_dir}|{self.current_room}|{self.player.floor}|"
            f"{self.last_summary.get('mode')}|{self.last_summary.get('insertions')}|"
            f"{self.last_summary.get('deletions')}|{files}"
        )
        return int(hashlib.sha256(sig.encode()).hexdigest()[:8], 16)

    def _render_corridor(self, W: int, H: int) -> List[str]:
        """Draw a first-person dungeon corridor matching Arena's perspective.

        Key visual elements from the reference:
          - Dark open void in the CENTER — walls are on the SIDES only
          - Stone brick walls converge from left/right toward a vanishing point
          - Chains hanging from the ceiling near the walls
          - Ceiling is a dark slab with slight texture
          - Floor is dark near the horizon, gains tile texture near camera
          - Inner wall face shows a diagonal converging line (\\ and /)
        """
        rng    = random.Random(self._arena_seed())
        lines: List[str] = []

        ceil_h  = max(2, H * 22 // 100)
        floor_h = max(2, H * 28 // 100)
        mid_h   = H - ceil_h - floor_h
        half    = W // 2

        ins  = int(self.last_summary.get("insertions", 0))
        dels = int(self.last_summary.get("deletions",  0))
        heat = ins + dels

        # ── ceiling ───────────────────────────────────────────────────────
        lines.append("+" + "-" * (W - 2) + "+")
        for row in range(1, ceil_h):
            t         = row / ceil_h          # 0=top, 1=bottom of ceiling band
            row_chars = [" "] * W
            # converging perspective lines from top corners toward center
            left_x  = max(0, int(half * (1.0 - t)))
            right_x = W - 1 - left_x
            if 0 <= left_x < W:
                row_chars[left_x]  = "\\"
            if 0 <= right_x < W:
                row_chars[right_x] = "/"
            # sparse ceiling drip/texture between the lines
            for c in range(left_x + 1, right_x):
                if rng.random() < 0.025:
                    row_chars[c] = rng.choice(["'", "`", ".", ","])
            # chains at ~W/4 and 3W/4 — only in upper ceiling rows
            for cx in [W // 4, 3 * W // 4]:
                if 0 <= cx < W and t < 0.75:
                    row_chars[cx] = "|" if row % 2 == 0 else "+"
            lines.append("".join(row_chars))

        # ── corridor walls + dark center ──────────────────────────────────
        # Brick chars vary by diff heat so the room feels different each time
        if heat > 180:
            b1, b2 = "8", "="   # heavily modified — solid brick
        elif heat > 60:
            b1, b2 = "H", "-"   # medium activity
        else:
            b1, b2 = "[", "]"   # quiet hall — carved stone blocks

        for row in range(mid_h):
            t      = row / max(1, mid_h - 1)
            wall_w = max(2, int(W * (0.06 + 0.32 * t)))
            row_chars = list(" " * W)

            # Build brick columns — alternating rows offset for realism
            brick_offset = 2 if (row // 2) % 2 == 1 else 0
            for c in range(wall_w):
                bpos = (c + brick_offset) % 5
                if bpos == 0:
                    ch = "|"
                elif bpos == 4 and row % 3 == 0:
                    ch = "+"
                elif row % 3 == 0:
                    ch = "-"
                else:
                    ch = b1 if (c % 2 == 0) else b2
                row_chars[c]             = ch
                row_chars[W - 1 - c]     = ch

            # Inner wall face — perspective diagonal becomes vertical near camera
            inner_l = "\\" if t < 0.6 else "|"
            inner_r = "/" if t < 0.6 else "|"
            if wall_w < W // 2:
                row_chars[wall_w]         = inner_l
                row_chars[W - 1 - wall_w] = inner_r

            # Torch sconces at 1/3 and 2/3 depth
            if row == mid_h // 3 and wall_w >= 3:
                row_chars[wall_w - 2] = "}"
                row_chars[wall_w - 1] = "*"
                row_chars[W - wall_w]     = "*"
                row_chars[W - wall_w + 1] = "{"
            if row == (mid_h * 2) // 3 and wall_w >= 2:
                row_chars[wall_w - 1] = "}"
                row_chars[W - wall_w] = "{"

            lines.append("".join(row_chars)[:W].ljust(W))

        # ── floor ─────────────────────────────────────────────────────────
        for row in range(floor_h):
            t         = row / max(1, floor_h - 1)  # 0=horizon, 1=near camera
            row_chars = [" "] * W
            # perspective convergence lines
            floor_x = max(0, int(half * (1.0 - t)))
            if floor_x < half:
                row_chars[floor_x]         = "/"
                row_chars[W - 1 - floor_x] = "\\"
            # tile texture only appears close to camera
            if t > 0.35:
                tile_w = max(2, int(2 + t * 7))
                for c in range(floor_x + 1, W - floor_x - 1):
                    local = c % tile_w
                    if local == 0:
                        row_chars[c] = "+"
                    elif t > 0.65 and rng.random() < 0.08:
                        row_chars[c] = rng.choice([".", ",", "_"])
                    else:
                        row_chars[c] = "-" if (c // tile_w) % 2 == 0 else "_"
            lines.append("".join(row_chars))

        # bottom edge
        if len(lines) < H:
            lines.append("+" + "=" * (W - 2) + "+")

        return [ln[:W].ljust(W) for ln in lines[:H]]

    def _render_enemy_sprite(self, corridor: List[str], W: int) -> List[str]:
        """Composite the enemy ASCII sprite into the mid-section of the corridor."""
        cur = self._current_enemy()
        if not cur:
            return corridor

        art, _ = get_enemy(cur.kind)
        sprite_lines = [l for l in art.strip().splitlines() if l.strip()]
        if not sprite_lines:
            return corridor

        ceil_h = max(2, len(corridor) * 33 // 100)

        max_sw = max(len(l) for l in sprite_lines)
        scale  = max(1, int(W * 0.35) // max(1, max_sw))
        if scale > 1:
            sprite_lines = ["".join(c * scale for c in l) for l in sprite_lines]

        sw = max(len(l) for l in sprite_lines)
        sx = max(0, (W - sw) // 2)

        hp_pct = max(0.0, min(1.0, cur.hp / max(1, enemy_hp(cur.files, cur.insertions, cur.deletions, cur.kind))))
        bar_w  = min(sw, 20)
        filled = int(bar_w * hp_pct)
        hp_bar = f"[{'#' * filled}{'.' * (bar_w - filled)}] {cur.hp}hp"
        hp_row = ceil_h - 1
        lines  = list(corridor)

        if 0 <= hp_row < len(lines):
            row = list(lines[hp_row].ljust(W))
            hx  = max(0, (W - len(hp_bar)) // 2)
            for i, ch in enumerate(hp_bar):
                if hx + i < W:
                    row[hx + i] = ch
            lines[hp_row] = "".join(row)

        start_row = ceil_h
        for si, sline in enumerate(sprite_lines):
            ri = start_row + si
            if ri >= len(lines):
                break
            row = list(lines[ri].ljust(W))
            for ci, ch in enumerate(sline):
                if sx + ci < W and ch != " ":
                    row[sx + ci] = ch
            lines[ri] = "".join(row)

        return lines

    def _render_status_overlay(self, corridor: List[str], W: int) -> List[str]:
        """Burn status line into the top-left of the view."""
        lines = list(corridor)
        cur   = self._current_enemy()

        top_left = (
            f" FL:{self.player.floor} {self.current_room} | "
            f"Lv{self.player.level} {self.player.title} | "
            f"XP:{self.player.xp} "
        )[:W]

        if lines:
            row      = list(lines[0].ljust(W))
            for i, ch in enumerate(top_left):
                row[i] = ch
            lines[0] = "".join(row)

        if cur and len(lines) > 1:
            enemy_txt = f" {cur.name}  HP:{cur.hp} [{self.enemy_index+1}/{len(self.enemies)}] "[:W]
            row       = list(lines[1].ljust(W))
            for i, ch in enumerate(enemy_txt):
                row[i] = ch
            lines[1]  = "".join(row)

        return lines

    def _generate_arena(self, width: int = 80, height: int = 22) -> List[str]:
        corridor = self._render_corridor(width, height)
        corridor = self._render_enemy_sprite(corridor, width)
        corridor = self._render_status_overlay(corridor, width)
        return corridor

    def _build_view(
        self,
        frame: Optional[HandFrame] = None,
        width: int = 80,
        height: int = 22,
    ) -> str:
        """Compose corridor + HUD into the final display string.

        Arena-style layout:
          <corridor rows>                   ← `height` lines
          ════════════════════════════════  ← separator
          LEFT_HAND  weapon  RIGHT_HAND     ← HUD_ROWS rows

        `frame` is a HandFrame (left_lines, right_lines) from PlayerHUD.
        If None, the idle pose is used.
        """
        corridor = self._generate_arena(width, height)
        sep      = "═" * width

        left_lines: List[str]
        right_lines: List[str]
        if frame is None:
            left_lines, right_lines = PlayerHUD.idle()
        else:
            left_lines, right_lines = frame

        weapon  = self._weapon_lines()
        nrows   = HUD_ROWS

        lh: List[str] = (list(left_lines)  + [""] * nrows)[:nrows]
        rh: List[str] = (list(right_lines) + [""] * nrows)[:nrows]
        wp: List[str] = (list(weapon)      + [""] * nrows)[:nrows]

        hand_w = max((len(l) for l in lh + rh), default=14)
        wep_w  = max((len(l) for l in wp),       default=8)
        gap_w  = max(1, (width - hand_w * 2 - wep_w) // 2)

        hud_block: List[str] = []
        for i in range(nrows):
            left_str:  str = lh[i].ljust(hand_w)[:hand_w]
            wep_str:   str = wp[i].center(wep_w)
            right_str: str = rh[i].ljust(hand_w)[:hand_w]
            gap            = " " * gap_w
            hud_block.append((left_str + gap + wep_str + gap + right_str)[:width].ljust(width))

        return "\n".join(corridor + [sep] + hud_block)

    def _arena_text(self, frame: Optional[HandFrame] = None) -> str:
        return self._build_view(frame)

    def _arena_with_hud(self, frame: Optional[HandFrame] = None) -> str:
        return self._build_view(frame)

    # ------------------------------------------------------------------
    # HUD helpers
    # ------------------------------------------------------------------

    def _weapon_lines(self) -> List[str]:
        return PlayerHUD.weapon_art(commit_type=self.last_commit_type or "feat")

    def _hud_idle(self) -> HandFrame:
        return PlayerHUD.idle()

    def _hud_attack_frames(self) -> List[HandFrame]:
        return PlayerHUD.attack_frames(commit_type=self.last_commit_type)

    def _hud_cast_frames(self) -> List[HandFrame]:
        return PlayerHUD.cast_frames()

    def _render_arena(self) -> None:
        widget = self.query_one("#arena", Static)
        vw = widget.content_size.width
        vh = widget.content_size.height
        if vw < 10:
            vw = (self.app.size.width  or 120) - 4 # type: ignore
        if vh < 5:
            vh = (self.app.size.height or 40) - 22 # pyright: ignore[reportUnknownMemberType]
        corridor_h = max(8, vh - HUD_ROWS - 2)
        widget.update(self._build_view(self._hud_idle(), width=max(40, vw), height=corridor_h))

    # ------------------------------------------------------------------
    # Async animation helpers
    # ------------------------------------------------------------------

    async def _play_frames(self, frames: List[HandFrame], delay: float = 0.07) -> None:
        widget = self.query_one("#arena", Static)
        vw = widget.content_size.width  or (self.app.size.width  - 4) # type: ignore
        vh = widget.content_size.height or (self.app.size.height - 22) # pyright: ignore[reportUnknownMemberType]
        corridor_h = max(8, vh - HUD_ROWS - 2)
        for frame in frames:
            widget.update(self._build_view(frame, width=max(40, vw), height=corridor_h))
            await asyncio.sleep(delay)
        self._render_arena()

    async def _cast(self) -> None:
        if not self.last_message:
            self._write_log("### ⚠️ No spell prepared.\n\nRun `gen <type>` first.")
            return
        cur    = self._current_enemy()
        target = cur.name if cur else "the darkness"
        await self._play_frames(self._hud_cast_frames(), delay=0.08)
        self._write_log(
            "### 🪄 You cast a spell\n\n"
            f"**Target:** `{target}`\n\n"
            f"**Spell Text:** `{self.last_message}`"
        )

    async def _swing(self) -> None:
        cur    = self._current_enemy()
        target = cur.name if cur else "the air"
        await self._play_frames(self._hud_attack_frames(), delay=0.06)
        self._write_log(f"### ⚔️ You swing at `{target}`")

    # ------------------------------------------------------------------
    # Game commands
    # ------------------------------------------------------------------

    def _arena(self) -> None:
        self._render_arena()
        self._write_log("### 🏟️ Arena Revealed\n\nThe dungeon reshapes itself around your diff.")

    def _spawn_enemies(self, summary: Dict[str, Any]) -> None:
        files = list(summary.get("files", []))
        ins   = int(summary.get("insertions", 0))
        dels  = int(summary.get("deletions",  0))
        mode  = str(summary.get("mode", "unstaged"))

        if not files and ins == 0 and dels == 0:
            self.enemies      = []
            self.enemy_index  = 0
            self._write_log("### 🌿 Quiet hallway...\n\nNo changes. No enemies.")
            return

        kinds = enemy_kinds_for_files(files, ins, dels)
        self.enemies = [
            Enemy(kind=k, hp=enemy_hp(files, ins, dels, k),
                  files=files, insertions=ins, deletions=dels, diff_mode=mode)
            for k in kinds
        ]
        self.enemy_index = 0

        roster = "\n".join(f"- `{e.name}` (`{e.kind}`) HP `{e.hp}`" for e in self.enemies)
        self._write_log(f"### 🧟 A floor of enemies appears!\n\n{roster}")
        self._show_encounter()

    def _show_encounter(self) -> None:
        cur = self._current_enemy()
        if not cur:
            return
        art, flavor = get_enemy(cur.kind)
        self._write_log(
            "### 👁️ Encounter!\n\n"
            f"{flavor}\n\n"
            f"```text\n{art.strip()}\n```\n"
            f"**Enemy:** `{cur.name}` • **HP:** `{cur.hp}`"
        )
        self._render_arena()

    def _scan(self, mode: str) -> None:
        if self.repo is None:
            self._write_log("### ❌ No git repo found.\n\nMove into a repo and run again.")
            return

        mode    = mode if mode in ("staged", "unstaged") else "unstaged"
        summary = self._apply_room_filter(get_changes_summary(self.repo, mode=mode))
        self.last_summary = summary

        files      = summary["files"][:20]
        file_lines = "\n".join(f"- `{f}`" for f in files) or "- *(no files changed)*"
        if len(summary["files"]) > 20:
            file_lines += f"\n- *(+{len(summary['files']) - 20} more)*"

        self._write_log(
            "### 🔎 You search the dungeon...\n\n"
            f"- **Mode:** `{summary['mode']}`\n"
            f"- **Files Changed:** `{len(summary['files'])}`\n"
            f"- **Insertions:** `{summary['insertions']}`\n"
            f"- **Deletions:** `{summary['deletions']}`\n\n"
            f"#### Tracks\n{file_lines}"
        )
        self._spawn_enemies(summary)
        self._render_arena()
        self._update_status()

    def _generate(self, commit_type: str, custom_message: str = "") -> None:
        if self.repo is None:
            self._write_log("### ❌ No git repo found.")
            return

        cur = self._current_enemy()
        if not cur:
            self._write_log("### ⚠️ No enemy.\n\nRun `scan` first so there's something to fight.")
            return

        self.last_commit_type = (commit_type or "chore").strip().lower()
        diff_summary = (
            self.last_summary.get("summary_text")
            if self.last_summary.get("files")
            else "general updates"
        )

        msg = generate_commit_message(
            commit_type=commit_type,
            custom_message=custom_message,
            config=self.cfg,
            diff_summary=str(diff_summary),
        )
        self.last_message = msg
        self._write_log(
            f"### ✨ Spell Prepared for `{cur.name}`\n\n"
            f"`{msg}`\n\n"
            "Use `commit` to attack."
        )
        self._render_arena()

    def _commit(self) -> None:
        if self.repo is None:
            self._write_log("### ❌ No git repo found.")
            return
        if not self.last_message:
            self._write_log("### ⚠️ No spell prepared.\n\nRun `gen <type>` first.")
            return

        # Narrow once here so both the inline call and the closure capture a
        # non-optional Repo — satisfies the type checker without redundant checks.
        repo = self.repo

        cur = self._current_enemy()
        if not cur:
            self._write_log("### 🌿 No enemy is present.\n\nBut we can still commit.")
            self._write_log(f"### 🧾 Commit Result\n\n{maybe_auto_commit(repo, self.last_message, stage_all=True)}")
            self._update_status()
            return

        # Fire-and-forget swing animation, then resolve commit synchronously.
        # Using run_worker with a proper coroutine avoids blocking the event loop.
        async def _swing_then_resolve() -> None:
            await self._swing()

            dmg    = self._damage()
            cur.hp = max(0, cur.hp - dmg)

            result = maybe_auto_commit(repo, self.last_message, stage_all=True)
            self._write_log(f"### 🧾 Commit Result\n\n{result}")

            if "failed" in result.lower():
                self._write_log("### ⚠️ The enemy laughs.\n\nFix the issue and try again.")
                self._update_status()
                return

            # Successful commit → defeat enemy
            self.player.enemies_defeated += 1
            self._write_log(f"### ☠️ `{cur.name}` is defeated!")
            self.enemy_index  += 1
            self.last_message  = ""

            nxt = self._current_enemy()
            if nxt:
                self._show_encounter()
            else:
                threat = (
                    int(self.last_summary.get("insertions", 0))
                    + int(self.last_summary.get("deletions",  0))
                )
                self.player.xp    += threat
                self.player.floor += 1
                self._write_log(
                    f"### 🏆 FLOOR CLEARED!\n\n"
                    f"You gain `{threat}` XP and descend to FLOOR `{self.player.floor}`."
                )
                self.enemies      = []
                self.enemy_index  = 0

            self._update_status()

        self.run_worker(_swing_then_resolve(), exclusive=True)

    def _help(self) -> None:
        self._write_log(
            "### Commands\n\n"
            "- `map` — show dungeon layout with lore room names\n"
            "- `room` — inspect the current room as a full ASCII chamber\n"
            "- `enter <room>` — move into a room (or `enter root`)\n"
            "- `arena` — show the current procedurally-generated arena\n"
            "- `cast` — animate + display your prepared commit-message spell\n"
            "- `help` — show this\n"
            "- `scan` — scan unstaged changes (spawns multiple enemies)\n"
            "- `scan staged` — scan staged changes\n"
            "- `mode staged|unstaged` — set default scan mode\n"
            "- `gen <type>` — generate AI commit spell (feat/fix/chore/docs/refactor/test)\n"
            "- `say <type> <message...>` — write your own spell\n"
            "- `commit` — attack + auto-commit (defeats current enemy on success)\n"
            "- `stats` — show player stats\n"
            "- `quit` — exit\n"
        )

    def _stats(self) -> None:
        self._write_log(
            "### 🏆 Adventurer Stats\n\n"
            f"- **Floor:** `{self.player.floor}`\n"
            f"- **Level:** `{self.player.level}` ({self.player.title})\n"
            f"- **XP:** `{self.player.xp}`\n"
            f"- **Enemies Defeated:** `{self.player.enemies_defeated}`\n"
        )

    def _set_mode(self, mode: str) -> None:
        mode = mode.strip()
        if mode not in ("staged", "unstaged"):
            self._write_log("### ⚠️ Unknown mode.\n\nUse: `mode staged` or `mode unstaged`")
            return
        self.last_summary["mode"] = mode
        self._write_log(f"### ✅ Default scan mode set to `{mode}`")
        self._update_status()

    def _map(self) -> None:
        self.dungeon = build_dungeon(self.project_dir)
        text         = render_map(self.dungeon, commit_type=self.last_commit_type)
        room_hint    = self.current_room
        self._write_log(
            "### 🗺️ Dungeon Map\n\n"
            f"Current room: `{room_hint}`\n\n"
            f"```text\n{text}\n```\n\n"
            "Use `enter <room>` to explore a room (or `enter root`).\n"
            "Use `room` to inspect the current room."
        )

    def _room(self) -> None:
        """Render the current room as a full-size ASCII dungeon chamber."""
        if self.current_room == "root":
            self._write_log(
                "### 🏰 Dungeon Entrance\n\n"
                "You stand at the root of the repository.\n"
                "Use `enter <room>` to descend into a room."
            )
            return

        self.dungeon = build_dungeon(self.project_dir)
        files        = self.dungeon.get(self.current_room, [])
        art          = render_room(
            self.current_room, files,
            commit_type=self.last_commit_type,
            width=54, height=16,
        )
        name = lore_name(self.current_room, self.last_commit_type)
        self._write_log(
            f"### 🚪 {name}\n\n"
            f"```text\n{art}\n```"
        )

    def _enter(self, room: str) -> None:
        room = (room or "").strip()
        if not room or room == "root":
            self.current_room = "root"
            self._write_log("### 🚪 You return to the dungeon entrance (root).")
            self._update_status()
            return

        self.dungeon = build_dungeon(self.project_dir)
        if room not in self.dungeon:
            rooms = ", ".join(sorted(self.dungeon.keys())) or "(no rooms found)"
            self._write_log(
                "### ⚠️ Unknown room\n\n"
                f"Room `{room}` does not exist. Available rooms: {rooms}\n\n"
                "Tip: run `map` to see the layout."
            )
            return

        self.current_room = room
        name = lore_name(room, self.last_commit_type)
        self._write_log(
            f"### 🚪 You enter the {name}...\n\n"
            "Type `room` to inspect it. Type `scan` to search for enemies."
        )
        self._update_status()

    # ------------------------------------------------------------------
    # Input dispatch
    # ------------------------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw   = event.value
        event.input.value = ""
        parts = self._parse(raw)
        if not parts:
            return

        cmd = parts[0].lower()
        dispatch: Dict[str, Callable[[], None]] = {
            "q":      self.exit,
            "quit":   self.exit,
            "exit":   self.exit,
            "help":   self._help,
            "stats":  self._stats,
            "map":    self._map,
            "room":   self._room,
            "arena":  self._arena,
        }

        if cmd in dispatch:
            dispatch[cmd]()
            return

        if cmd == "enter":
            self._enter(parts[1] if len(parts) > 1 else "")
        elif cmd == "cast":
            self.run_worker(self._cast(), exclusive=True)
        elif cmd == "mode":
            self._set_mode(parts[1] if len(parts) > 1 else "")
        elif cmd == "scan":
            mode = parts[1] if len(parts) > 1 else str(self.last_summary.get("mode", "unstaged"))
            self._scan(mode)
        elif cmd == "gen":
            self._generate(parts[1] if len(parts) > 1 else "chore")
        elif cmd == "say":
            if len(parts) < 3:
                self._write_log("### ⚠️ Usage\n\n`say <type> <message...>`")
            else:
                self.last_commit_type = parts[1].lower() or "feat"
                self._generate(parts[1], custom_message=" ".join(parts[2:]))
        elif cmd == "commit":
            self._commit()
        else:
            self._write_log(f"### ❓ Unknown command: `{cmd}`\n\nType `help` to see options.")


if __name__ == "__main__":
    CommitQuest().run()