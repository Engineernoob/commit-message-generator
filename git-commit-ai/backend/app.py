import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from commit_cli import load_config, setup_config, check_or_initialize_git_repo, generate_commit_message, get_git_changes, analyze_diff

app = Flask(__name__)
CORS(app)  # Enable CORS for the Flask app

@app.route('/generateCommitMessage', methods=['POST'])
def generate_commit():
    data = request.json
    project_dir = data.get('projectDir')
    commit_type = data.get('commitType', 'feat')
    custom_message = data.get('customMessage', '')

    if not project_dir or not os.path.isdir(project_dir):
        return jsonify({"error": "Invalid project directory specified."}), 400

    # Load or set up configuration for the project
    config = load_config(project_dir)

    # Check or initialize Git repository
    repo = check_or_initialize_git_repo(project_dir)
    if not repo:
        return jsonify({"error": "No Git repository found and initialization declined."}), 400

    try:
        # Get git changes and generate the commit message
        changes = get_git_changes(repo)
        diff_summary = changes[0]["diff"] if changes else "general updates"

        commit_message = generate_commit_message(
            commit_type=commit_type,
            custom_message=custom_message,
            language=config["language"],
            framework=config["framework"],
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
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while generating the commit message."}), 500

if __name__ == '__main__':
    app.run(port=5000)
