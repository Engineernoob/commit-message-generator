import os
import json
import argparse
from model import generate_commit_message, get_git_changes, analyze_diff  # Import functions from model.py

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

def reconfigure():
    os.remove(CONFIG_FILE)
    print("Reconfiguring...")
    return setup_config()

def interactive_commit_review(messages):
    """
    Displays multiple commit message suggestions and allows the user to choose, modify, or regenerate messages.
    Returns the user's selected or modified message.
    """
    for idx, message in enumerate(messages, start=1):
        print(f"\nSuggested Commit Message {idx}:\n{message}")

    choice = input("\nChoose a commit message by number, or type 'r' to regenerate: ")

    if choice.isdigit() and 1 <= int(choice) <= len(messages):
        return messages[int(choice) - 1]
    elif choice.lower() == 'r':
        return None  # Indicate regeneration needed
    else:
        print("Invalid choice, using the first message as default.")
        return messages[0]


def main():
    parser = argparse.ArgumentParser(description="Generate AI-based git commit messages.")
    parser.add_argument("--generate", action="store_true", help="Generate a commit message based on changes")
    parser.add_argument("--setup", action="store_true", help="Set up or reconfigure project settings")
    args = parser.parse_args()

    # Load or reconfigure configuration
    config = load_config() if not args.setup else setup_config()
    language = config.get("language", "Unknown")
    framework = config.get("framework", "Unknown")

    if args.generate:
        commit_type = input("Enter commit type (e.g., feat, fix, chore): ")
        length = input("Message length (brief/detailed): ")

        # Retrieve unstaged changes and generate multiple commit messages
        changes = get_git_changes()
        for change in changes:
            diff_summary = analyze_diff(change["diff"])
            initial_messages = [
                generate_commit_message(commit_type, "", language, framework, diff_summary, length)
                for _ in range(3)
            ]  # Generate 3 variations

            # Interactive review
            selected_message = None
            while selected_message is None:
                selected_message = interactive_commit_review(initial_messages)
            
            print(f"\nFinalized Commit Message:\n{selected_message}")

if __name__ == "__main__":
    main()