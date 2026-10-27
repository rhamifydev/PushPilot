"""
Feature-Completion File Watcher for Autopush.
Monitors directory for changes with a debounced settlement timer.
When the developer finishes coding a feature, it automatically stages,
commits with a semantic message, and pushes to GitHub.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from autopush import ui
from autopush.detector import ProjectStack
from autopush.git_ops import get_git_status_changes


# Folders and extensions to ignore during file watching
IGNORED_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "vendor", "target", "build",
    "dist", ".next", ".nuxt", ".svelte-kit", "__pycache__", ".venv",
    "venv", "env", ".idea", ".vscode", ".turbo", ".gradle", "bin", "obj",
    "coverage", ".pytest_cache", ".dart_tool"
}

IGNORED_EXTS = {
    ".tmp", ".swp", ".bak", ".log", ".pyc", ".pyo", ".class", ".exe",
    ".dll", ".so", ".dylib", ".DS_Store"
}


def should_ignore(path: Path) -> bool:
    """Returns True if file/directory should be ignored."""
    for part in path.parts:
        if part in IGNORED_DIRS or part.startswith(".git"):
            return True
    if path.suffix.lower() in IGNORED_EXTS:
        return True
    if path.name.startswith("~") or path.name.endswith("~"):
        return True
    return False


def get_tree_fingerprint(root: Path) -> dict[str, float]:
    """Scans relevant source files and records modification timestamps."""
    fingerprint = {}
    try:
        for entry in root.rglob("*"):
            if entry.is_file():
                try:
                    rel = entry.relative_to(root)
                    if not should_ignore(rel):
                        fingerprint[str(rel)] = entry.stat().st_mtime
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass
    return fingerprint


class FeatureWatcher:
    """Watches the project filesystem and triggers push when a feature is complete."""

    def __init__(
        self,
        root: Path,
        stack: ProjectStack,
        on_feature_complete: Callable[[list[tuple[str, str]]], None],
        settle_window_sec: float = 8.0,
        poll_interval_sec: float = 1.5,
    ):
        self.root = root
        self.stack = stack
        self.on_feature_complete = on_feature_complete
        self.settle_window = settle_window_sec
        self.poll_interval = poll_interval_sec
        self.last_snapshot = get_tree_fingerprint(root)
        self.changed_batch: set[str] = set()
        self.last_activity_time: float | None = None

    def start(self):
        """Runs the monitoring loop."""
        print(f"{ui.Style.BRIGHT_CYAN}{ui.Style.BOLD}╭── FEATURE-DRIVEN AUTO-PUSH WATCHER ────────────────────────╮{ui.Style.RESET}")
        print(f"  {ui.Style.BOLD}Stack Detected  :{ui.Style.RESET} {self.stack.language} ({self.stack.framework or 'General'})")
        print(f"  {ui.Style.BOLD}Watch Directory :{ui.Style.RESET} {self.root}")
        print(f"  {ui.Style.BOLD}Cooldown Window :{ui.Style.RESET} {self.settle_window}s feature settlement")
        print(f"  {ui.Style.BOLD}Status          :{ui.Style.RESET} {ui.Style.BRIGHT_GREEN}● Watching for changes{ui.Style.RESET} (Press Ctrl+C to stop)")
        print(f"{ui.Style.BRIGHT_CYAN}╰────────────────────────────────────────────────────────────╯{ui.Style.RESET}\n")

        try:
            while True:
                current_snapshot = get_tree_fingerprint(self.root)
                now = time.time()

                # Detect modified, added, or deleted files
                current_keys = set(current_snapshot.keys())
                last_keys = set(self.last_snapshot.keys())

                new_files = current_keys - last_keys
                deleted_files = last_keys - current_keys
                modified_files = {
                    k for k in (current_keys & last_keys)
                    if current_snapshot[k] != self.last_snapshot[k]
                }

                diff = new_files | deleted_files | modified_files
                if diff:
                    self.changed_batch.update(diff)
                    self.last_activity_time = now
                    self.last_snapshot = current_snapshot

                    sample_names = ", ".join(Path(f).name for f in list(self.changed_batch)[:3])
                    more = f" (+{len(self.changed_batch) - 3} more)" if len(self.changed_batch) > 3 else ""
                    print(
                        f"\r{ui.Style.BRIGHT_YELLOW}⚡ EDITING{ui.Style.RESET} {len(self.changed_batch)} file(s) active: {sample_names}{more} ... waiting for edits to settle   ",
                        end="",
                        flush=True,
                    )

                # Check if user paused editing (feature settlement window reached)
                if self.last_activity_time is not None:
                    elapsed = now - self.last_activity_time
                    remaining = self.settle_window - elapsed

                    if remaining > 0 and self.changed_batch:
                        # Still counting down
                        print(
                            f"\r{ui.Style.BRIGHT_CYAN}⏳ SETTLING{ui.Style.RESET} Feature completion countdown: {ui.Style.BOLD}{int(remaining) + 1}s{ui.Style.RESET} remaining...   ",
                            end="",
                            flush=True,
                        )
                    elif remaining <= 0 and self.changed_batch:
                        # Feature settlement window passed! Trigger auto commit & push
                        ts = datetime.now().strftime("%H:%M:%S")
                        print(f"\n\n{ui.Style.BRIGHT_MAGENTA}{ui.Style.BOLD}✨ FEATURE COMPLETE{ui.Style.RESET} Activity settled at {ts}. Starting auto-push...\n")

                        # Verify actual git status changes
                        git_changes = get_git_status_changes(self.root)
                        if git_changes:
                            try:
                                self.on_feature_complete(git_changes)
                            except Exception as e:
                                ui.error(f"Auto-push failed: {e}")
                        else:
                            ui.info("Working tree clean (no git changes staged or untracked).")

                        # Reset batch and update snapshot
                        self.changed_batch.clear()
                        self.last_activity_time = None
                        self.last_snapshot = get_tree_fingerprint(self.root)
                        print(f"\n{ui.Style.BRIGHT_GREEN}● Resuming watch mode for next feature...{ui.Style.RESET}\n")

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print(f"\n\n{ui.Style.BRIGHT_BLUE}ℹ PushPilot watcher stopped by user.{ui.Style.RESET}")
