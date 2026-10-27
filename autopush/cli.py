"""
PushPilot Command-Line Interface.
Professional multi-language & multi-framework Git & GitHub automation.
"""

import argparse
import sys
import time
from pathlib import Path

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from autopush import __version__, ui
from autopush.commit_gen import generate_commit_message
from autopush.detector import StackDetector
from autopush.git_ops import (
    GitError,
    commit,
    ensure_gitignore,
    ensure_repo_ready,
    get_current_branch,
    get_git_diff_summary,
    get_git_status_changes,
    get_remotes,
    get_upstream_branch,
    has_unpushed_commits,
    is_git_repo,
    push,
    resolve_target_branch,
    setup_remote_interactive,
    stage_all,
)
from autopush.watcher import FeatureWatcher


def run_single_sync(
    root: Path,
    repo_url: str | None = None,
    message: str | None = None,
    branch: str | None = None,
    remote: str = "origin",
    dry_run: bool = False,
    interactive: bool = True,
    allow_ai: bool = True,
) -> bool:
    """Performs a full automated check, stage, commit, and push cycle."""
    start_time = time.time()

    # Disable interactive prompts if dry_run or stdin is not a terminal
    if dry_run or not sys.stdin.isatty():
        interactive = False

    # 1. Detect Stack
    stack = StackDetector.detect(root)
    framework_label = stack.framework or "Standard"
    ui.badge(
        "STACK",
        f"{stack.language} ({framework_label})",
        subtitle=f"Ecosystem: {stack.ecosystem}",
        color=ui.Style.BRIGHT_CYAN,
    )

    # 2. Ensure Git & Remote Setup
    ready, remote_was_just_linked = ensure_repo_ready(root, repo_url=repo_url, interactive=interactive)

    # 3. Ensure .gitignore
    ensure_gitignore(root, stack, interactive=interactive)

    # 4. Resolve Target Branch (community/group branch, upstream tracking, or active local branch)
    active_branch, branch_source = resolve_target_branch(root, user_branch=branch)
    remotes = get_remotes(root)

    ui.badge("BRANCH", active_branch, subtitle=branch_source, color=ui.Style.BRIGHT_GREEN)

    if remote in remotes:
        ui.badge("REMOTE", f"{remote} → {remotes[remote]}", color=ui.Style.BRIGHT_BLUE)
    else:
        ui.warn(f"Remote '{remote}' is not configured.")

    # 5. Check Changes
    changes = get_git_status_changes(root)
    if not changes:
        if remote in remotes and (remote_was_just_linked or has_unpushed_commits(root, remote, active_branch)):
            ui.info("Working tree clean, but unpushed commits exist. Pushing to GitHub...")
            if not dry_run:
                try:
                    push(root, remote, active_branch)
                    elapsed = f"{time.time() - start_time:.1f}s"
                    ui.success(f"Pushed all commits to GitHub ({remote}/{active_branch}) in {elapsed}!")
                except GitError as e:
                    ui.error(f"Push failed: {e}")
                    return False
            else:
                ui.dry_run_badge(f"Would push unpushed commits to {remote}/{active_branch}")
            return True
        else:
            ui.info("Working tree clean and up to date with remote. Nothing to push.")
            return True

    ui.badge("CHANGES", f"{len(changes)} file(s) modified/staged", color=ui.Style.BRIGHT_YELLOW)
    for status, file_path in changes[:8]:
        print(ui.format_change_item(status, file_path))
    if len(changes) > 8:
        print(f"   ... and {len(changes) - 8} more file(s)")

    # 6. Generate Commit Message
    diff_summary = get_git_diff_summary(root)
    commit_msg, ai_source = generate_commit_message(
        changes,
        stack,
        custom_msg=message,
        root=root,
        diff_summary=diff_summary,
        allow_ai=allow_ai,
    )
    if ai_source:
        ui.badge("AI COMMIT", f'"{commit_msg}"', subtitle=f"Source: {ai_source}", color=ui.Style.BRIGHT_MAGENTA)
    else:
        ui.badge("COMMIT", f'"{commit_msg}"', color=ui.Style.BRIGHT_WHITE)

    if dry_run:
        ui.dry_run_badge("Would stage all files ('git add -A')")
        ui.dry_run_badge(f'Would commit with message: "{commit_msg}"')
        if remote in remotes:
            ui.dry_run_badge(f"Would push to {remote}/{active_branch}")
        return True

    # 7. Stage & Commit
    ui.info("Staging all files ('git add -A')...")
    stage_all(root)

    ui.info("Committing changes...")
    commit(root, commit_msg)
    ui.success("Changes committed locally.")

    # 8. Push to Remote
    remotes = get_remotes(root)
    if remote not in remotes:
        ui.warn(f"Remote '{remote}' not linked yet.")
        if interactive:
            new_remote = setup_remote_interactive(root)
            if not new_remote:
                ui.info("Commit saved locally. Link a remote when you are ready to push.")
                return True
        else:
            ui.warn(f"Remote '{remote}' not configured. Run 'pushpilot <repo-url>' to link a GitHub repo.")
            return True

    ui.badge("PUSHING", f"Pushing to GitHub ({remote}/{active_branch})...", color=ui.Style.BRIGHT_CYAN)
    try:
        push(root, remote, active_branch)
        elapsed = f"{time.time() - start_time:.1f}s"
        ui.success(f"Feature pushed to GitHub ({remote}/{active_branch}) in {elapsed}!")
        return True
    except GitError as e:
        ui.error(f"Push failed:\n{e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        prog="pushpilot",
        description="PushPilot - Intelligent Multi-Framework Git & GitHub Autopilot.",
    )
    parser.add_argument(
        "repo_url",
        nargs="?",
        default=None,
        help="Optional GitHub repository URL (e.g. https://github.com/user/repo.git). Automatically initializes git and links remote.",
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
        help="Target git branch (default: active/upstream branch, or 'main' for new repos).",
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
        "--no-ai",
        action="store_true",
        help="Disable AI commit message generation and force default rule-based message.",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Explicitly enable AI commit message generation (auto-detected by default).",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"PushPilot v{__version__}",
    )

    args = parser.parse_args()
    root = Path.cwd()
    allow_ai = not args.no_ai

    ui.banner(__version__)

    # --detect command
    if args.detect:
        stack = StackDetector.detect(root)
        active_b, b_src = resolve_target_branch(root, user_branch=args.branch) if is_git_repo(root) else ("None", "N/A")
        print(f"{ui.Style.BRIGHT_CYAN}{ui.Style.BOLD}╭── PROJECT STACK INSPECTION ────────────────────────────────╮{ui.Style.RESET}")
        print(f"  {ui.Style.BOLD}Language   :{ui.Style.RESET} {stack.language}")
        print(f"  {ui.Style.BOLD}Framework  :{ui.Style.RESET} {stack.framework or 'None / Standard'}")
        print(f"  {ui.Style.BOLD}Ecosystem  :{ui.Style.RESET} {stack.ecosystem}")
        print(f"  {ui.Style.BOLD}Build Tool :{ui.Style.RESET} {stack.build_tool or 'None detected'}")
        print(f"  {ui.Style.BOLD}Git Branch :{ui.Style.RESET} {active_b} ({b_src})")
        print(f"  {ui.Style.BOLD}Git Repo   :{ui.Style.RESET} {'Yes' if is_git_repo(root) else 'No (run pushpilot to initialize)'}")
        remotes = get_remotes(root) if is_git_repo(root) else {}
        print(f"  {ui.Style.BOLD}Remotes    :{ui.Style.RESET} {remotes or 'None'}")
        print(f"{ui.Style.BRIGHT_CYAN}╰────────────────────────────────────────────────────────────╯{ui.Style.RESET}")
        return

    # --init-gitignore command
    if args.init_gitignore:
        stack = StackDetector.detect(root)
        ensure_gitignore(root, stack, interactive=False)
        return

    # --setup command
    if args.setup:
        ensure_repo_ready(root, repo_url=args.repo_url, interactive=False)
        setup_remote_interactive(root)
        return

    # --watch mode
    if args.watch:
        stack = StackDetector.detect(root)
        ensure_repo_ready(root, repo_url=args.repo_url, interactive=True)
        ensure_gitignore(root, stack, interactive=True)

        def on_feature_complete(changes):
            run_single_sync(
                root=root,
                repo_url=args.repo_url,
                message=args.message,
                branch=args.branch,
                remote=args.remote,
                dry_run=args.dry_run,
                interactive=False,
                allow_ai=allow_ai,
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
        repo_url=args.repo_url,
        message=args.message,
        branch=args.branch,
        remote=args.remote,
        dry_run=args.dry_run,
        interactive=True,
        allow_ai=allow_ai,
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
