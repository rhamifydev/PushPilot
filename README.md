# 🚀 PushPilot

> **Intelligent Multi-Framework Git & GitHub Autopilot**  
> One command to initialize Git, link your GitHub repository, generate conventional commits, and push. Includes an **Internal AI Commit Generator** and a **Feature-Complete File Watcher**.

[![PyPI version](https://img.shields.io/pypi/v/pushpilot.svg?color=blue)](https://pypi.org/project/pushpilot/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pushpilot.svg?color=brightgreen)](https://pypi.org/project/pushpilot/)
[![GitHub](https://img.shields.io/badge/GitHub-rhamifydev%2FPushPilot-blue?logo=github)](https://github.com/rhamifydev/PushPilot)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## ⚡ Instant Install

Install PushPilot globally in a single command:

```bash
pip install pushpilot
```

*(Or via [pipx](https://pypa.github.io/pipx/) for an isolated global CLI environment: `pipx install pushpilot`)*

Once installed, the command `pushpilot` (or short aliases `pilot` and `push`) is instantly available in any terminal window and across all your projects!

---

## 🌟 Key Features

### 1. Zero-Config One-Command GitHub Setup
```bash
pushpilot https://github.com/username/my-repo.git
```
- Initializes Git automatically if not yet initialized (defaults branch to `main`).
- Links the `origin` remote to your GitHub repository.
- Detects if GitHub was created with a default README or `.gitignore` and performs conflict-free rebase.
- Generates a framework-tailored `.gitignore` if none exists.
- Stages all files, creates a conventional semantic commit, and pushes to GitHub!

### 2. Subsequent 1-Second Push
```bash
pushpilot
```
- Detects all modified, added, and deleted files.
- Generates a **Conventional Semantic Commit Message** (e.g. `feat(auth): implement login endpoint in FastAPI`).
- Stages, commits, and pushes to GitHub in 2 seconds.

### 3. Internal AI Commit Intelligence (Auto-Detecting)
- **Coding with AI?** If you are working in an AI-assisted environment (**Google Antigravity IDE**, **Cursor**, **Aider**, **Claude Code**, **Cline**) or have an AI API configured (**Gemini**, **OpenAI**, **Anthropic**, **Groq**, or local **Ollama**), PushPilot detects the active developer intent and git diff to produce **ultra-accurate, laser-focused Conventional Commit messages**.
- **Not coding with AI?** PushPilot instantly and seamlessly uses its **smart default heuristic engine** (zero dependencies, zero delay, offline-friendly).
- Use `--no-ai` to force the default rule-based engine, or `--ai` to force AI mode.

### 4. Feature-Completion File Watcher
```bash
pushpilot --watch
```
- Monitors your project files while ignoring build artifacts (`node_modules`, `venv`, `dist`, `.next`, `target`, etc.).
- Uses a **Feature Settlement Window**: as you rapidly edit files and tests, changes accumulate. When you finish coding a feature and edits settle (e.g., 8s cooldown), PushPilot automatically commits and ships your feature to GitHub.

### 5. Multi-Language & Multi-Framework Stack Detection
PushPilot automatically understands:
- **JavaScript / TypeScript**: React, Next.js, Vue, Nuxt, Angular, Svelte, Vite, Node.js, Express, NestJS
- **Python**: Django, FastAPI, Flask, Standard Python, AI/ML
- **Rust**: Cargo projects
- **Go**: Go modules
- **Dart / Flutter**: Mobile & Web Flutter applications
- **Java / Kotlin**: Spring Boot, Maven, Gradle
- **C# / .NET**: ASP.NET Core, .NET solutions
- **PHP**: Laravel, Symfony, Composer
- **Ruby**: Ruby on Rails, Bundler

---

## 🛠️ Usage Examples

### Initialize & Link a Project in One Step
```bash
pushpilot https://github.com/rhamifydev/PushPilot.git
```

### Quick Push with Auto Commit Message
```bash
pushpilot
```

### Continuous Feature Watcher
```bash
pushpilot --watch
# or with custom settlement cooldown (e.g. 12 seconds)
pushpilot -w --cooldown 12
```

### Push with a Custom Commit Message
```bash
pushpilot -m "feat(billing): integrate Stripe payment webhook"
```

### Preview Actions without Modifying Git (Dry Run)
```bash
pushpilot --dry-run
```

### Inspect Detected Project Stack
```bash
pushpilot --detect
```

### Interactive Remote Setup
```bash
pushpilot --setup
```

---

## 📋 CLI Reference

| Command / Option | Description |
| :--- | :--- |
| `pushpilot [URL]` | Sync & push to GitHub (optionally initializes git and links remote) |
| `-w`, `--watch` | Continuous watcher mode with feature-completion settlement |
| `--cooldown SEC` | Seconds of inactivity before triggering feature commit (default: 8s) |
| `-m`, `--message MSG` | Override auto-generated message with a custom commit message |
| `-b`, `--branch NAME` | Target git branch (defaults to active branch / `main`) |
| `-r`, `--remote NAME` | Target git remote (default: `origin`) |
| `--ai` | Explicitly enable AI-powered commit generation |
| `--no-ai` | Disable AI detection and force default rule-based conventional commit |
| `--detect` | Print detected language, framework, ecosystem, and git status |
| `--setup` | Interactively link or update GitHub repository URL |
| `--init-gitignore` | Create/reset tailored `.gitignore` for the detected stack |
| `--dry-run` | Simulate actions without staging, committing, or pushing |
| `-v`, `--version` | Display version information |

---

## 🤝 Contributing & License

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/rhamifydev/PushPilot/issues).

Distributed under the **MIT License**. See `LICENSE` for more information.
