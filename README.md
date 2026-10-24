# 🚀 PushPilot

> **Intelligent Multi-Framework Git & GitHub Autopilot**  
> One command to initialize Git, link your GitHub repository, generate conventional commits, and push. Includes a **Feature-Complete File Watcher** that automatically syncs code to GitHub whenever a feature is completed.

[![GitHub](https://img.shields.io/badge/GitHub-rhamifydev%2FPushPilot-blue?logo=github)](https://github.com/rhamifydev/PushPilot)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## 🌟 What PushPilot Does

1. **Zero-Config One-Command Setup (`pushpilot <github-url>`)**:
   - Give it your GitHub repo URL once: `pushpilot https://github.com/username/repo.git`.
   - If Git is not initialized, PushPilot initializes it with default branch `main`.
   - Links the `origin` remote automatically.
   - Detects if GitHub was initialized with a default README or `.gitignore` and merges/rebases seamlessly without conflicts.
   - Generates a framework-tailored `.gitignore` if none exists.
   - Stages all files, creates a conventional commit, and pushes directly to GitHub!

2. **Subsequent One-Command Push (`pushpilot` or `auto-push`)**:
   - Devs just write `pushpilot` (or `auto-push`).
   - Detects all modified/added/deleted files.
   - Generates a **Conventional Semantic Commit Message** (e.g., `feat(auth): implement login endpoint in FastAPI`).
   - Stages, commits, and pushes to GitHub in 2 seconds.

3. **Feature-Completion File Watcher (`pushpilot -w`)**:
   - Devs code while running `pushpilot -w`.
   - Monitors file changes while ignoring build folders (`node_modules`, `venv`, `target`, `dist`, `.next`, etc.).
   - Uses an intelligent **Feature Settlement Timer**: as you rapidly edit components/tests/views, changes accumulate. When you finish editing and changes settle (e.g., 8s cooldown), PushPilot recognizes feature completion, crafts the semantic commit message, and pushes to GitHub.

4. **Multi-Language & Multi-Framework Intelligence**:
   - **JavaScript / TypeScript**: React, Next.js, Vue, Nuxt, Angular, Svelte, Vite, Node.js, Express, NestJS
   - **Python**: Django, FastAPI, Flask, standard Python, AI/ML
   - **Rust**: Cargo projects
   - **Go**: Go modules
   - **Dart / Flutter**: Mobile & Web Flutter apps
   - **Java / Kotlin**: Spring Boot, Maven, Gradle
   - **C# / .NET**: ASP.NET Core, .NET solutions
   - **PHP**: Laravel, Symfony, Composer
   - **Ruby**: Ruby on Rails, Bundler

---

## 🚀 Installation & Setup

### Option 1: Direct in Project (Windows Runners Included)
Run any of the included batch/PowerShell scripts:
```bash
auto-push
# or
pushpilot
# or
push
# or
pilot
```

### Option 2: Install System-Wide Global Command
Install once in editable mode:
```bash
pip install -e .
```
Now `pilot`, `push`, `pushpilot`, `auto-push`, and `autopush` are accessible in **any terminal window and any project on your computer!**

---

## 🛠️ Usage Examples

### 1. Initialize & Link GitHub in One Step
```bash
pushpilot https://github.com/rhamifydev/PushPilot.git
```
*Initializes Git if needed, sets default branch `main`, links remote `origin`, stages, commits, and pushes to GitHub.*

### 2. Instant Auto-Push (Subsequent uses)
```bash
pushpilot
```

### 3. Continuous Feature-Complete Watcher
```bash
pushpilot --watch
```
*Watches files and pushes to GitHub whenever you finish coding a feature increment!*

Customizing the feature settlement window:
```bash
pushpilot -w --cooldown 10
```

### 4. Custom Commit Message
```bash
pushpilot -m "feat(payment): integrate Stripe checkout webhook"
```

### 5. Inspect Detected Project Stack
```bash
pushpilot --detect
```

### 6. Interactive Setup / Update GitHub Remote
```bash
pushpilot --setup
```

### 7. Dry-Run (Preview what would happen)
```bash
pushpilot --dry-run
```

---

## 📋 CLI Reference

| Command / Option | Description |
| :--- | :--- |
| `pushpilot [URL]` | Run auto-sync (optionally initialize & link GitHub repository URL) |
| `-w`, `--watch` | Continuous watcher mode with feature-completion settlement |
| `--cooldown SEC` | Seconds of inactivity before triggering feature commit (default: 8s) |
| `-m`, `--message MSG` | Override auto-generated message with a custom commit message |
| `-b`, `--branch NAME` | Target git branch (defaults to active branch / `main`) |
| `-r`, `--remote NAME` | Target git remote (default: `origin`) |
| `--detect` | Print detected language, framework, ecosystem, and git status |
| `--setup` | Interactively link or update GitHub repository URL |
| `--init-gitignore` | Create/reset tailored `.gitignore` for the detected stack |
| `--dry-run` | Simulate actions without staging, committing, or pushing |
| `-v`, `--version` | Display version information |
