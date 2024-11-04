import os
import json
from model import generate_commit_message, get_git_changes, analyze_diff
from utils import save_common_message, get_similar_message, log_error

# Configuration file path
CONFIG_FILE = "config.json"

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
    config["specialization"] = input("Enter your specialization (e.g., AI, Front-end, Backend): ")
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
    return config

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
    else:
        print("No special boost for this class and specialization.")

    return boost

def main():
    print("Welcome to Commit Message Quest!")
    print("Type 'generate' to start your quest.\n")

    while True:
        user_input = input("> ").strip().lower()

        if user_input == "generate":
            # Step 1: Choose a class (commit type)
            print("\nChoose your class:")
            print("[feat] Magician - Adds new features")
            print("[fix] Warrior - Fixes bugs")
            print("[chore] Archer - General maintenance\n")
            commit_type = input("Enter your class: ").strip().lower()

            if commit_type not in ["feat", "fix", "chore"]:
                print("Invalid class! Please choose feat, fix, or chore.")
                continue

            # Step 2: Enter a custom commit message
            custom_message = input("\nEnter your commit message: ").strip()

            # Step 3: Generate commit message and calculate stats
            config = load_config()
            language = config.get("language", "Unknown")
            framework = config.get("framework", "Unknown")
            specialization = config.get("specialization", "Generalist")
            
            # Retrieve Git changes
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

            # Calculate experience and enemies slain
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

            # Display the "game-like" result
            print("\n--- Quest Result ---")
            print(f"Commit Message: {commit_message}")
            print(f"You gained {experience} experience points (with a {boost} specialization boost) and slayed {enemies_slain} enemies.")
            print("--------------------\n")

            # Option to continue or exit
            cont = input("Would you like to continue your quest? (yes/no): ").strip().lower()
            if cont != "yes":
                print("Farewell, brave coder! Until next time.")
                break
        elif user_input == "setup":
            setup_config()
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
