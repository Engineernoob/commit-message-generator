from transformers import pipeline
from git import Repo
import torch
import os

# Check if a GPU is available
device = 0 if torch.cuda.is_available() else -1

# Initialize a text generation pipeline with the device set for GPU or CPU
generator = pipeline('text-generation', model='distilgpt2', device=device)

def generate_commit_message(commit_type, custom_message, language, framework, diff_summary, length="brief"):
    """
    Generates a commit message based on the commit type, optional custom message,
    project language and framework, diff summary, and message length.
    
    Parameters:
    - commit_type: Type of commit (e.g., feat, fix, chore).
    - custom_message: Optional custom message provided by the user.
    - language: The primary language of the project (e.g., Python, JavaScript).
    - framework: The framework used in the project (e.g., Flask, React).
    - diff_summary: Summary of changes from the diff.
    - length: Length of the message (either "brief" or "detailed"). Default is "brief".
    
    Returns:
    A generated commit message as a string.
    """
    if custom_message:
        # Use custom message if provided
        return f"{commit_type}: {custom_message}"
    else:
        # Customize prompt based on commit type and length
        length_prompt = "a brief" if length == "brief" else "a detailed"
        prompt = f"Generate {length_prompt} {commit_type} commit message for a {language} {framework} project: {diff_summary}"
        
        # Generate the commit message
        result = generator(prompt, max_length=100 if length == "detailed" else 50, num_return_sequences=1)
        return result[0]["generated_text"]

def find_repo_root():
    """
    Finds the Git repository root by moving up directories until a `.git` folder is found.
    Raises an exception if the repository root is not found.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while current_dir != '/':  # Stop at the root directory if `.git` is not found
        if '.git' in os.listdir(current_dir):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    raise Exception("Git repository root not found")

# Initialize the repository with the dynamically found path
repo_path = find_repo_root()
repo = Repo(repo_path)

def get_git_changes():
    """
    Retrieves unstaged changes with diffs for the current Git repository.
    Returns a list of dictionaries with file paths and diff summaries.
    """
    changes = []

    # Get unstaged changes by checking the diff
    for item in repo.index.diff(None):  # None indicates unstaged changes
        file_path = item.a_path
        diff = repo.git.diff(file_path)  # Retrieve the diff for this file
        diff_summary = analyze_diff(diff)  # Summarize the diff
        changes.append({"file": file_path, "diff": diff_summary})

    return changes

def analyze_diff(diff):
    """
    Analyzes the diff to extract keywords and summarize changes.
    Returns a summary string describing the changes.
    """
    keywords = set()
    frontend_files = ["js", "jsx", "ts", "tsx", "css", "html"]
    backend_files = ["py", "go", "rb", "php"]
    summary = ""

    for line in diff.splitlines():
        # Identify added lines (assuming '+' at start)
        if line.startswith('+') and not line.startswith('+++'):
            keywords.update(line.split())  # Simple keyword extraction by splitting on whitespace

        # Add context based on file types
        if any(ext in line for ext in frontend_files):
            summary += "frontend changes "
        elif any(ext in line for ext in backend_files):
            summary += "backend updates "

    # Add keywords to the summary for more context
    summary += " | ".join(keywords) if keywords else "general updates"
    return summary

# Example usage
if __name__ == "__main__":
    # Retrieve Git changes and generate commit messages for each
    changes = get_git_changes()
    for change in changes:
        # Generate a commit message using a sample configuration
        commit_message = generate_commit_message(
            commit_type="feat",
            custom_message="",  # Leave blank to use AI generation
            language="Python",
            framework="Flask",
            diff_summary=change["diff"],
            length="brief"  # Can change to "detailed" for a longer message
        )
        print(f"Suggested commit message for {change['file']}:\n{commit_message}\n")
