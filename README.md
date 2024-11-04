Commit Message Quest:

Commit Message Quest is a text-based adventure web app that guides users through the process of generating meaningful Git commit messages. It incorporates an AI-powered model to create commit messages, and users earn "experience points" and "enemies slain" based on their Git changes.

Table of Contents
Features
Setup and Installation
Frontend Commands
Backend API Endpoints
Configuration
Auto-Commit Feature
Development Notes

Features
AI-Powered Commit Messages: Automatically generate Git commit messages based on changes.
Game-Like Feedback: Earn "experience points" and "enemies slain" for Git insertions and deletions.
Setup and Configuration: Setup project configuration with details such as primary programming language, framework, and specialization.
Auto-Commit: Optionally commit changes automatically after generating a commit message.
Temporary Directory Support: Automatically create a temporary project directory if none is provided.
Setup and Installation
Requirements
Python 3.x
Node.js and npm (for frontend development)
Git
Flask and required Python packages (flask, flask_cors, gitpython, tempfile)
A frontend framework like React (already integrated in this project)
Backend Setup
Clone the repository and navigate to the project directory:

bash
Copy code
git clone <repository-url>
cd Commit-Message-Quest
Set up a virtual environment and install dependencies:

bash
Copy code
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Start the Flask server:

bash
Copy code
python app.py
Frontend Setup
Navigate to the frontend directory:

bash
Copy code
cd frontend/my-pwa-app
Install frontend dependencies:

bash
Copy code
npm install
Start the frontend development server:

bash
Copy code
npm start
The app should now be accessible at http://localhost:3000.

Frontend Commands
The app supports the following commands:

setup: Starts the project setup process. This will prompt the backend to create a configuration file if it doesn't already exist.
generate [type] [message]: Generates a commit message based on the provided type and message.
Example: generate feat Added new feature
clear: Clears the message history on the UI.
help: Displays a list of available commands.
Backend API Endpoints
/setup (POST)
Initiates the project setup process.

Request Body:

projectDir (optional): Path to the project directory. If not provided, a temporary directory will be created.
createConfig: Set to "yes" to create a new configuration file if one doesn't exist.
Response:

message: Status of the setup process.
config: Configuration details for the project.
projectDir: Path to the project directory used.
/generateCommitMessage (POST)
Generates a commit message based on Git changes and configuration settings.

Request Body:

projectDir (required): Path to the project directory.
commitType (required): Type of the commit (e.g., feat, fix, chore).
customMessage: Custom commit message to include.
autoCommit: Boolean flag to auto-commit the generated message.
Response:

commitMessage: The generated commit message.
experience: Experience points based on insertions and deletions.
enemiesSlain: Number of changes in the Git repository.
autoCommitResponse: Status of the auto-commit process.
Configuration
The project setup process creates a configuration file in the project directory (or a temporary one if no directory is specified). This configuration file includes:

language: Primary programming language of the project.
framework: Framework used in the project (if applicable).
specialization: The user's specialization, such as AI, Backend, or Frontend.
Auto-Commit Feature
The /generateCommitMessage endpoint accepts an autoCommit parameter, which will attempt to automatically commit the changes with the generated message.

Example:

json
Copy code
{
  "projectDir": "/path/to/project",
  "commitType": "feat",
  "customMessage": "Added a new feature",
  "autoCommit": true
}
Development Notes
Temporary Directory Creation
If no projectDir is provided, a temporary directory will be created and used for the session. This is particularly useful for users testing the setup without an existing Git project.

Error Handling
The backend will respond with error messages for invalid directories, missing configurations, or failed auto-commit attempts.