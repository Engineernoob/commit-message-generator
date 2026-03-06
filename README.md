# CommitQuest ⚔️

**An AI‑Powered Git Commit Roguelike in the Terminal**

CommitQuest turns writing Git commit messages into a **retro ASCII dungeon crawler**.

Instead of typing boring commits, you explore a **procedurally generated repo dungeon**, fight enemies representing your code changes, and use an **AI spell (via Ollama)** to craft high‑quality **Conventional Commit messages**.

The better the commit message, the stronger your attack.

---

# Preview

```
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
```

---

# Features

## Procedural Repo Dungeon

Your Git repository becomes a dungeon.

- **Folders → rooms**
- **Code changes → enemies**
- **Diff size → difficulty**

Every scan generates a **new combat arena**.

---

## AI Commit Message Generator

CommitQuest uses **local AI models via Ollama** to generate commit messages.

Example command:

```
gen feat
```

AI response:

```
feat: add dungeon map rendering system
```

That commit message becomes your **attack spell**.

---

## Roguelike Combat System

Enemies spawn based on the type of files changed.

| Change Type | Enemy |
|-------------|------|
| Python files | Python Serpent |
| JS / TS | JavaScript Gremlin |
| Config files | Config Golem |
| Docs changes | Documentation Lich |
| Large diffs | Diff Dragon (Boss) |

When you run:

```
commit
```

you attack the enemy and perform the Git commit simultaneously.

---

## First‑Person ASCII Combat

CommitQuest renders a **first‑person ASCII weapon HUD**.

Weapons depend on the commit type.

| Commit Type | Weapon |
|-------------|--------|
| feat | Sword |
| fix | Dagger |
| refactor | Staff |
| docs | Scroll |
| test | Hammer |
| chore | Torch |

Example:

```
gen feat
commit
```

Result:

```
You swing your sword!
Python Serpent takes 18 damage!
```

---

# Why This Project Exists

Developers hate writing commit messages.

CommitQuest turns the task into a **game** while enforcing good practices:

- Conventional commits
- Clear summaries
- Better commit discipline

It also demonstrates how **AI tools can integrate directly into developer workflows**.

---

# Tech Stack

- **Python**
- **Textual** (terminal UI framework)
- **Ollama** (local LLM inference)
- **Git CLI**
- **Procedural generation**
- **ASCII rendering**

---

# Project Structure

```
backend/
│
├── tui_app.py        # Textual game interface
├── commit_core.py    # Git + commit generation logic
├── llm_provider.py   # Ollama integration
├── dungeon.py        # procedural dungeon generation
├── enemies.py        # enemy definitions
├── player.py         # player HUD and weapons
└── ascii.tcss        # terminal UI styling
```

---

# Future Upgrades

Planned improvements:

- Boss fights for large diffs
- Procedural dungeon maps
- Enemy animations
- Git stash / branch spells
- AI commit splitting suggestions
- Automatic changelog generation

---

# Author

**Taahirah Denmark**  
Computer Science student building AI developer tools.

GitHub:

https://github.com/Engineernoob

---

# License

MIT
