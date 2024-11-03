import os
import json
import argparse

from numpy import common_type
from model import generate_commit_message, get_git_changes, analyze_diff  # Import functions from model.py
from utils import save_common_message, get_similar_message, log_error

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
    parser.add_argument('--type', type=str, required=True, help="Commit type (feat, fix, chore, etc.)")
    parser.add_argument('--message', type=str, required=False, help="Custom message")
    args = parser.parse_args()

    config = load_config() if not args.setup else setup_config()
    language = config.get("language", "Unknown")
    framework = config.get("framework", "Unknown")

    if args.generate:
         # Generate the commit message using the provided arguments
        commit_message = generate_commit_message(
            commit_type=args.type,
            custom_message=args.message if args.message else "",
            language="Python",
            framework="Flask",
            diff_summary="general updates",  # Adjust if needed
            length="brief"
        )
        print(commit_message)  # Print to stdout for Electron to capture

        try:
            changes = get_git_changes()
            for change in changes:
                context_summary = analyze_diff(change["diff"])

                # Check for a saved message
                saved_message = get_similar_message(context_summary)
                if saved_message:
                    print(f"Suggested common commit message:\n{saved_message}")
                    use_saved = input("Use this message? (y/n): ")
                    if use_saved.lower() == 'y':
                        selected_message = saved_message
                    else:
                        selected_message = generate_commit_message(
                            args.type, "", language, framework, context_summary, "brief"
                        )
                        save_common_message(context_summary, selected_message)
                else:
                    selected_message = generate_commit_message(
                        args.type, "", language, framework, context_summary, "brief"
                    )
                    save_common_message(context_summary, selected_message)

                print(f"\nFinalized Commit Message:\n{selected_message}")

        except Exception as e:
            log_error(e)
            print("An error occurred. Check commit_tool.log for details.")

if __name__ == "__main__":
    main()