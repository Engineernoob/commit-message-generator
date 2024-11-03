from git import Repo

# Path to your git repository
repo_path = '.'  # Adjust if not in the root of the repo

# Initialize the repository
repo = Repo(repo_path)

def get_git_changes():
    changes = []
    for item in repo.index.diff(None):  # None shows unstaged changes
        file_path = item.a_path
        diff = item.diff.decode('utf-8')
        changes.append({"file": file_path, "diff": diff})
    return changes

# Print the current changes
if __name__ == "__main__":
    changes = get_git_changes()
    for change in changes:
        print(f"File: {change['file']}")
        print(f"Diff:\n{change['diff']}")
