# ⚡ AutoPush

> **Professional Multi-Language & Multi-Framework Git & GitHub Automation**  
> One command to stage, generate conventional commit messages, link your GitHub repository, and push. Includes a **Feature-Complete File Watcher** that automatically syncs whenever you finish writing a feature.

---

## 🌟 What AutoPush Does

1. **One-Command Dev Workflow (`auto-push`)**:
   - Devs type `auto-push` in any project terminal.
   - If Git is not initialized, it initializes it with `main` branch.
   - If no GitHub remote exists, it interactively prompts for your repo URL (HTTPS or SSH), links it, and configures upstream tracking.
   - If `.gitignore` is missing, it auto-generates framework-tailored rules.
   - Automatically detects modified, added, and deleted files.
   - Generates a **Conventional Semantic Commit Message** (e.g. `feat(auth): implement login endpoint in FastAPI`).
   - Stages, commits, and pushes directly to GitHub!

2. **Feature-Completion File Watcher (`auto-push -w`)**:
   - Devs start coding while running `auto-push -w`.
   - The watcher monitors file changes while automatically ignoring build/cache folders (`node_modules`, `venv`, `target`, `dist`, `.next`, etc.).
   - Employs an intelligent **Feature Settlement Timer**: as you rapidly edit components/tests/views, changes accumulate. When you finish editing and changes settle (e.g., 8s cooldown), AutoPush recognizes feature completion, crafts the semantic commit message, and pushes to GitHub.

3. **Multi-Language & Multi-Framework Intelligence**:
   - **JavaScript / TypeScript**: React, Next.js, Vue, Nuxt, Angular, Svelte, Vite, Express, NestJS
   - **Python**: Django, FastAPI, Flask, standard Python, AI/ML
   - **Rust**: Cargo projects
   - **Go**: Go modules
   - **Dart / Flutter**: Flutter mobile/web apps
   - **Java / Kotlin**: Spring Boot, Maven, Gradle
   - **C# / .NET**: ASP.NET, .NET Core
   - **PHP**: Laravel, Symfony, Composer
   - **Ruby**: Rails, Bundler

---

## 🚀 Quick Start

### Option A: Direct Command (Windows Shortcut)
From your terminal inside this project directory:
```bash
auto-push
```
Or with PowerShell:
```powershell
.\auto-push.ps1
```

### Option B: System-Wide Global Command
Install once in editable mode:
```bash
pip install -e .
```
Now you can run `auto-push` or `autopush` in **any terminal window and any project on your computer!**

---

## 🛠️ Usage Examples

### 1. Instant One-Command Auto-Push
```bash
auto-push
```
*If your project does not have a GitHub remote yet, AutoPush prompts you for the repository link, links `origin`, sets branch to `main`, and pushes.*

### 2. Feature-Complete Auto-Watch Mode
Keep this running in a terminal while you work on features:
```bash
auto-push --watch
```
*Auto-pushes to GitHub whenever you finish coding a feature increment!*

Customizing the feature settlement window:
```bash
auto-push -w --cooldown 12
```

### 3. Custom Commit Message
```bash
auto-push -m "feat(payment): integrate Stripe checkout webhook"
```

### 4. Inspect Detected Stack
Check what AutoPush detects for your current project:
```bash
auto-push --detect
```

### 5. Setup / Change Linked GitHub Repo
```bash
auto-push --setup
```

### 6. Generate Framework-Specific `.gitignore`
```bash
auto-push --init-gitignore
```

### 7. Dry-Run (Preview what would happen)
```bash
auto-push --dry-run
```

---

## 📋 CLI Reference

| Command / Option | Description |
| :--- | :--- |
| `auto-push` | Run full auto-sync (inspect, stage, semantic commit, push) |
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
