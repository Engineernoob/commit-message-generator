from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Filesystem scanning
# ---------------------------------------------------------------------------

_SKIP_PREFIXES = (".",)
_SKIP_NAMES = {
    "__pycache__", "node_modules", ".git", "venv", ".venv",
    "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
}


def build_dungeon(repo_path: str) -> Dict[str, List[str]]:
    """Build a dungeon map from the top-level folders of a repo.

    Returns an alphabetically-sorted dict mapping folder name to list of
    relative file paths beneath it.  Hidden and noise directories are skipped.
    """
    root = Path(repo_path)
    dungeon: Dict[str, List[str]] = {}

    for item in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_dir():
            continue
        if item.name.startswith(_SKIP_PREFIXES) or item.name in _SKIP_NAMES:
            continue

        files: List[str] = sorted(
            str(f.relative_to(root))
            for f in item.rglob("*")
            if f.is_file()
            and f.name not in _SKIP_NAMES
            and not any(part in _SKIP_NAMES for part in f.parts)
        )
        dungeon[item.name] = files

    return dungeon


# ---------------------------------------------------------------------------
# Lore name generation  —  folder name + commit type → fantasy room title
# ---------------------------------------------------------------------------

_LORE_PARTS: Dict[str, Tuple[List[str], List[str]]] = {
    "feat": (
        ["Arcane", "Gilded", "Radiant", "Enchanted", "Gleaming"],
        ["Sanctum", "Forge", "Nexus", "Vault", "Spire"],
    ),
    "fix": (
        ["Broken", "Cursed", "Crumbling", "Scarred", "Shattered"],
        ["Lair", "Pit", "Ruins", "Crypt", "Warren"],
    ),
    "refactor": (
        ["Shifting", "Twisted", "Labyrinthine", "Mirrored", "Warped"],
        ["Maze", "Passage", "Gallery", "Corridor", "Chamber"],
    ),
    "docs": (
        ["Ancient", "Dusty", "Forgotten", "Faded", "Whispering"],
        ["Library", "Archive", "Scriptorium", "Hall", "Athenaeum"],
    ),
    "test": (
        ["Proving", "Judgement", "Trial", "Ordeal", "Gauntlet"],
        ["Arena", "Crucible", "Chamber", "Tribunal", "Grounds"],
    ),
    "chore": (
        ["Damp", "Neglected", "Rusted", "Cobwebbed", "Hollow"],
        ["Cellar", "Storeroom", "Undercroft", "Antechamber", "Den"],
    ),
    "perf": (
        ["Swift", "Burning", "Crackling", "Surging", "Blazing"],
        ["Foundry", "Engine", "Conduit", "Pylon", "Reactor"],
    ),
    "style": (
        ["Ornate", "Painted", "Gilded", "Woven", "Carved"],
        ["Gallery", "Studio", "Atelier", "Salon", "Alcove"],
    ),
}

_DEFAULT_LORE: Tuple[List[str], List[str]] = (
    ["Dark", "Shadowed", "Forsaken", "Hidden", "Silent"],
    ["Chamber", "Room", "Hall", "Vault", "Den"],
)

# Folder name fragments that hint at a better commit-type theme
_FOLDER_THEMES: Dict[str, str] = {
    "test":     "test",
    "tests":    "test",
    "spec":     "test",
    "docs":     "docs",
    "doc":      "docs",
    "src":      "feat",
    "lib":      "feat",
    "backend":  "refactor",
    "frontend": "style",
    "scripts":  "chore",
    "config":   "chore",
    "build":    "perf",
    "ci":       "chore",
}


def lore_name(folder: str, commit_type: str = "chore") -> str:
    """Return a deterministic fantasy room name for a folder + commit type.

    Example::

        lore_name("backend", "feat")  ->  "Arcane Nexus (backend)"
        lore_name("tests",   "fix")   ->  "Broken Crypt (tests)"
    """
    theme = _FOLDER_THEMES.get(folder.lower(), commit_type.lower())
    adjs, nouns = _LORE_PARTS.get(theme, _DEFAULT_LORE)
    seed = int(hashlib.md5(f"{folder}:{theme}".encode()).hexdigest()[:8], 16)
    rng  = random.Random(seed)
    return f"{rng.choice(adjs)} {rng.choice(nouns)} ({folder})"


# ---------------------------------------------------------------------------
# Procedural ASCII room shapes
# ---------------------------------------------------------------------------

def _rect_room(W: int, H: int) -> List[str]:
    lines = ["+" + "-" * (W - 2) + "+"]
    for _ in range(H - 2):
        lines.append("|" + " " * (W - 2) + "|")
    lines.append("+" + "-" * (W - 2) + "+")
    return lines


