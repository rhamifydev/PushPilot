# Git Auto Commit & Push (Python)

A Python tool to automate `git add`, `git commit`, and `git push` workflows. Works with standard Python libraries (no external dependencies required).

## Features

- **One-Command Sync**: Automatically stages changes, commits with descriptive messages, and pushes to your remote branch.
- **Smart Commit Messages**: Inspects changed, added, and deleted files to generate meaningful commit messages (or specify your own with `-m`).
- **Continuous Watch Mode (`--watch`)**: Runs in the background and automatically commits & pushes whenever file changes are detected.
- **Safety Checks**: Checks for clean working tree, avoids blank commits, handles upstream tracking (`-u`), and supports rebase pulls (`-p`).
- **Dry Run Mode (`--dry-run`)**: Test what commands will be executed without modifying anything.
- **Programmatic Import**: Use `from git_auto import auto_push_commit` inside your own Python apps, scrapers, data pipelines, or automation scripts.

---

## Quick Usage

### 1. One-Click Commit & Push (Smart Auto Message)
```bash
python git_auto.py
```
*Detects changes, crafts a message like `Update app.py & Add script.py [2026-10-24 11:00:00]`, and pushes to the current branch.*

### 2. Custom Commit Message
```bash
python git_auto.py -m "Feature: implement user authentication"
```

### 3. Pull Before Pushing (Rebase)
```bash
python git_auto.py -p -m "Sync latest changes"
```

### 4. Continuous Watch Mode (Auto-Sync)
Monitors your workspace directory every 30 seconds (or custom interval) and pushes when files change:
```bash
python git_auto.py --watch --interval 60
```

### 5. Dry Run (Preview changes without pushing)
```bash
python git_auto.py --dry-run
```

### 6. Initialize & Configure Remote
```bash
python git_auto.py --init --set-remote https://github.com/your-username/your-repo.git
```

---

## Programmatic Usage in Python

You can easily integrate it into any Python script:

```python
from pathlib import Path
from git_auto import auto_push_commit

auto_push_commit(
    repo_dir=Path("./"),
    message="Automated pipeline output update",
    remote="origin",
    pull_first=True
)
```

---

## Options Summary

| Argument | Description | Default |
| :--- | :--- | :--- |
| `-m`, `--message` | Custom commit message | Auto-generated summary |
| `-b`, `--branch` | Target branch | Active branch |
| `-r`, `--remote` | Target remote repository | `origin` |
| `-p`, `--pull-first` | Run `git pull --rebase` before pushing | `False` |
| `-w`, `--watch` | Continuous watcher mode | `False` |
| `-i`, `--interval` | Watch check interval (seconds) | `30` |
| `--dry-run` | Simulate actions without running | `False` |
| `--init` | Initialize Git repo if missing | `False` |
| `--set-remote` | Add or update origin remote URL | `None` |
