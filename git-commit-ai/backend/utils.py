import json
import os
import logging

# File path for storing commonly used commit messages
COMMON_MESSAGES_FILE = "common_messages.json"

# Configure logging for error handling
logging.basicConfig(
    filename="commit_tool.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_common_messages():
    """
    Loads common commit messages from a JSON file.
    Returns a dictionary of stored commit messages.
    """
    if os.path.exists(COMMON_MESSAGES_FILE):
        with open(COMMON_MESSAGES_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_common_message(context_summary, message):
    """
    Saves a new commit message to the JSON file based on context summary.
    """
    common_messages = load_common_messages()
    common_messages[context_summary] = message
    with open(COMMON_MESSAGES_FILE, 'w') as f:
        json.dump(common_messages, f)

def get_similar_message(context_summary):
    """
    Retrieves a similar past commit message based on context summary.
    Returns the stored message if found, otherwise None.
    """
    common_messages = load_common_messages()
    return common_messages.get(context_summary, None)

def log_error(error):
    """
    Logs an error message to the log file.
    """
    logging.error(f"Error: {error}")
