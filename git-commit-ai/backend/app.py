from flask import Flask, request, jsonify
from flask_cors import CORS
from commit_cli import load_config, generate_commit_message, get_git_changes, analyze_diff, calculate_specialization_boost

app = Flask(__name__)
CORS(app)  # Enable CORS for the Flask app

@app.route('/generateCommitMessage', methods=['POST'])
def generate_commit():
    data = request.json
    commit_type = data.get('commitType', 'feat')
    custom_message = data.get('customMessage', '')

    try:
        # Load configuration for language, framework, and specialization
        config = load_config()
        language = config.get("language", "Unknown")
        framework = config.get("framework", "Unknown")
        specialization = config.get("specialization", "Generalist")

        # Get git changes and diff summary
        changes = get_git_changes()
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

        # Calculate experience points and enemies slain
        insertions, deletions = 0, 0
        for change in changes:
            ins, dels = analyze_diff(change["diff"])
            insertions += ins
            deletions += dels
        experience = insertions + deletions
        enemies_slain = len(changes)

        # Apply specialization boost
        boost = calculate_specialization_boost(language, specialization, commit_type)
        experience += boost

        # Return response with commit message, experience points, and enemies slain
        return jsonify({
            "commitMessage": commit_message,
            "experience": experience,
            "enemiesSlain": enemies_slain
        })

    except Exception as e:
        # Log the error and return an error message
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while generating the commit message."}), 500

if __name__ == '__main__':
    app.run(port=5000)
