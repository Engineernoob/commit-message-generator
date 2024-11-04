import argparse
import os
import json
import tempfile

from git import InvalidGitRepositoryError, Repo
from model import generate_commit_message, get_git_changes, analyze_diff  # Import functions from model.py

# Set the configuration file name
CONFIG_FILE = "project_config.json"

def get_persistent_temp_project_dir():
    """Returns a persistent temporary directory for storing the configuration file and project settings."""
    temp_dir = os.path.join(tempfile.gettempdir(), "CommitMessageProject")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        print(f"Persistent temporary project directory created at: {temp_dir}")
    else:
        print(f"Using existing project directory at: {temp_dir}")
    return temp_dir

def load_config(project_dir):
    """Loads configuration for the specified project directory or sets it up if missing."""
    config_path = os.path.join(project_dir, CONFIG_FILE)
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        create_config = input("No configuration file found. Do you want to create a new one? (yes/no): ").strip().lower()
        if create_config == 'yes':
            return setup_config(project_dir)
        else:
            print("No configuration file created. Please run setup to configure your project.")
            return {}

def setup_config(project_dir):
    """Prompts the user to set up configuration for a specified project directory and saves it."""
    config = {}
    config["language"] = input("Enter the primary programming language (e.g., Python, JavaScript, Rust, None): ")
    config["framework"] = input("Enter the front-end framework (e.g., React, Angular, Vue, None): ")
    config["specialization"] = input("Enter your specialization (e.g., AI, Front-end, Backend, Full-stack, None): ")

    os.makedirs(project_dir, exist_ok=True)
    
    config_path = os.path.join(project_dir, CONFIG_FILE)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
        print(f"Configuration saved to {config_path}")
    return config

def check_or_initialize_git_repo(project_dir):
    """Checks if the specified directory is a Git repository; if not, prompts to initialize one."""
    try:
        repo = Repo(project_dir)
        if repo.bare:
            raise InvalidGitRepositoryError
        return repo
    except InvalidGitRepositoryError:
        initialize = input("No Git repository found. Would you like to initialize one here? (yes/no): ").strip().lower()
        if initialize == 'yes':
            repo = Repo.init(project_dir)
            print("Initialized a new Git repository.")
            return repo
        else:
            print("Git repository is required to generate commit messages.")
            return None

def reconfigure(project_dir):
    """Removes the configuration file to reconfigure the project."""
    config_path = os.path.join(project_dir, CONFIG_FILE)
    if os.path.exists(config_path):
        os.remove(config_path)
    print("Reconfiguring...")
    return setup_config(project_dir)

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

def generate_commit_message_for_frontend(commit_type, custom_message, project_dir):
    """
    Generates a commit message for use in the Flask app, using the specified project directory.

    Parameters:
    - commit_type: The type of the commit (e.g., feat, fix, chore).
    - custom_message: A custom message provided by the user.
    - project_dir: The directory of the project.

    Returns:
    A generated commit message string.
    """
    # Use default commit type if not provided
    commit_type = commit_type or 'chore'
    custom_message = custom_message or ''  # Allow the model to generate a message without a custom message

    # Load the configuration for the project
    config = load_config(project_dir)
    language = config.get("language", "Unknown")
    framework = config.get("framework", "Unknown")

    # Retrieve Git changes if required
    repo = check_or_initialize_git_repo(project_dir)
    if not repo:
        return "No Git repository found, and initialization declined."

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

    return commit_message


def main():
    parser = argparse.ArgumentParser(description="Generate AI-based git commit messages.")
    parser.add_argument("project_dir", type=str, nargs='?', default=get_persistent_temp_project_dir(),
                        help="Path to the project directory. Creates a temporary directory if not provided.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--generate", action="store_true", help="Generate a commit message based on changes")
    group.add_argument("--setup", action="store_true", help="Set up or reconfigure project settings")
    
    parser.add_argument('--type', type=str, help="Commit type (feat, fix, chore, etc.)")
    parser.add_argument('--message', type=str, help="Custom message")
    args = parser.parse_args()

    project_dir = args.project_dir

    # Handle configuration setup
    if args.setup:
        config = setup_config(project_dir)
        print("Configuration completed.")
        return
    
    # Handle commit message generation
    config = load_config(project_dir)
    language = config.get("language", "Unknown")
    framework = config.get("framework", "Unknown")

    if args.generate:
        # Ensure that --type is provided when --generate is used
        if not args.type:
            parser.error("--type is required when using --generate")

        # Check or initialize Git repository
        repo = check_or_initialize_git_repo(project_dir)
        if not repo:
            print("Git repository is required to generate commit messages.")
            return

        # Generate the commit message using the provided arguments
        commit_message = generate_commit_message(
            commit_type=args.type,
            custom_message=args.message if args.message else "",
            language=language,
            framework=framework,
            diff_summary="general updates",  # Adjust if needed
            length="brief"
        )
        print(commit_message)  # Print to stdout for capture

        try:
            changes = get_git_changes(repo)
            for change in changes:
                context_summary = analyze_diff(change["diff"])

                # Interactive commit review
                selected_message = interactive_commit_review([commit_message])
                print(f"\nFinalized Commit Message:\n{selected_message}")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
