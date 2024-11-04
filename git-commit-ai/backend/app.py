from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
from commit_cli import (
    load_config,
    setup_config,
    check_or_initialize_git_repo,
    generate_commit_message,
    get_git_changes,
    analyze_diff,
)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Create a temporary directory if the project directory is not specified
def get_temp_project_dir():
    temp_dir = tempfile.mkdtemp(prefix="CommitMessageProject_")
    print(f"Temporary project directory created at: {temp_dir}")
    return temp_dir

@app.route('/setup', methods=['POST'])
def setup_project():
    # Retrieve project directory or create a temporary one if not provided
    data = request.json
    project_dir = data.get('projectDir') or get_temp_project_dir()

    if not os.path.exists(project_dir):
        try:
            os.makedirs(project_dir)
        except OSError as e:
            return jsonify({"error": f"Failed to create directory '{project_dir}': {str(e)}"}), 500

    # Load configuration or initiate setup if no config is found
    config = load_config(project_dir)
    if not config:
        create_config = data.get('createConfig', 'no')
        if create_config.lower() == 'yes':
            config = setup_config(project_dir)
        else:
            return jsonify({"error": "No configuration file found and creation declined."}), 400
    
    return jsonify({"message": "Configuration setup completed.", "config": config, "projectDir": project_dir})

@app.route('/generateCommitMessage', methods=['POST'])
def generate_commit():
    data = request.json
    project_dir = data.get('projectDir') or get_temp_project_dir()
    commit_type = data.get('commitType', 'feat')
    custom_message = data.get('customMessage', '')
    auto_commit = data.get('autoCommit', False)  # New parameter to auto-commit

    if not os.path.isdir(project_dir):
        return jsonify({"error": "Invalid project directory specified."}), 400

    # Load configuration or prompt to create a new one if none is found
    config = load_config(project_dir)
    if not config:
        create_config = data.get('createConfig', 'no')
        if create_config.lower() == 'yes':
            config = setup_config(project_dir)
        else:
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
    commit_message = generate_commit_message(
        commit_type=commit_type,
        custom_message=custom_message,
        language=language,
        framework=framework,
        diff_summary=diff_summary,
        length="brief"
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

