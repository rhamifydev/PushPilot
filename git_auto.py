#!/usr/bin/env python3
"""
Git Automation Utility (git_auto.py)
Automates git add, commit, and push operations with smart commit messages,
one-shot CLI triggers, and continuous watch/auto-sync modes.
"""

import argparse
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path


# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# Terminal Colors for console output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def log_info(msg: str):
    print(f"{Colors.CYAN}[INFO]{Colors.RESET} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} {msg}")


def log_warn(msg: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")


def run_command(cmd: list[str], cwd: Path = Path.cwd()) -> tuple[int, str, str]:
    """Execute a system command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 1, "", f"Command '{cmd[0]}' not found in PATH."
    except Exception as e:
        return 1, "", str(e)


def is_git_installed() -> bool:
    """Verify Git is installed and accessible."""
    code, stdout, _ = run_command(["git", "--version"])
    return code == 0


def is_git_repo(repo_dir: Path) -> bool:
    """Check if current directory is inside a git repository."""
    code, stdout, _ = run_command(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo_dir)
    return code == 0 and stdout == "true"


def get_current_branch(repo_dir: Path) -> str:
    """Retrieve the current active branch name."""
    code, stdout, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)
    if code == 0 and stdout:
        return stdout
    # Fallback if no commits yet (initial repo)
    code, stdout, _ = run_command(["git", "symbolic-ref", "--short", "HEAD"], cwd=repo_dir)
    if code == 0 and stdout:
        return stdout
    return "main"


def get_remote_names(repo_dir: Path) -> list[str]:
    """Return configured remote names (e.g., ['origin'])."""
    code, stdout, _ = run_command(["git", "remote"], cwd=repo_dir)
    if code == 0 and stdout:
        return [r.strip() for r in stdout.splitlines() if r.strip()]
    return []


def get_changed_files(repo_dir: Path) -> list[tuple[str, str]]:
    """Return a list of (status_code, filename) from git status --porcelain."""
    code, stdout, _ = run_command(["git", "status", "--porcelain"], cwd=repo_dir)
    if code != 0 or not stdout:
        return []

    changes = []
    for line in stdout.splitlines():
        if len(line) >= 4:
            status = line[:2].strip()
            filename = line[3:].strip().strip('"')
            changes.append((status, filename))
    return changes


def generate_smart_message(changes: list[tuple[str, str]]) -> str:
    """Generate a clean, descriptive commit message based on changed files."""
    if not changes:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"Auto-update: sync repository [{now}]"

    modified = [f for s, f in changes if "M" in s]
    added = [f for s, f in changes if "?" in s or "A" in s]
    deleted = [f for s, f in changes if "D" in s]

    parts = []
    if added:
        names = ", ".join(Path(f).name for f in added[:3])
        more = f" (+{len(added) - 3} more)" if len(added) > 3 else ""
        parts.append(f"Add {names}{more}")
    if modified:
        names = ", ".join(Path(f).name for f in modified[:3])
        more = f" (+{len(modified) - 3} more)" if len(modified) > 3 else ""
        parts.append(f"Update {names}{more}")
    if deleted:
        names = ", ".join(Path(f).name for f in deleted[:3])
        more = f" (+{len(deleted) - 3} more)" if len(deleted) > 3 else ""
        parts.append(f"Remove {names}{more}")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = " & ".join(parts) if parts else "Repository files updated"
    return f"{summary} [{timestamp}]"


def auto_push_commit(
    repo_dir: Path,
    message: str | None = None,
    branch: str | None = None,
    remote: str = "origin",
    pull_first: bool = False,
    dry_run: bool = False,
) -> bool:
    """Perform git add, commit, and push."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}=== Git Auto Commit & Push ==={Colors.RESET}")
    log_info(f"Working Directory: {repo_dir}")

    if not is_git_repo(repo_dir):
        log_error(f"'{repo_dir}' is not a git repository! Run 'git init' or pass --init.")
        return False

    current_branch = branch or get_current_branch(repo_dir)
    remotes = get_remote_names(repo_dir)

    log_info(f"Active Branch: {Colors.BOLD}{current_branch}{Colors.RESET}")
    log_info(f"Target Remote: {Colors.BOLD}{remote}{Colors.RESET} ({', '.join(remotes) if remotes else 'No remotes configured'})")

    # Check for changes
    changes = get_changed_files(repo_dir)
    if not changes:
        log_warn("No working tree changes detected (working tree clean).")
        # Check if there are unpushed commits
        code, stdout, _ = run_command(["git", "log", f"{remote}/{current_branch}..{current_branch}"], cwd=repo_dir)
        if code != 0 or not stdout:
            log_info("Nothing to commit or push.")
            return True
        log_info("Local commits exist that have not yet been pushed to remote.")
    else:
        log_info(f"Detected {len(changes)} changed file(s):")
        for status, file in changes[:10]:
            print(f"   {Colors.YELLOW}[{status or '?' }]{Colors.RESET} {file}")
        if len(changes) > 10:
            print(f"   ... and {len(changes) - 10} more file(s)")

    # Pull latest changes if requested
    if pull_first and remote in remotes:
        log_info(f"Pulling latest changes from {remote}/{current_branch} (rebase)...")
        if dry_run:
            log_info("[DRY RUN] Would execute: git pull --rebase")
        else:
            code, stdout, stderr = run_command(["git", "pull", "--rebase", remote, current_branch], cwd=repo_dir)
            if code != 0:
                log_error(f"Git pull failed: {stderr or stdout}")
                return False
            log_success("Pull completed.")

    # Stage files
    if changes:
        log_info("Staging all changes ('git add -A')...")
        if dry_run:
            log_info("[DRY RUN] Would execute: git add -A")
        else:
            code, stdout, stderr = run_command(["git", "add", "-A"], cwd=repo_dir)
            if code != 0:
                log_error(f"Failed to stage files: {stderr or stdout}")
                return False

        # Prepare commit message
        commit_msg = message.strip() if message and message.strip() else generate_smart_message(changes)
        log_info(f"Commit message: \"{Colors.BOLD}{commit_msg}{Colors.RESET}\"")

        if dry_run:
            log_info(f"[DRY RUN] Would execute: git commit -m \"{commit_msg}\"")
        else:
            code, stdout, stderr = run_command(["git", "commit", "-m", commit_msg], cwd=repo_dir)
            if code != 0:
                log_error(f"Git commit failed: {stderr or stdout}")
                return False
            log_success("Changes committed successfully.")

    # Push to remote
    if remote not in remotes:
        log_warn(f"Remote '{remote}' is not configured. Skipping push.")
        log_info("To link a remote GitHub repository, run:")
        log_info("  git remote add origin https://github.com/<username>/<repo>.git")
        return True

    log_info(f"Pushing to {remote}/{current_branch}...")
    if dry_run:
        log_info(f"[DRY RUN] Would execute: git push -u {remote} {current_branch}")
        return True

    # Attempt push with upstream tracking
    code, stdout, stderr = run_command(["git", "push", "-u", remote, current_branch], cwd=repo_dir)
    if code == 0:
        log_success(f"Successfully pushed to {remote}/{current_branch}!")
        return True

    # If push failed, print error details
    err_msg = stderr or stdout
    log_error(f"Push failed:\n{err_msg}")
    if "set-upstream" in err_msg or "upstream" in err_msg:
        log_info("Retrying with explicit upstream flag...")
        code, stdout, stderr = run_command(["git", "push", "--set-upstream", remote, current_branch], cwd=repo_dir)
        if code == 0:
            log_success(f"Successfully pushed to {remote}/{current_branch}!")
            return True

    return False


