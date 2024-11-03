from flask import Flask, request, jsonify
from flask_cors import CORS
from commit_cli import generate_commit_message_for_frontend  # Import the new function

app = Flask(__name__)
CORS(app)  # Enable CORS for the Flask app

@app.route('/generateCommitMessage', methods=['POST'])
def generate_commit():
    data = request.json
    commit_type = data.get('commitType', 'feat')
    custom_message = data.get('customMessage', '')

    # Call the function in commit_cli.py to generate the commit message
    try:
        commit_message = generate_commit_message_for_frontend(commit_type, custom_message)
        return jsonify({"commitMessage": commit_message})
    except Exception as e:
        # Log the error and return an error message
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while generating the commit message."}), 500

if __name__ == '__main__':
    app.run(port=5000)
