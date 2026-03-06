## CommitQuest ⚔️

An AI-Powered Git Commit Roguelike in the Terminal

CommitQuest turns writing Git commit messages into a retro ASCII dungeon crawler.

Instead of typing boring commits, you explore a procedurally generated repo dungeon, fight enemies representing code changes, and use an AI spell (via Ollama) to craft high-quality Conventional Commit messages.

The better the commit message, the stronger your attack.

⸻
## Preview 
╔════════════════════════════════════════════════════╗
║ QUIET HALL • FLOOR 1 • ROOM backend                ║
║ FLOOR 1 | Lv 2 Commit Squire | XP 340              ║
║                                                    ║
║        ░      ░           ░                         ║
║                                                    ║
║                &                                    ║
║                                                    ║
║      @                                             ║
║                                                    ║
║        ░         ░                                  ║
╚════════════════════════════════════════════════════╝

@ you    & enemy    ░ cover

You awaken in the Repo Dungeon...
Type `scan` to search for enemies.

## Features

Procedural Repo Dungeon

Your Git repository becomes a dungeon:
	•	Folders → rooms
	•	Code changes → enemies
	•	Diff size → difficulty

Each scan generates a new combat arena.

⸻

## AI Commit Message Generator

CommitQuest uses local AI models via Ollama to generate high-quality commit messages.

Example:
gen feat

AI response:
feat: add dungeon map rendering system

The generated message becomes your attack spell.

Roguelike Combat System

Enemies spawn based on your code changes:
Change Type                  

Python files
Python Serpent
JS / TS
JavaScript Gremlin
Config files
Config Golem
Docs changes
Documentation Lich
Large diffs
Diff Dragon (Boss)
