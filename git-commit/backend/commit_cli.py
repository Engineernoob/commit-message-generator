from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from commit_core import (
    ensure_git_repo,
    ensure_project_dir,
    generate_commit_message,
    get_changes_summary,
    load_config,
    maybe_auto_commit,
    save_config,
)

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")


def _print_err(msg: str) -> None:
    print(f"[commit-cli] {msg}", file=sys.stderr)


def cmd_setup(args: argparse.Namespace) -> int:
    project_dir = ensure_project_dir(args.project_dir)

    config: Dict[str, Any] = {
        "language": args.language or "Unknown",
        "framework": args.framework or "Unknown",
        "specialization": args.specialization or "Generalist",
        "provider": "ollama",
        "model": args.model or DEFAULT_MODEL,
    }

    save_config(project_dir, config)
    print(f"Config saved to: {Path(project_dir) / 'project_config.json'}")
    print(config)
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    project_dir = ensure_project_dir(args.project_dir)

    config = load_config(project_dir)
    if not config:
        _print_err("Missing config. Run: commit-cli setup --project-dir <path>")
        return 2

    repo = ensure_git_repo(project_dir)
    if repo is None:
        _print_err("No git repository found in projectDir.")
        return 2

    diff_mode = "staged" if args.staged else "unstaged"
    summary = get_changes_summary(repo, mode=diff_mode)
    diff_summary = summary["summary_text"] if summary["files"] else "general updates"

    commit_type = (args.type or "chore").strip()
    custom_message = (args.message or "").strip()

    commit_message = generate_commit_message(
        commit_type=commit_type,
        custom_message=custom_message,
        config=config,
        diff_summary=diff_summary,
    )

    print("\n--- Commit Message ---")
    print(commit_message)
    print("\n--- Stats ---")
    print(f"Mode: {summary['mode']}")
    print(f"Files changed: {len(summary['files'])}")
    print(f"Insertions: {summary['insertions']}")
    print(f"Deletions: {summary['deletions']}")
    print(f"XP: {summary['insertions'] + summary['deletions']}")
    print(f"Enemies slain: {len(summary['files'])}")

    if args.auto_commit:
        result = maybe_auto_commit(repo, commit_message, stage_all=True)
        print("\n--- Auto-Commit ---")
        print(result)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="commit-cli",
        description="Ollama-only AI commit message generator (uses local Git diffs).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # setup
    s = sub.add_parser("setup", help="Create/update project_config.json for a repo.")
    s.add_argument("--project-dir", default=".", help="Path to the git repo (default: .)")
    s.add_argument("--language", default=None, help="Primary language (e.g., Python)")
    s.add_argument("--framework", default=None, help="Framework (e.g., Flask, React)")
    s.add_argument("--specialization", default=None, help="Specialization (e.g., AI, Backend)")
    s.add_argument("--model", default=None, help=f"Ollama model name (default: {DEFAULT_MODEL})")
    s.set_defaults(func=cmd_setup)

    # generate
    g = sub.add_parser("generate", help="Generate a commit message from git changes.")
    g.add_argument("--project-dir", default=".", help="Path to the git repo (default: .)")
    g.add_argument("--type", default="chore", help="Conventional commit type (feat, fix, chore, docs, refactor, etc.)")
    g.add_argument("--message", default="", help="Custom message override. If provided, AI is skipped.")
    g.add_argument("--staged", action="store_true", help="Use staged changes (git diff --cached). Default is unstaged.")
    g.add_argument("--auto-commit", action="store_true", help="Automatically commit with the generated message.")
    g.set_defaults(func=cmd_generate)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())