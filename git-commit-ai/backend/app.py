from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from commit_cli import load_config, setup_config, check_or_initialize_git_repo, generate_commit_message, get_git_changes, analyze_diff

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

@app.route('/setup', methods=['POST'])
def setup_project():
    try:
        data = request.json
        # Default to a directory in the home directory if projectDir is not provided
        project_dir = data.get('projectDir') or os.path.expanduser("~/Commit-Message/default-project")

        # Attempt to create the directory if it doesn’t exist
        if not os.path.exists(project_dir):
            os.makedirs(project_dir, exist_ok=True)

        # Load configuration or prompt to create a new one if none is found
        config = load_config(project_dir)
        if not config:
            create_config = data.get('createConfig', 'no')
            if create_config.lower() == 'yes':
                config = setup_config(project_dir)
            else:
                return jsonify({"error": "No configuration file found and creation declined."}), 400
        
        return jsonify({"message": "Configuration setup completed.", "config": config, "projectDir": project_dir})
    
    except Exception as e:
        print(f"Error in /setup: {e}")  # Log the error to the console
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

@app.route('/generateCommitMessage', methods=['POST'])
def generate_commit():
    try:
        data = request.json
        project_dir = data.get('projectDir')
        commit_type = data.get('commitType', 'feat')
        custom_message = data.get('customMessage', '')

        # Check if project directory is valid
        if not project_dir or not os.path.isdir(project_dir):
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

        # Check for Git repository
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
            "enemiesSlain": enemies_slain
        })

    except Exception as e:
        print(f"Error in /generateCommitMessage: {e}")  # Log the error to the console for debugging
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000)
