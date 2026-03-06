from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from git import InvalidGitRepositoryError, Repo

from llm_provider import generate_with_provider

CONFIG_FILE = "project_config.json"

# Conventional Commits types we accept/normalize to.
ALLOWED_TYPES = {
    "feat",
    "fix",
    "refactor",
    "docs",
    "test",
    "chore",
    "style",
    "perf",
    "build",
    "ci",
    "revert",
}


def normalize_commit_type(raw: str) -> str:
    """Normalize a commit type to a safe Conventional Commits type."""
    t = (raw or "").strip().lower()
    if not t:
        return "chore"

    # accept forms like "feat:" or "feat(scope):"
    t = t.split(":", 1)[0].strip()

    # if there is a scope, keep the base type
    base = t.split("(", 1)[0].strip()
    if base in ALLOWED_TYPES:
        return base

    # common aliases
    aliases = {
        "feature": "feat",
        "bug": "fix",
        "bugfix": "fix",
        "documentation": "docs",
        "doc": "docs",
        "tests": "test",
        "performance": "perf",
    }
    return aliases.get(base, "chore")


def ensure_project_dir(project_dir: Optional[str]) -> str:
    if project_dir:
        p = Path(project_dir).expanduser().resolve()
    else:
        # default: stable temp dir
        p = Path(os.getenv("TMPDIR", "/tmp")) / "CommitMessageProject"

    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def config_path(project_dir: str) -> Path:
    return Path(project_dir) / CONFIG_FILE


def load_config(project_dir: str) -> Dict[str, Any]:
    p = config_path(project_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_config(project_dir: str, config: Dict[str, Any]) -> None:
    p = config_path(project_dir)
    p.write_text(json.dumps(config, indent=2), encoding="utf-8")


def ensure_git_repo(project_dir: str) -> Optional[Repo]:
    """
    Non-interactive: return Repo if valid, else None.
    """
    try:
        repo = Repo(project_dir, search_parent_directories=True)
        if repo.bare:
            return None
        return repo
    except InvalidGitRepositoryError:
        return None


def _run(repo: Repo, args: List[str]) -> str:
    """
    Run a git command in repo working tree and return stdout.
    """
    cwd = repo.working_tree_dir or "."
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return res.stdout


def _diff_mode_args(mode: str) -> List[str]:
    # staged => --cached
    return ["--cached"] if mode == "staged" else []


def get_changes_summary(repo: Repo, mode: str = "unstaged") -> Dict[str, Any]:
    """
    Returns:
      - files: list[str]
      - insertions, deletions: int
      - summary_text: str (compact natural-language summary)
    """
    mode = mode if mode in ("staged", "unstaged") else "unstaged"
    extra = _diff_mode_args(mode)

    # Files changed
    name_only = _run(repo, ["diff", *extra, "--name-only"]).strip()
    files: List[str] = [f for f in name_only.splitlines() if f.strip()]

    # Stats: use numstat for reliability
    numstat = _run(repo, ["diff", *extra, "--numstat"]).strip()
    insertions: int = 0
    deletions: int = 0
    per_file: List[Tuple[str, int, int]] = []

    for line in numstat.splitlines():
        # format: <ins>\t<del>\t<path>
        parts = line.split("\t")
        if len(parts) < 3:
            continue

        ins_s, del_s, path = parts[0], parts[1], parts[2]

        # binary files show '-' sometimes
        ins: int = int(ins_s) if ins_s.isdigit() else 0
        dels: int = int(del_s) if del_s.isdigit() else 0

        insertions += ins
        deletions += dels
        per_file.append((path, ins, dels))

    # Build a compact summary
    if not files:
        summary_text = "general updates"
    else:
        top: List[Tuple[str, int, int]] = per_file[:6]
        chunks: List[str] = [f"{p} (+{ins}/-{dels})" for (p, ins, dels) in top]
        suffix = "" if len(per_file) <= 6 else f" +{len(per_file) - 6} more files"
        summary_text = f"Changed {len(files)} files: " + ", ".join(chunks) + suffix

    return {
        "mode": mode,
        "files": files,
        "insertions": insertions,
        "deletions": deletions,
        "summary_text": summary_text,
    }


def generate_commit_message(
    commit_type: str,
    custom_message: str,
    config: Dict[str, Any],
    diff_summary: str,
) -> str:
    commit_type = normalize_commit_type(commit_type)
    if custom_message:
        msg = " ".join(str(custom_message).strip().splitlines()).strip()
        return f"{commit_type}: {msg}" if msg else f"{commit_type}: update project"

    language = str(config.get("language", "Unknown"))
    framework = str(config.get("framework", "Unknown"))
    specialization = str(config.get("specialization", "Generalist"))

    prompt = (
        "You are a senior software engineer. Generate ONE concise git commit message.\n"
        "Rules:\n"
        "- Use Conventional Commits EXACTLY: <type>: <summary>\n"
        "- The <type> MUST be: " + commit_type + " (do not change it).\n"
        "- No quotes, no backticks, no extra commentary.\n"
        "- Summary should be <= 72 characters.\n\n"
        f"Context:\n- language: {language}\n- framework: {framework}\n- specialization: {specialization}\n"
        f"- type: {commit_type}\n"
        f"- diff summary: {diff_summary}\n"
    )

    # Ollama-only defaults
    provider = str(config.get("provider", "ollama"))
    model = str(config.get("model", os.getenv("OLLAMA_MODEL", "qwen3:1.7b")))

    msg = generate_with_provider(prompt, provider=provider, model=model)

    # Hard clean-up: keep first line, enforce type prefix
    lines = (msg or "").strip().splitlines()
    first = lines[0].strip() if lines else ""
    if not first:
        return f"{commit_type}: update project"

    # If model forgot type prefix, add it
    if not re.match(r"^[a-z]+(\([^)]+\))?:\s", first):
        return f"{commit_type}: {first[:72]}".strip()

    # If model used a different type, override to preserve weapon consistency
    # (keep optional scope and summary when possible).
    m = re.match(r"^([a-z]+)(\([^)]+\))?:\s*(.+)$", first)
    if m:
        _type, scope, summary = m.group(1), m.group(2) or "", m.group(3)
        summary = (summary or "").strip()
        fixed = f"{commit_type}{scope}: {summary}" if summary else f"{commit_type}: update project"
        return fixed[:72].strip()

    return first[:72].strip()


def maybe_auto_commit(repo: Repo, message: str, stage_all: bool = True) -> str:
    try:
        if stage_all:
            repo.git.add(A=True)
        repo.index.commit(message)
        return "Changes committed automatically."
    except Exception as e:
        return f"Auto-commit failed: {e}"