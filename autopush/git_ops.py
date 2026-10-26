"""
Git Operations Layer for Autopush.
Handles repository status, remote configuration, branch management,
staging, committing, and upstream pushing.
"""

import re
import subprocess
import sys
from pathlib import Path
from autopush.detector import ProjectStack, StackDetector


class GitError(Exception):
    pass


def run_git(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    """Execute git command and return (code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["git"] + cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        raise GitError("Git is not installed or not in PATH.")
    except Exception as e:
        raise GitError(str(e))


def is_git_repo(root: Path) -> bool:
    code, stdout, _ = run_git(["rev-parse", "--is-inside-work-tree"], cwd=root)
    return code == 0 and stdout == "true"


def get_current_branch(root: Path) -> str:
    code, stdout, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    if code == 0 and stdout and stdout != "HEAD":
        return stdout
    code, stdout, _ = run_git(["symbolic-ref", "--short", "HEAD"], cwd=root)
    if code == 0 and stdout:
        return stdout
    return "main"


def get_remotes(root: Path) -> dict[str, str]:
    """Returns mapping of remote name -> fetch URL."""
    code, stdout, _ = run_git(["remote", "-v"], cwd=root)
    if code != 0 or not stdout:
        return {}
    remotes = {}
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and "(fetch)" in line:
            remotes[parts[0]] = parts[1]
    return remotes


def ensure_gitignore(root: Path, stack: ProjectStack, interactive: bool = True) -> bool:
    """Checks if .gitignore exists. If missing, creates a framework-tailored .gitignore."""
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        return True

    print(f"\n[NOTICE] No .gitignore found in this {stack.language} ({stack.framework or 'project'}) repository.")
    content = StackDetector.get_recommended_gitignore(stack)
    try:
        gitignore_path.write_text(content, encoding="utf-8")
        print(f"[OK] Generated framework-specific .gitignore for {stack.language} ({stack.framework or 'General'}).")
        return True
    except Exception as e:
        print(f"[WARNING] Could not create .gitignore: {e}")
        return False


def setup_remote_interactive(root: Path) -> str | None:
    """Prompts user to link a GitHub repository if none is configured."""
    print("\n" + "=" * 60)
    print(" GITHUB REPOSITORY SETUP")
    print("=" * 60)
    print("No GitHub remote repository is currently linked to this project.")
    print("To auto-push, enter your GitHub repository URL.")
    print("Examples:")
    print("  - HTTPS: https://github.com/username/my-repo.git")
    print("  - SSH:   git@github.com:username/my-repo.git\n")

    try:
        repo_url = input("Enter GitHub repository URL (or press Enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if not repo_url:
        print("[INFO] Skipped remote setup.")
        return None

    # Clean URL
    repo_url = repo_url.strip("'\"")

    # Add remote
    code, _, stderr = run_git(["remote", "add", "origin", repo_url], cwd=root)
    if code == 0:
        print(f"[OK] Linked remote 'origin': {repo_url}")
        # Standardize default branch to main if in initial state
        run_git(["branch", "-M", "main"], cwd=root)
        return repo_url
    else:
        # Check if origin already existed and update it
        run_git(["remote", "set-url", "origin", repo_url], cwd=root)
        print(f"[OK] Updated remote 'origin': {repo_url}")
        return repo_url


def ensure_repo_ready(root: Path, repo_url: str | None = None, interactive: bool = True) -> tuple[bool, bool]:
    """Ensures git is initialized and ready.
    Returns (is_ready, remote_was_just_linked).
    """
    if not is_git_repo(root):
        print(f"[INFO] Initializing new Git repository in: {root}")
        code, stdout, stderr = run_git(["init"], cwd=root)
        if code != 0:
            raise GitError(f"Failed to initialize git repository: {stderr}")
        run_git(["branch", "-M", "main"], cwd=root)
        print("[OK] Git repository initialized with default branch 'main'.")

    remotes = get_remotes(root)
    remote_was_just_linked = False

    if repo_url and repo_url.strip():
        clean_url = repo_url.strip().strip("'\"")
        if "origin" in remotes:
            run_git(["remote", "set-url", "origin", clean_url], cwd=root)
            print(f"[OK] Updated remote 'origin': {clean_url}")
        else:
            code, _, stderr = run_git(["remote", "add", "origin", clean_url], cwd=root)
            if code != 0:
                run_git(["remote", "set-url", "origin", clean_url], cwd=root)
            print(f"[OK] Linked remote 'origin': {clean_url}")
        run_git(["branch", "-M", "main"], cwd=root)
        remote_was_just_linked = True
    elif "origin" not in remotes and interactive:
        linked_url = setup_remote_interactive(root)
        if linked_url:
            remote_was_just_linked = True

    return True, remote_was_just_linked


def get_git_status_changes(root: Path) -> list[tuple[str, str]]:
    """Returns list of (status, filename) from git status --porcelain."""
    code, stdout, stderr = run_git(["status", "--porcelain"], cwd=root)
    if code != 0 or not stdout:
        return []

    changes = []
    for line in stdout.splitlines():
        if len(line) >= 3:
            status = line[:2].strip()
            filename = line[2:].strip().strip('"')
            if filename:
                changes.append((status, filename))
    return changes


def get_git_diff_summary(root: Path, max_chars: int = 3500) -> str:
    """Returns a concise diff summary of staged, unstaged, and untracked changes."""
    _, diff_unstaged, _ = run_git(["diff", "--no-color"], cwd=root)
    _, diff_staged, _ = run_git(["diff", "--cached", "--no-color"], cwd=root)
    _, status_out, _ = run_git(["status", "--short"], cwd=root)

    combined = []
    if status_out:
        combined.append(f"Changed files:\n{status_out.strip()}\n")
    if diff_staged:
        combined.append(f"Staged changes:\n{diff_staged.strip()}\n")
    if diff_unstaged:
        combined.append(f"Working tree changes:\n{diff_unstaged.strip()}\n")

    full_text = "\n".join(combined)
    if len(full_text) > max_chars:
        return full_text[:max_chars] + "\n... [diff truncated]"
    return full_text


def has_unpushed_commits(root: Path, remote: str = "origin", branch: str = "main") -> bool:
    """Check if local commits exist that are not on remote."""
    # 1. Does local branch have any commits?
    code, head_commit, _ = run_git(["rev-parse", "HEAD"], cwd=root)
    if code != 0 or not head_commit:
        return False  # No commits in repository

    # 2. Check if remote tracking branch exists locally
    code, remote_commit, _ = run_git(["rev-parse", "--verify", f"{remote}/{branch}"], cwd=root)
    if code != 0:
        # Remote tracking branch does not exist locally (branch never pushed/fetched)
        return True

    # 3. If remote tracking branch exists, check if local is ahead
    code, stdout, _ = run_git(["log", f"{remote}/{branch}..{branch}"], cwd=root)
    return code == 0 and bool(stdout.strip())


def stage_all(root: Path) -> None:
    code, _, stderr = run_git(["add", "-A"], cwd=root)
    if code != 0:
        raise GitError(f"Failed to stage changes: {stderr}")


def commit(root: Path, message: str) -> None:
    code, stdout, stderr = run_git(["commit", "-m", message], cwd=root)
    if code != 0:
        raise GitError(f"Failed to commit: {stderr or stdout}")


def pull_rebase(root: Path, remote: str, branch: str) -> bool:
    # Attempt 1: Standard pull rebase with autostash
    code, stdout, stderr = run_git(["pull", "--rebase", "--autostash", remote, branch], cwd=root)
    if code == 0:
        return True

    # Clean up any paused rebase attempt
    run_git(["rebase", "--abort"], cwd=root)

    # Attempt 2: Pull rebase preferring local project files on conflict (-X ours)
    # This automatically resolves conflicts when GitHub initialized a default README or .gitignore
    code, stdout, stderr = run_git(["pull", "--rebase", "-X", "ours", remote, branch], cwd=root)
    if code == 0:
        return True

    # If still stuck, abort cleanly so user's work tree is preserved
    run_git(["rebase", "--abort"], cwd=root)
    return False


def push(root: Path, remote: str = "origin", branch: str = "main") -> bool:
    """Push local branch to remote with upstream tracking."""
    # First attempt: git push -u remote branch
    code, stdout, stderr = run_git(["push", "-u", remote, branch], cwd=root)
    if code == 0:
        return True

    err = (stderr or stdout).lower()
    # If branch rejected because remote has commits not present locally:
    if "fetch first" in err or "non-fast-forward" in err or "rejected" in err:
        print("[INFO] Remote contains newer commits (e.g. GitHub initial commit). Syncing with local project...")
        if pull_rebase(root, remote, branch):
            code, stdout, stderr = run_git(["push", "-u", remote, branch], cwd=root)
            if code == 0:
                return True

    raise GitError(f"Git push failed:\n{stderr or stdout}")
