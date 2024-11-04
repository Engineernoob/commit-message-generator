from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
from commit_cli import (
    get_persistent_temp_project_dir,
    load_config,
    setup_config,
    check_or_initialize_git_repo,
    generate_commit_message_for_frontend,
    get_git_changes,
    analyze_diff
)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Define a fixed directory for storing the configuration file in the system's temp folder
def get_persistent_temp_dir():
    temp_dir = os.path.join(tempfile.gettempdir(), "CommitMessageProject")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        print(f"Temporary project directory created at: {temp_dir}")
    else:
        print(f"Using existing project directory at: {temp_dir}")
    return temp_dir

@app.route('/setup', methods=['POST'])
def setup_project():
    # Use the persistent temporary directory for configuration
    data = request.json
    project_dir = data.get('projectDir') or get_persistent_temp_dir()

    # Ensure configuration setup
    config = setup_config(project_dir)
    return jsonify({"message": "Configuration setup completed.", "config": config, "projectDir": project_dir})

@app.route('/generateCommitMessage', methods=['POST'])
def generate_commit():
    data = request.json
    project_dir = data.get('projectDir') or get_persistent_temp_project_dir()
    commit_type = data.get('commitType', '')  # Allow empty commit type
    custom_message = data.get('customMessage', '')  # Allow empty custom message
    auto_commit = data.get('autoCommit', False)  # Optional, for auto-commit

    if not os.path.isdir(project_dir):
        return jsonify({"error": "Invalid project directory specified."}), 400

    # Load configuration
    config = load_config(project_dir)
    if not config:
        return jsonify({"error": "No configuration file found and creation declined."}), 400
    language = config.get("language", "Unknown")
    framework = config.get("framework", "Unknown")

    # Check for Git repository or initialize if missing
    repo = check_or_initialize_git_repo(project_dir)
    if not repo:
        return jsonify({"error": "No Git repository found and initialization declined."}), 400

    # Get git changes
    changes = get_git_changes(repo)
    diff_summary = changes[0]["diff"] if changes else "general updates"

    # Generate the commit message
    commit_message = generate_commit_message_for_frontend(
        commit_type=commit_type,
        custom_message=custom_message,
        project_dir=project_dir
    )

    # Auto-commit if requested
    if auto_commit:
        try:
            repo.git.add(A=True)
            repo.index.commit(commit_message)
            auto_commit_response = "Changes have been committed automatically."
        except Exception as e:
            auto_commit_response = f"Auto-commit failed: {str(e)}"
    else:
        auto_commit_response = "Auto-commit not performed."

    # Calculate experience and enemies slain based on insertions and deletions
    insertions, deletions = 0, 0
    for change in changes:
        ins, dels = analyze_diff(change["diff"])
        insertions += ins
        deletions += dels

    experience = insertions + deletions
    enemies_slain = len(changes)

    return jsonify({
        "commitMessage": commit_message,
        "experience": experience,
        "enemiesSlain": enemies_slain,
        "autoCommitResponse": auto_commit_response
    })

if __name__ == '__main__':
    app.run(port=5000)
