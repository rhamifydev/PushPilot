"""
Example: Using git_auto programmatically inside your Python code.
"""

from pathlib import Path
from git_auto import auto_push_commit, is_git_repo, get_current_branch

# Path to the repository you want to manage
REPO_PATH = Path(__file__).parent

def sync_my_project():
    if not is_git_repo(REPO_PATH):
        print(f"Directory {REPO_PATH} is not a git repo.")
        return

    print(f"Current branch: {get_current_branch(REPO_PATH)}")

    # 1. Automatic smart commit message based on changed files
    success = auto_push_commit(
        repo_dir=REPO_PATH,
        message=None,          # Auto-generates summary (e.g. "Add file.py & Update app.py [2026-10-24 11:00]")
        remote="origin",       # Target remote
        pull_first=True,       # Pull latest changes before pushing (rebase)
        dry_run=False          # Set to True to test without making actual commits
    )

    if success:
        print("Project synchronized successfully!")
    else:
        print("Sync encountered an issue or nothing to push.")

if __name__ == "__main__":
    sync_my_project()
