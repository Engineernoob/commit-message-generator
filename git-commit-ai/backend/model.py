from transformers import pipeline
from git import Repo

# Initialize a text generation pipeline
generator = pipeline('text-generation', model='distilgpt2')

def generate_commit_message(commit_type, custom_message, language, framework, diff_summary):
    """
    Generates a commit message based on the commit type, optional custom message, 
    project language and framework, and diff summary.
    """
    if custom_message:
        # Use custom message if provided
        return f"{commit_type}: {custom_message}"
    else:
        # Generate a message based on diff summary if no custom message provided
        prompt = f"Generate a {commit_type} commit message for a {language} {framework} project: {diff_summary}"
        result = generator(prompt, max_length=50, num_return_sequences=1)
        return result[0]["generated_text"]

def get_git_changes():
    """
    Retrieves unstaged changes with diffs for the current Git repository.
    Returns a list of dictionaries with file paths and diff summaries.
    """
    repo = Repo('.')  # Initialize the repository in the current directory
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
            diff_summary=change["diff"]
        )
        print(f"Suggested commit message for {change['file']}:\n{commit_message}\n")