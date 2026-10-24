"""
Autopush Command-Line Interface.
Professional multi-language & multi-framework Git automation.
"""

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from autopush import __version__
from autopush.commit_gen import generate_commit_message
from autopush.detector import StackDetector
from autopush.git_ops import (
    GitError,
    commit,
    ensure_gitignore,
    ensure_repo_ready,
    get_current_branch,
    get_git_status_changes,
    get_remotes,
    has_unpushed_commits,
    is_git_repo,
    push,
    setup_remote_interactive,
    stage_all,
)
from autopush.watcher import FeatureWatcher


def banner():
    print(
        f"""
╔═════════════════════════════════════════════════════════════╗
║                   AUTOPUSH v{__version__}                           ║
║   Professional Multi-Framework Git & GitHub Automation      ║
╚═════════════════════════════════════════════════════════════╝
"""
    )


def run_single_sync(
    root: Path,
    message: str | None = None,
    branch: str | None = None,
    remote: str = "origin",
    dry_run: bool = False,
    interactive: bool = True,
) -> bool:
    """Performs a full automated check, stage, commit, and push cycle."""
    # Disable interactive prompts if dry_run or stdin is not a terminal
    if dry_run or not sys.stdin.isatty():
        interactive = False

    # 1. Detect Stack
    stack = StackDetector.detect(root)
    print(f"[STACK] Detected: {stack.language} | Framework: {stack.framework or 'None'} | Ecosystem: {stack.ecosystem}")

    # 2. Ensure Git & Remote Setup
    ensure_repo_ready(root, interactive=interactive)

    # 3. Ensure .gitignore
    ensure_gitignore(root, stack, interactive=interactive)

    # Active branch and remotes
    active_branch = branch or get_current_branch(root)
    remotes = get_remotes(root)

    print(f"[BRANCH] Active Branch : {active_branch}")
    if remote in remotes:
        print(f"[REMOTE] Target Remote : {remote} ({remotes[remote]})")
    else:
        print(f"[REMOTE] Warning: Remote '{remote}' is not configured.")

    # 4. Check Changes
    changes = get_git_status_changes(root)
    if not changes:
        if remote in remotes and has_unpushed_commits(root, remote, active_branch):
            print("[INFO] Working tree clean, but unpushed commits exist. Pushing to GitHub...")
            if not dry_run:
                push(root, remote, active_branch)
                print(f"[SUCCESS] Pushed unpushed commits to {remote}/{active_branch}!")
            else:
                print(f"[DRY-RUN] Would push to {remote}/{active_branch}")
            return True
        else:
            print("[INFO] Working tree clean. Nothing to commit or push.")
            return True

    print(f"[CHANGES] Detected {len(changes)} modified/new file(s):")
    for status, file_path in changes[:8]:
        print(f"   [{status or '?'}] {file_path}")
    if len(changes) > 8:
        print(f"   ... and {len(changes) - 8} more file(s)")

    # 5. Generate Commit Message
    commit_msg = generate_commit_message(changes, stack, custom_msg=message)
    print(f"[COMMIT] Generated Message: \"{commit_msg}\"")

    if dry_run:
        print(f"[DRY-RUN] Would stage all files ('git add -A')")
        print(f"[DRY-RUN] Would commit with message: \"{commit_msg}\"")
        if remote in remotes:
            print(f"[DRY-RUN] Would push to {remote}/{active_branch}")
        return True

    # 6. Stage & Commit
    print("[STAGING] Staging all files...")
    stage_all(root)

    print("[COMMITTING] Committing changes...")
    commit(root, commit_msg)
    print("[SUCCESS] Changes committed successfully.")

    # 7. Push to Remote
    remotes = get_remotes(root)
    if remote not in remotes:
        print(f"\n[NOTICE] Remote '{remote}' not linked yet.")
        if interactive:
            new_remote = setup_remote_interactive(root)
            if not new_remote:
                print("[INFO] Commit saved locally. Link a remote when you are ready to push.")
                return True
        else:
            print(f"[WARNING] Remote '{remote}' not configured. Run 'auto-push --setup' to link a GitHub repo.")
            return True

    print(f"[PUSHING] Pushing to GitHub ({remote}/{active_branch})...")
    try:
        push(root, remote, active_branch)
        print(f"\n[SUCCESS] Feature pushed to GitHub ({remote}/{active_branch}) successfully!")
        return True
    except GitError as e:
        print(f"\n[ERROR] Push failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        prog="auto-push",
        description="Professional Multi-Language & Multi-Framework Git and GitHub automation.",
    )
    parser.add_argument(
        "-m", "--message",
        type=str,
        default=None,
        help="Custom commit message (if omitted, conventional semantic message is generated).",
    )
    parser.add_argument(
        "-w", "--watch",
        action="store_true",
        help="Enable Feature-Watcher mode: monitors files and auto-pushes when features are completed.",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=8.0,
        help="Feature completion settlement window in seconds for watch mode (default: 8.0s).",
    )
    parser.add_argument(
        "-b", "--branch",
        type=str,
        default=None,
        help="Target git branch (default: active branch).",
    )
    parser.add_argument(
        "-r", "--remote",
        type=str,
        default="origin",
        help="Git remote name (default: 'origin').",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Interactive GitHub repository setup / change remote URL.",
    )
    parser.add_argument(
        "--detect",
        action="store_true",
        help="Inspect detected language, framework, ecosystem, and build tools for this project.",
    )
    parser.add_argument(
        "--init-gitignore",
        action="store_true",
        help="Generate or reset a framework-tailored .gitignore file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate actions without staging, committing, or pushing.",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Autopush v{__version__}",
    )

    args = parser.parse_args()
    root = Path.cwd()

    banner()

    # --detect command
    if args.detect:
        stack = StackDetector.detect(root)
        print("=" * 50)
        print(" PROJECT STACK INSPECTION")
        print("=" * 50)
        print(f"Language   : {stack.language}")
        print(f"Framework  : {stack.framework or 'None / Standard'}")
        print(f"Ecosystem  : {stack.ecosystem}")
        print(f"Build Tool : {stack.build_tool or 'None detected'}")
        print(f"Git Repo   : {'Yes' if is_git_repo(root) else 'No (run auto-push to initialize)'}")
        remotes = get_remotes(root) if is_git_repo(root) else {}
        print(f"Remotes    : {remotes or 'None'}")
        return

    # --init-gitignore command
    if args.init_gitignore:
        stack = StackDetector.detect(root)
        ensure_gitignore(root, stack, interactive=False)
        return

    # --setup command
    if args.setup:
        ensure_repo_ready(root, interactive=False)
        setup_remote_interactive(root)
        return

    # --watch mode
    if args.watch:
        stack = StackDetector.detect(root)
        ensure_repo_ready(root, interactive=True)
        ensure_gitignore(root, stack, interactive=True)

        def on_feature_complete(changes):
            run_single_sync(
                root=root,
                message=args.message,
                branch=args.branch,
                remote=args.remote,
                dry_run=args.dry_run,
                interactive=False,
            )

        watcher = FeatureWatcher(
            root=root,
            stack=stack,
            on_feature_complete=on_feature_complete,
            settle_window_sec=args.cooldown,
        )
        watcher.start()
        return

    # Default: One-command sync
    success = run_single_sync(
        root=root,
        message=args.message,
        branch=args.branch,
        remote=args.remote,
        dry_run=args.dry_run,
        interactive=True,
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
