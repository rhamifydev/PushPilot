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


def ensure_repo_ready(root: Path, interactive: bool = True) -> bool:
    """Ensures git is initialized and ready."""
    if not is_git_repo(root):
        print(f"[INFO] Initializing new Git repository in: {root}")
        code, stdout, stderr = run_git(["init"], cwd=root)
        if code != 0:
            raise GitError(f"Failed to initialize git repository: {stderr}")
        # Set main as default branch
        run_git(["branch", "-M", "main"], cwd=root)
        print("[OK] Git repository initialized with branch 'main'.")

    remotes = get_remotes(root)
    if "origin" not in remotes and interactive:
        setup_remote_interactive(root)

    return True


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


def has_unpushed_commits(root: Path, remote: str = "origin", branch: str = "main") -> bool:
    """Check if local commits exist that are not on remote."""
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
    code, stdout, stderr = run_git(["pull", "--rebase", remote, branch], cwd=root)
    if code != 0:
        # Check if merge conflict occurred
        if "conflict" in (stderr + stdout).lower():
            raise GitError(f"Merge conflict detected during pull rebase:\n{stderr or stdout}")
        return False
    return True


def push(root: Path, remote: str = "origin", branch: str = "main") -> bool:
    """Push local branch to remote with upstream tracking."""
    # First attempt: git push -u remote branch
    code, stdout, stderr = run_git(["push", "-u", remote, branch], cwd=root)
    if code == 0:
        return True

    err = (stderr or stdout).lower()
    # If branch rejected because remote has commits not present locally:
    if "fetch first" in err or "non-fast-forward" in err:
        print("[INFO] Remote contains newer commits. Attempting automatic pull rebase before pushing...")
        if pull_rebase(root, remote, branch):
            code, stdout, stderr = run_git(["push", "-u", remote, branch], cwd=root)
            if code == 0:
                return True

    raise GitError(f"Git push failed:\n{stderr or stdout}")
