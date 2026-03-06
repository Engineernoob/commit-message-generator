from __future__ import annotations

from typing import Dict, List, Tuple, Set

# Emoji are kept OUT of the ASCII art strings — terminal emulators measure
# them inconsistently (1 or 2 columns depending on font/OS), which breaks
# sprite alignment when composited onto the corridor.  Flavor text can use
# them freely since it's rendered in the Markdown log, not the raw arena.

BESTIARY: Dict[str, Tuple[str, str]] = {

    "python": (
        # ~11 chars wide, 7 tall
        r"""
  /^\/^\
 _|__|  O|
\/     /~/
 \____/  \
  |  |    \
  |  |     \
  \_/       \
""",
        "🐍 A coiled Python Serpent rises from the import swamp...",
    ),

    "js": (
        # ~13 chars wide, 8 tall
        r"""
  .--------.
 /  .-""-. /|
|  / ___ \ ||
| | ((_)) | ||
|  \ --- / ||
 \  '---' /
  '-------'
""",
        "⚡ A JavaScript Gremlin hurls unhandled promise rejections...",
    ),

    "ts": (
        # ~13 chars wide, 7 tall
        r"""
   +-------+
  /|  TS   /|
 / |_____/ /|
|  |     | /|
|  |_____|/ /
|  /     | /
|_/______|/
""",
        "🧾 A TypeScript Warden materialises, demanding strict types...",
    ),

    "docs": (
        # ~11 chars wide, 8 tall
        r"""
   .------.
  | README |
  |  ----  |
  |  ----  |
  |  ----  |
  |  ----  |
   '------'
    |    |
""",
        "📜 A Documentation Lich rises from ancient README scrolls...",
    ),

    "config": (
        # ~11 chars wide, 9 tall
        r"""
   _______
  |.-----.|
  ||     ||
  ||  X  ||
  ||     ||
  |'-----'|
  `-.___.--'
    |   |
    |___|
""",
        "⚙️  A Config Golem assembled from YAML and .env shards lumbers forward...",
    ),

    "generic": (
        # ~9 chars wide, 7 tall
        r"""
   .----.
  ( o  o )
  |  __  |
   \ -- /
  .-'  '-.
 /        \
'----------'
""",
        "👾 A mischievous Repo Imp materialises from the diff noise...",
    ),

    "boss": (
        # ~17 chars wide, 12 tall
        r"""
        ___
     .-'   '-.
    /  .-""-.  \
   /  / _  _ \  \
  |  | (o)(o) |  |
  |   \  __  /   |
   \   '----'   /
    '-._    _.-'
     /  |  |  \
    / __|  |__ \
   / /  |  |  \ \
  /_/   |__|   \_\
""",
        "🐉 The Diff Dragon awakens — its scales forged from merge conflicts...",
    ),
}


# ---------------------------------------------------------------------------
# Spawning logic
# ---------------------------------------------------------------------------

# Ordered so the hardest enemies come last in the encounter queue
_SPAWN_ORDER: List[str] = ["python", "ts", "js", "docs", "config", "generic", "boss"]


def enemy_kinds_for_files(
    files: List[str],
    insertions: int,
    deletions: int,
) -> List[str]:
    """Return an ordered list of enemy kinds to spawn for the given diff.

    Rules:
    - One enemy per file-type category found in the diff.
    - ``generic`` is used only when no other category matches.
    - ``boss`` is appended when the total diff is large (≥250 lines or ≥12 files).
    """
    kinds: Set[str] = set()

    for f in files:
        if f.endswith(".py"):
            kinds.add("python")
        if f.endswith((".ts", ".tsx")):
            kinds.add("ts")
        if f.endswith((".js", ".jsx")):
            kinds.add("js")
        if f.endswith((".md", ".rst", ".txt")):
            kinds.add("docs")
        if f.endswith((".json", ".yml", ".yaml", ".env", ".toml")):
            kinds.add("config")

    if not kinds and files:
        kinds.add("generic")

    if insertions + deletions >= 250 or len(files) >= 12:
        kinds.add("boss")

    return [k for k in _SPAWN_ORDER if k in kinds]


def get_enemy(kind: str) -> Tuple[str, str]:
    """Return ``(ascii_art, flavor_text)`` for an enemy kind.

    Falls back to ``generic`` for unrecognised kinds.
    """
    return BESTIARY.get(kind, BESTIARY["generic"])

