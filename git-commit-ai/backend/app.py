from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin  # Import CORS and cross_origin decorator
from model import generate_commit_message, get_git_changes
from commit_cli import load_config

app = Flask(__name__)

# Enable CORS for all routes with explicit origin
CORS(app, resources={r"/generateCommitMessage": {"origins": "http://localhost:3000"}})

@app.route('/generateCommitMessage', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:3000')  # Ensure CORS for this specific route
def generate_commit():
    if request.method == 'OPTIONS':
        # Preflight request handler
        response = jsonify({"message": "CORS preflight response"})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response

    # Handle the POST request
    data = request.json
    commit_type = data.get('commitType', 'feat')
    custom_message = data.get('customMessage', '')

    # Load the configuration (e.g., language and framework)
    config = load_config()
    language = config.get("language", "Unknown")
    framework = config.get("framework", "Unknown")

    # Retrieve Git changes if required
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

    # Return the generated commit message with CORS headers
    response = jsonify({"commitMessage": commit_message})
    response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    return response

if __name__ == '__main__':
    app.run(port=5000)

