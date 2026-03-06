from __future__ import annotations

import os
from typing import Any, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS

from commit_core import (
    ensure_git_repo,
    ensure_project_dir,
    generate_commit_message,
    get_changes_summary,
    load_config,
    maybe_auto_commit,
    save_config,
)

app = Flask(__name__)
CORS(app)


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/setup")
def setup():
    """
    Create/update project config.
    Ollama-only defaults:
      - provider: "ollama"
      - model: env OLLAMA_MODEL or "llama3"
    """
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}

    project_dir = ensure_project_dir(data.get("projectDir"))
    config = { # type: ignore
        "language": data.get("language", "Unknown"),
        "framework": data.get("framework", "Unknown"),
        "specialization": data.get("specialization", "Generalist"),
        "provider": "ollama",
        "model": data.get("model") or os.getenv("OLLAMA_MODEL", "qwen3:1.7b"),
    }

    save_config(project_dir, config) # type: ignore

    return jsonify(
        {
            "message": "Configuration saved.",
            "config": config,
            "projectDir": project_dir,
        }
    )


@app.post("/generateCommitMessage")
def generate():
    """
    Generate a commit message based on repo changes.
    Request body:
      - projectDir (required)
      - commitType (required) e.g. feat, fix, chore
      - customMessage (optional)
      - autoCommit (optional bool)
      - diffMode (optional: "unstaged" | "staged")
    """
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}

    project_dir = data.get("projectDir")
    if not project_dir:
        return jsonify({"error": "projectDir is required"}), 400

    project_dir = ensure_project_dir(project_dir)

    commit_type = str(data.get("commitType") or "chore").strip()
    custom_message = str(data.get("customMessage") or "").strip()
    auto_commit = bool(data.get("autoCommit", False))
    diff_mode = str(data.get("diffMode") or "unstaged").strip()

    config = load_config(project_dir)
    if not config:
        return jsonify({"error": "Missing config. Call POST /setup first."}), 400

    repo = ensure_git_repo(project_dir)
    if repo is None:
        return jsonify({"error": "No git repository found in projectDir."}), 400

    summary = get_changes_summary(repo, mode=diff_mode)
    diff_summary = summary["summary_text"] if summary["files"] else "general updates"

    commit_message = generate_commit_message(
        commit_type=commit_type,
        custom_message=custom_message,
        config=config,
        diff_summary=diff_summary,
    )

    auto_commit_result = "Auto-commit not performed."
    if auto_commit:
        auto_commit_result = maybe_auto_commit(repo, commit_message, stage_all=True)

    return jsonify(
        {
            "commitMessage": commit_message,
            "experience": summary["insertions"] + summary["deletions"],
            "enemiesSlain": len(summary["files"]),
            "diffMode": summary["mode"],
            "stats": {
                "filesChanged": len(summary["files"]),
                "insertions": summary["insertions"],
                "deletions": summary["deletions"],
            },
            "autoCommitResponse": auto_commit_result,
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)