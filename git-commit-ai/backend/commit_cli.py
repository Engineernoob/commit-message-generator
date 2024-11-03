import os
import json
import argparse
from model import generate_commit_message, get_git_changes  # Import functions from model.py

# Configuration file path
CONFIG_FILE = "config.json"

# Function to load or set up configuration
def load_config():
    """Loads configuration for the project or sets it up if missing."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        return setup_config()

def setup_config():
    """Prompts the user to set up configuration and saves it to a file."""
    config = {}
    config["language"] = input("Enter the primary programming language (e.g., Python, JavaScript): ")
    config["framework"] = input("Enter the front-end framework (e.g., React, Angular, Vue, None): ")
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
    return config

# Main function to handle CLI interaction
def main():
    parser = argparse.ArgumentParser(description="Generate AI-based git commit messages.")
    parser.add_argument("--generate", action="store_true", help="Generate a commit message based on changes")
    parser.add_argument("--setup", action="store_true", help="Set up or reconfigure project settings")
    args = parser.parse_args()

    # Load or reconfigure configuration
    if args.setup:
        config = setup_config()
    else:
        config = load_config()

    # Load config parameters for language and framework
    language = config.get("language", "Unknown")
    framework = config.get("framework", "Unknown")

    if args.generate:
        # Prompt user for commit preferences
        commit_type = input("Enter commit type (e.g., feat, fix, chore): ")
        custom_message = input("Enter a custom message (or leave blank for auto generation): ")

        # Retrieve unstaged changes
        changes = get_git_changes()
        
        # Generate commit messages
        for change in changes:
            # Generate the commit message using model.py logic
            commit_message = generate_commit_message(
                commit_type=commit_type,
                custom_message=custom_message,
                language=language,
                framework=framework,
                diff_summary=change["diff"]
            )
            print(f"Suggested commit message for {change['file']}:\n{commit_message}\n")

if __name__ == "__main__":
    main()
