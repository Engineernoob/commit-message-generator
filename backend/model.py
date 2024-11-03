from transformers import pipeline

# Initialize a text generation pipeline
generator = pipeline('text-generation', model='distilgpt2')

def generate_commit_message(change_summary):
    prompt = f"Generate a commit message: {change_summary}"
    result = generator(prompt, max_length=50, num_return_sequences=1)
    return result[0]["generated_text"]

def get_git_changes():
    # Placeholder for the actual implementation
    return [{"diff": "Example change description"}]  # Example return value

# Example usage
if __name__ == "__main__":
    changes = get_git_changes()
    for change in changes:
        commit_message = generate_commit_message(change["diff"][:100])  # Use a subset of diff for brevity
        print(f"Suggested commit message:\n{commit_message}")
