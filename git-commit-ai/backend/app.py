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
    analyze_diff
)
from git import Repo

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Root directory for all project directories
ROOT_DIR = os.path.expanduser("~/Commit-Message")

# Ensure ROOT_DIR exists
os.makedirs(ROOT_DIR, exist_ok=True)

# Function to load configuration for a project
def load_or_create_config(project_dir):
    config = load_config(project_dir)
    if not config:
        # Ask the user (or system) if a new config should be created
        config = setup_config(project_dir)
    return config

# Endpoint to set up the project directory and configuration
@app.route('/setup', methods=['POST'])
def setup_project():
    try:
        data = request.json
        # Use ROOT_DIR as base if projectDir is not provided, or create a temporary directory for testing
        project_dir = data.get('projectDir') or tempfile.mkdtemp(dir=ROOT_DIR)

        # Create project directory if it doesn't exist
        if not os.path.exists(project_dir):
            os.makedirs(project_dir, exist_ok=True)

        # Load or create configuration
        config = load_or_create_config(project_dir)
        return jsonify({"message": "Configuration setup completed.", "config": config, "projectDir": project_dir})
    
    except Exception as e:
        print(f"Error in /setup: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

# Endpoint to generate and commit a message automatically
@app.route('/autoCommit', methods=['POST'])
def auto_commit():
    try:
        data = request.json
        project_dir = data.get('projectDir') or os.path.join(ROOT_DIR, "default-project")
        commit_type = data.get('commitType', 'feat')
        custom_message = data.get('customMessage', '')

        # Create project directory if it doesn’t exist
        if not os.path.exists(project_dir):
            os.makedirs(project_dir, exist_ok=True)

        # Load or create configuration
        config = load_or_create_config(project_dir)
        language = config.get("language", "Unknown")
        framework = config.get("framework", "Unknown")

        # Check or initialize Git repository
        repo = check_or_initialize_git_repo(project_dir)
        if not repo:
            return jsonify({"error": "No Git repository found and initialization declined."}), 400

        # Retrieve Git changes and generate commit message
        changes = get_git_changes(repo)
        if not changes:
            return jsonify({"error": "No changes to commit."}), 400
        
        diff_summary = changes[0]["diff"] if changes else "general updates"
        commit_message = generate_commit_message(
            commit_type=commit_type,
            custom_message=custom_message,
            language=language,
            framework=framework,
            diff_summary=diff_summary,
            length="brief"
        )

        # Perform the commit
        repo.git.add(A=True)  # Stage all changes
        repo.index.commit(commit_message)  # Commit with the generated message

        # Calculate experience and enemies slain
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
            "message": "Changes committed successfully!"
        })

    except Exception as e:
        print(f"Error in /autoCommit: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000)