def watch_mode(
    repo_dir: Path,
    interval: int = 30,
    message: str | None = None,
    branch: str | None = None,
    remote: str = "origin",
    pull_first: bool = False,
):
    """Periodically check for changes and auto-commit & push."""
    print(f"{Colors.BOLD}{Colors.HEADER}=== Starting Auto-Sync Watch Mode ==={Colors.RESET}")
    log_info(f"Watching '{repo_dir}' every {interval}s. Press Ctrl+C to stop.")

    try:
        while True:
            changes = get_changed_files(repo_dir)
            if changes:
                print("\n" + "-" * 50)
                log_info(f"Changes detected at {datetime.datetime.now().strftime('%H:%M:%S')}! Syncing...")
                auto_push_commit(
                    repo_dir=repo_dir,
                    message=message,
                    branch=branch,
                    remote=remote,
                    pull_first=pull_first,
                )
                log_info(f"Waiting {interval}s before next check...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Watch mode stopped by user.{Colors.RESET}")


def init_repo(repo_dir: Path, remote_url: str | None = None):
    """Helper to initialize git repository and configure remote."""
    if is_git_repo(repo_dir):
        log_info(f"'{repo_dir}' is already a git repository.")
    else:
        code, stdout, stderr = run_command(["git", "init"], cwd=repo_dir)
        if code == 0:
            log_success(f"Initialized empty Git repository in {repo_dir}")
        else:
            log_error(f"Failed to init git repository: {stderr or stdout}")
            return

    if remote_url:
        remotes = get_remote_names(repo_dir)
        if "origin" in remotes:
            run_command(["git", "remote", "set-url", "origin", remote_url], cwd=repo_dir)
            log_success(f"Updated remote 'origin' URL to: {remote_url}")
        else:
            run_command(["git", "remote", "add", "origin", remote_url], cwd=repo_dir)
            log_success(f"Added remote 'origin': {remote_url}")


def main():
    parser = argparse.ArgumentParser(
        description="Automate git add, commit, and push in Python with smart commit messages and auto-sync watch mode."
    )
    parser.add_argument(
        "-m", "--message",
        type=str,
        default=None,
        help="Custom commit message (if omitted, a smart summary with timestamp is generated).",
    )
    parser.add_argument(
        "-b", "--branch",
        type=str,
        default=None,
        help="Git branch name (default: current active branch).",
    )
    parser.add_argument(
        "-r", "--remote",
        type=str,
        default="origin",
        help="Git remote name (default: 'origin').",
    )
    parser.add_argument(
        "-p", "--pull-first",
        action="store_true",
        help="Pull remote changes before pushing (git pull --rebase).",
    )
    parser.add_argument(
        "-w", "--watch",
        action="store_true",
        help="Enable watch mode: continuously monitor and auto-push changes.",
    )
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=30,
        help="Interval in seconds for watch mode (default: 30).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate actions without staging, committing, or pushing.",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize git repo in current directory if not already initialized.",
    )
    parser.add_argument(
        "--set-remote",
        type=str,
        default=None,
        help="Set or update git remote 'origin' URL (e.g., https://github.com/user/repo.git).",
    )

    args = parser.parse_args()

    if not is_git_installed():
        log_error("Git is not found in your system PATH. Please install Git first.")
        sys.exit(1)

    repo_dir = Path.cwd()

    if args.init or args.set_remote:
        init_repo(repo_dir, args.set_remote)
        if not args.watch and not args.message:
            return

    if args.watch:
        watch_mode(
            repo_dir=repo_dir,
            interval=args.interval,
            message=args.message,
            branch=args.branch,
            remote=args.remote,
            pull_first=args.pull_first,
        )
    else:
        success = auto_push_commit(
            repo_dir=repo_dir,
            message=args.message,
            branch=args.branch,
            remote=args.remote,
            pull_first=args.pull_first,
            dry_run=args.dry_run,
        )
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
