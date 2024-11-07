import argparse
import os
import json
import tempfile

from git import InvalidGitRepositoryError, Repo
from model import generate_commit_message, get_git_changes, analyze_diff

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
        initialize = input("No Git repository found in the project directory. Would you like to initialize one? (yes/no): ").strip().lower()
        if initialize == 'yes':
            repo = Repo.init(project_dir)
            print("Initialized a new Git repository.")
            return repo
        else:
            print("Git repository is required to generate commit messages.")
            return None

def calculate_specialization_boost(language, specialization, commit_type):
    """Calculate additional experience points based on the language and specialization."""
    boost = 0
    if language.lower() == "python" and specialization.lower() == "machine learning":
        if commit_type == "feat":  # Magician class
            boost = 20  # Extra experience for ML/AI feats
            print("Your AI spells are more powerful as a Magician!")
    elif language.lower() == "javascript" and specialization.lower() == "front-end":
        if commit_type == "chore":  # Archer class
            boost = 15  # Extra experience for front-end maintenance
            print("Your front-end Archer skills give extra precision!")
    elif language.lower() in ["go", "rust"] and specialization.lower() == "backend":
        if commit_type == "fix":  # Warrior class
            boost = 25  # Extra experience for backend fixes
            print("Your backend Warrior skills provide extra resilience!")
    elif specialization.lower() == "full-stack":
        # Full-stack specialization gets a balanced boost for all commit types
        if commit_type == "feat":
            boost = 10  # Smaller boost for new features
            print("Your Full-stack skills shine as you craft a new feature!")
        elif commit_type == "fix":
            boost = 10  # Smaller boost for bug fixes
            print("Your Full-stack prowess helps squash a bug!")
        elif commit_type == "chore":
            boost = 10  # Smaller boost for maintenance
            print("Your Full-stack versatility enhances the codebase!")
    return boost

def interactive_commit_review(messages):
    """Displays multiple commit message suggestions and allows the user to choose, modify, or regenerate messages."""
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
    """Generates a commit message for use in the Flask app, using the specified project directory."""
    commit_type = commit_type or 'chore'  # Default to 'chore' if no type is provided
    custom_message = custom_message or ''  # Allow generation without a custom message

    # Load the configuration for the project
    config = load_config(project_dir)
    language = config.get("language", "Unknown")
    framework = config.get("framework", "Unknown")
    specialization = config.get("specialization", "Generalist")

    # Example usage of specialization (if applicable)
    print(f"Specialization: {specialization}")

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
    
    # Calculate experience points
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

    return commit_message, experience, enemies_slain, boost

def main():
    print("Welcome to Commit Message Quest!")
    print("Type 'generate' to start your quest.\n")

    project_dir = get_persistent_temp_project_dir()
    config = load_config(project_dir)

    while True:
        user_input = input("> ").strip().lower()

        if user_input == "generate":
            print("\nChoose your class:")
            print("[feat] Magician - Adds new features")
            print("[fix] Warrior - Fixes bugs")
            print("[chore] Archer - General maintenance\n")
            commit_type = input("Enter your class: ").strip().lower()

            if commit_type not in ["feat", "fix", "chore"]:
                print("Invalid class! Please choose feat, fix, or chore.")
                continue

            custom_message = input("\nEnter your commit message (or leave blank to auto-generate): ").strip()

            changes = get_git_changes(Repo(project_dir))
            diff_summary = changes[0]["diff"] if changes else "general updates"

            # Generate commit message
            commit_message = generate_commit_message(
                commit_type=commit_type,
                custom_message=custom_message,
                language=config.get("language", "Unknown"),
                framework=config.get("framework", "Unknown"),
                diff_summary=diff_summary,
                length="brief"
            )

            # Apply specialization boost
            boost = calculate_specialization_boost(
                config.get("language", "Unknown"),
                config.get("specialization", "Generalist"),
                commit_type
            )
            experience = sum(len(change['diff']) for change in changes) + boost

            # Display results
            print("\n--- Quest Result ---")
            print(f"Commit Message: {commit_message}")
            print(f"You gained {experience} experience points and received a boost of {boost}.")
            print("--------------------\n")

        elif user_input == "setup":
            setup_config(project_dir)
            print("Configuration completed.\n")
        elif user_input == "help":
            print("Commands:")
            print("- generate: Begin your quest to generate a commit message.")
            print("- setup: Configure project settings.")
            print("- help: Show available commands.")
            print("- exit: Exit the quest.")
        elif user_input == "exit":
            print("Farewell, brave coder! Until next time.")
            break
        else:
            print("Unknown command. Type 'help' to see available commands.")

if __name__ == "__main__":
    main()
