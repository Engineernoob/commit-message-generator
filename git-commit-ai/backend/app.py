from flask import Flask, request, jsonify
from flask_cors import CORS
from model import generate_commit_message, get_git_changes # Import functions from model.py
from commit_cli import load_config  # Import the config loading function from commit_cli.py


app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"]) # Enable CORS to allow requests from the frontend

# Endpoint to handle commit message generation
@app.route('/generateCommitMessage', methods=['POST'])
def generate_commit():
    data = request.json
    commit_type = data.get('commitType', 'feat')
    custom_message = data.get('customMessage', '')

    # Load the configuration (e.g., language and framework)
    config = load_config()  # This function should return a dictionary with configuration data
    language = config.get("language", "Unknown")
    framework = config.get("framework", "Unknown")

    # Retrieve Git changes if required
    changes = get_git_changes()  # List of changes with diff summaries
    diff_summary = changes[0]["diff"] if changes else "general updates"  # Using the first change's diff summary

    # Generate the commit message
    commit_message = generate_commit_message(
        commit_type=commit_type,
        custom_message=custom_message,
        language=language,
        framework=framework,
        diff_summary=diff_summary,  # Using the diff summary from Git changes
        length="brief"
    )

    return jsonify({"commitMessage": commit_message})

if __name__ == '__main__':
    app.run(port=5000)
