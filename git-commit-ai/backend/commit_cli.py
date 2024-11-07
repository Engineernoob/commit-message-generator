
import os
import json
import tempfile
from git import InvalidGitRepositoryError, Repo
from model import generate_commit_message, get_git_changes, analyze_diff

CONFIG_FILE = "project_config.json"

def get_persistent_temp_project_dir():
    """Returns a persistent temporary directory for storing the configuration file and project settings."""
    temp_dir = os.path.join(tempfile.gettempdir(), "CommitMessageProject")
    os.makedirs(temp_dir, exist_ok=True)
    print(f"Using persistent project directory at: {temp_dir}")
    return temp_dir

def load_config(project_dir):
    """Loads configuration for the specified project directory or prompts to create it if missing."""
    config_path = os.path.join(project_dir, CONFIG_FILE)
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        create_config = input("No configuration file found. Do you want to create a new one? (yes/no): ").strip().lower()
        if create_config == 'yes':
            return setup_config(project_dir)
        print("No configuration file created. Please run setup to configure your project.")
        return {}

def setup_config(project_dir):
    """Prompts the user to set up configuration for a specified project directory and saves it."""
    config = {
        "language": input("Enter the primary programming language (e.g., Python, JavaScript, Rust, None): "),
        "framework": input("Enter the front-end framework (e.g., React, Angular, Vue, None): "),
        "specialization": input("Enter your specialization (e.g., AI, Front-end, Backend, Full-stack, None): ")
    }
    config_path = os.path.join(project_dir, CONFIG_FILE)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
        print(f"Configuration saved to {config_path}")
    return config

def check_or_initialize_git_repo(project_dir):
    """Checks if the specified directory is a Git repository; prompts to initialize one if missing."""
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
        print("Git repository is required to generate commit messages.")
        return None

def calculate_specialization_boost(language, specialization, commit_type):
    """Calculate additional experience points based on the language and specialization."""
    boosts = {
        ("python", "machine learning", "feat"): (20, "Your AI spells are more powerful as a Magician!"),
        ("javascript", "front-end", "chore"): (15, "Your front-end Archer skills give extra precision!"),
        ("go", "backend", "fix"): (25, "Your backend Warrior skills provide extra resilience!"),
        ("rust", "backend", "fix"): (25, "Your backend Warrior skills provide extra resilience!"),
        ("", "full-stack", "feat"): (10, "Your Full-stack skills shine as you craft a new feature!"),
        ("", "full-stack", "fix"): (10, "Your Full-stack prowess helps squash a bug!"),
        ("", "full-stack", "chore"): (10, "Your Full-stack versatility enhances the codebase!")
    }
    boost, message = boosts.get((language.lower(), specialization.lower(), commit_type), (0, ""))
    if message:
        print(message)
    return boost

def interactive_commit_review(messages):
    """Displays commit message suggestions and allows the user to choose or regenerate messages."""
    for idx, message in enumerate(messages, start=1):
        print(f"\nSuggested Commit Message {idx}:\n{message}")
    choice = input("\nChoose a commit message by number, or type 'r' to regenerate: ")
    return messages[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= len(messages) else None

def generate_commit_message_for_frontend(commit_type, custom_message, project_dir):
    """Generates a commit message for use in the Flask app, using the specified project directory."""
    config = load_config(project_dir)
    language = config.get("language", "Unknown")
    specialization = config.get("specialization", "Generalist")

    repo = check_or_initialize_git_repo(project_dir)
    if not repo:
        return "No Git repository found, and initialization declined."

    changes = get_git_changes(repo)
    diff_summary = changes[0]["diff"] if changes else "general updates"

    commit_message = generate_commit_message(
        commit_type=commit_type,
        custom_message=custom_message,
        language=language,
        framework=config.get("framework", "Unknown"),
        diff_summary=diff_summary,
        length="brief"
    )

    experience = sum(len(change['diff']) for change in changes)
    boost = calculate_specialization_boost(language, specialization, commit_type)
    experience += boost
    return commit_message, experience, len(changes), boost

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

            custom_message = input("Enter your commit message (or leave blank to auto-generate): ").strip()

            commit_message, experience, enemies_slain, boost = generate_commit_message_for_frontend(
                commit_type, custom_message, project_dir
            )

            print("\n--- Quest Result ---")
            print(f"Commit Message: {commit_message}")
            print(f"You gained {experience} experience points and slayed {enemies_slain} enemies.")
            print(f"Specialization Boost: {boost}")
            print("--------------------\n")

        elif user_input == "setup":
            setup_config(project_dir)
            print("Configuration completed.\n")
        elif user_input == "help":
            print("Commands:\n- generate: Begin your quest to generate a commit message.\n- setup: Configure project settings.\n- help: Show available commands.\n- exit: Exit the quest.")
        elif user_input == "exit":
            print("Farewell, brave coder! Until next time.")
            break
        else:
            print("Unknown command. Type 'help' to see available commands.")

if __name__ == "__main__":
    main()