def _pillar_room(W: int, H: int) -> List[str]:
    lines = _rect_room(W, H)
    for r in [H // 3, H * 2 // 3]:
        if 1 <= r <= H - 2:
            row = list(lines[r])
            for c in [W // 4, W * 3 // 4]:
                if 1 <= c <= W - 2:
                    row[c] = "O"
            lines[r] = "".join(row)
    return lines


def _round_room(W: int, H: int) -> List[str]:
    lines  = ["  +" + "-" * max(0, W - 6) + "+  "]
    lines += [" /  " + " " * max(0, W - 6) + "  \\ "]
    for _ in range(max(0, H - 4)):
        lines.append("|" + " " * (W - 2) + "|")
    lines += [" \\  " + " " * max(0, W - 6) + "  / "]
    lines += ["  +" + "-" * max(0, W - 6) + "+  "]
    return [l.ljust(W)[:W] for l in lines]


def _cross_room(W: int, H: int) -> List[str]:
    third = W // 3
    mid   = W - 2 * third
    lines: List[str] = []
    for row in range(H):
        if row < H // 3 or row >= H * 2 // 3:
            pad = " " * third
            lines.append((pad + "|" + " " * max(0, mid - 2) + "|" + pad).ljust(W)[:W])
        else:
            lines.append(("+" + "-" * (W - 2) + "+").ljust(W)[:W])
    return lines


_ROOM_STYLES = [_rect_room, _pillar_room, _round_room, _cross_room]

# Floor debris characters scattered inside rooms
_DEBRIS = ["*", "o", ".", "x", "~", "^", '"', ","]

# Theme-specific wall decoration characters  left-wall / right-wall
_TORCH: Dict[str, Tuple[str, str]] = {
    "feat":     ("}",  "{" ),
    "fix":      ("!",  "!" ),
    "refactor": ("?",  "?" ),
    "docs":     ("&",  "&" ),
    "test":     ("#",  "#" ),
    "chore":    (":",  ":" ),
    "perf":     (">",  "<" ),
    "style":    ("@",  "@" ),
}


def render_room(
    folder: str,
    files: List[str],
    commit_type: str = "chore",
    width: int = 54,
    height: int = 16,
) -> str:
    """Render a procedural ASCII room for a dungeon folder.

    Layout, floor scatter, and wall decorations are seeded from
    ``folder + commit_type`` so the room is deterministic but changes
    when you change commit type — entering the same room with ``feat``
    vs ``fix`` gives it a different feel.

    The lore name is burned into the top border; artifact count into
    the bottom border.
    """
    rng   = random.Random(int(hashlib.sha256(f"{folder}:{commit_type}".encode()).hexdigest()[:8], 16))
    lines = _ROOM_STYLES[rng.randint(0, len(_ROOM_STYLES) - 1)](width, height)

    # Normalise to height rows of width chars
    while len(lines) < height:
        lines.append(" " * width)
    lines = [l.ljust(width)[:width] for l in lines[:height]]

    # Burn lore name into top border
    name  = lore_name(folder, commit_type)
    label = f"[ {name} ]"
    if len(label) <= width - 4:
        sx  = (width - len(label)) // 2
        row = list(lines[0])
        for i, ch in enumerate(label):
            row[sx + i] = ch
        lines[0] = "".join(row)

    # Scatter floor debris — density proportional to file count
    n_items = min(8, max(1, len(files) // 3))
    for _ in range(n_items):
        r = rng.randint(2, height - 3)
        c = rng.randint(3, width - 4)
        row = list(lines[r])
        if row[c] == " ":
            row[c] = rng.choice(_DEBRIS)
            lines[r] = "".join(row)

    # Wall decorations (torches / symbols) at 1/3 and 2/3 height
    theme         = _FOLDER_THEMES.get(folder.lower(), commit_type.lower())
    left_d, right_d = _TORCH.get(theme, ("}", "{"))

    for torch_row, col, deco in [
        (height // 3,       1,         left_d),
        ((height * 2) // 3, width - 2, right_d),
    ]:
        if 1 <= torch_row <= height - 2:
            row = list(lines[torch_row])
            row[col] = deco
            lines[torch_row] = "".join(row)

    # Burn artifact count into bottom border
    count = len(files)
    word  = "artifact" if count == 1 else "artifacts"
    foot  = f"[ {count} {word} ]"
    if len(foot) <= width - 4:
        sx  = (width - len(foot)) // 2
        row = list(lines[-1])
        for i, ch in enumerate(foot):
            row[sx + i] = ch
        lines[-1] = "".join(row)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Map tree renderer
# ---------------------------------------------------------------------------

def render_map(
    dungeon: Dict[str, List[str]],
    commit_type: str = "chore",
) -> str:
    """Render an ASCII tree of all dungeon rooms with lore names and mini previews.

    Example output::

        DUNGEON MAP
        ══════════════════════════════════════════════════════
        ├── Arcane Nexus (backend)  —  3 artifacts
        │     +----------------------+
        │     |}      o             |
        │     |       *     {       |
        │     +----[3 artifacts]----+
        │     ├── backend/tui_app.py
        │     └── backend/commit_core.py
        │
        └── Broken Crypt (tests)  —  1 artifact
              ...
    """
    if not dungeon:
        return "DUNGEON MAP\n\n  (no rooms found)"

    lines = ["DUNGEON MAP", "═" * 54]
    rooms = list(dungeon.items())

    for idx, (folder, files) in enumerate(rooms):
        is_last        = idx == len(rooms) - 1
        conn           = "└──" if is_last else "├──"
        child_pfx      = "    " if is_last else "│   "

        name  = lore_name(folder, commit_type)
        count = len(files)
        word  = "artifact" if count == 1 else "artifacts"
        lines.append(f"{conn} {name}  —  {count} {word}")

        # Mini room preview (32 wide, 5 tall)
        for preview_line in render_room(folder, files, commit_type, width=32, height=5).splitlines():
            lines.append(f"{child_pfx}  {preview_line}")

        # Up to 3 file names
        visible   = files[:3]
        truncated = len(files) - len(visible)
        for fi, fname in enumerate(visible):
            fc = "└──" if (fi == len(visible) - 1 and not truncated) else "├──"
            lines.append(f"{child_pfx}  {fc} {fname}")
        if truncated:
            lines.append(f"{child_pfx}  └── … +{truncated} more")

        if not is_last:
            lines.append("│")

    return "\n".join(lines)