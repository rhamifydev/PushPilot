"""
Conventional Commit Message Generator.
Generates human-readable, semantic, and highly accurate commit messages:
1. If the developer is coding with AI (Google Antigravity, Cursor, Aider,
   Claude Code, Cline, or configured Gemini/OpenAI/Anthropic/Groq/Ollama APIs),
   it leverages the internal AI context and git diff to produce an ultra-accurate commit message.
2. If the developer is not coding with AI, it uses an advanced heuristic engine
   that inspects actual diff contents and component frequencies across changed files
   rather than static hardcoded templates.
"""

import re
from pathlib import Path
from typing import Optional

from autopush.detector import ProjectStack, classify_file_role


def extract_diff_context(diff_text: str) -> Optional[str]:
    """Inspects git diff text to extract specific UI terms, methods, or action keywords."""
    if not diff_text:
        return None

    # Check for specific commented or added UI elements
    match_ui = re.search(
        r'[-+]\s*<([A-Z][a-zA-Z0-9]+|strong|h[1-6]|button|div)[^>]*>([^<]{3,40})<',
        diff_text,
    )
    if match_ui:
        text = match_ui.group(2).strip().rstrip(":")
        text = re.sub(r"[^\w\s-]", "", text).strip()
        if 4 < len(text) < 35:
            return text.lower()

    # Check for function/method definitions
    match_func = re.search(r'[-+]\s*(?:public\s+function|const|function|def)\s+([a-zA-Z0-9_]+)', diff_text)
    if match_func:
        raw_func = match_func.group(1)
        # Split camelCase to readable words
        words = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', raw_func).replace('_', ' ').lower()
        words = re.sub(r'^(get\s+|set\s+|is\s+|has\s+)', '', words).strip()
        words = re.sub(r'(\s+attribute)$', '', words).strip()
        if words and words not in ('render', 'construct', 'handle', 'index', 'init', 'up', 'down'):
            return words

    return None


def generate_default_commit_message(
    changes: list[tuple[str, str]],
    stack: ProjectStack,
    diff_summary: Optional[str] = None,
) -> str:
    """
    Advanced heuristic conventional commit generator.
    Dynamically analyzes file roles, component dominance, and diff keywords.
    """
    if not changes:
        return f"chore: sync project updates [{stack.language}]"

    # 1. Analyze change classifications and count component occurrences
    role_counts: dict[str, int] = {}
    comp_counts: dict[str, int] = {}
    actions = {"add": 0, "modify": 0, "delete": 0}

    has_active_edits = any("M" in s or "A" in s or "?" in s for s, _ in changes)

    for status, file_path in changes:
        if "?" in status or "A" in status:
            actions["add"] += 1
        elif "D" in status:
            actions["delete"] += 1
        else:
            actions["modify"] += 1

        role, comp = classify_file_role(file_path)
        is_deleted = "D" in status
        if not (is_deleted and has_active_edits):
            role_counts[role] = role_counts.get(role, 0) + 1

        # Skip generic wrapper components and deleted files if active changes exist
        comp_clean = comp.lower().replace("layout", "").replace("index", "").strip()
        weight = 0 if (is_deleted and has_active_edits) else 1

        if weight > 0:
            if comp_clean and len(comp_clean) > 2:
                comp_counts[comp_clean] = comp_counts.get(comp_clean, 0) + 1
            elif comp:
                comp_counts[comp.lower()] = comp_counts.get(comp.lower(), 0) + 1

    # 2. Determine dominant scope
    if any("ai" in f.lower() or "commit" in f.lower() for _, f in changes):
        dominant_comp = "ai"
    elif comp_counts:
        dominant_comp = sorted(comp_counts.items(), key=lambda x: x[1], reverse=True)[0][0]
    else:
        dominant_comp = Path(changes[0][1]).stem.lower()

    # Clean up scope name
    scope = re.sub(r"[^\w-]", "", dominant_comp)[:16] or "core"

    # 3. Determine dominant role
    dominant_role = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[0][0] if role_counts else "core"

    # 4. Determine Conventional Commit Type (feat/fix/refactor/docs/chore/style)
    diff_lower = (diff_summary or "").lower()
    if dominant_role == "docs":
        c_type = "docs"
    elif dominant_role == "test":
        c_type = "test"
    elif dominant_role == "config":
        c_type = "chore(deps)" if any("package" in f or "req" in f or "composer" in f for _, f in changes) else "chore"
    elif "fix" in diff_lower or "bug" in diff_lower or "resolve" in diff_lower or "error" in diff_lower:
        c_type = f"fix({scope})"
    elif actions["add"] > actions["modify"]:
        c_type = f"feat({scope})"
    elif actions["delete"] > (actions["add"] + actions["modify"]):
        c_type = f"refactor({scope})"
    elif dominant_role == "style":
        c_type = f"style({scope})"
    else:
        c_type = f"feat({scope})" if actions["add"] > 0 else f"refactor({scope})"

    # 5. Extract specific diff details if available
    diff_hint = extract_diff_context(diff_summary or "")

    # 6. Construct natural subject
    stem_title = scope.replace("_", " ").replace("-", " ").title()

    if diff_hint:
        if scope.lower() in diff_hint.lower():
            subject = f"update {diff_hint}"
        else:
            subject = f"update {scope} {diff_hint}"
    elif dominant_role == "ui":
        if "layout" in [f.lower() for _, f in changes]:
            subject = f"refine {scope} layout and view components"
        else:
            subject = f"update {scope} view and interface components"
    elif dominant_role == "api":
        subject = f"update {scope} controller handlers and API logic"
    elif dominant_role == "model":
        subject = f"update data models and database schema for {scope}"
    elif dominant_role == "auth":
        subject = f"update authentication and user session controls"
    elif dominant_role == "style":
        subject = f"improve {scope} styling and visual presentation"
    elif dominant_role == "docs":
        subject = "update project documentation and guides"
    elif dominant_role == "config":
        subject = "update project configuration and dependencies"
    elif dominant_role == "test":
        subject = f"add/update test suite for {scope}"
    else:
        if actions["add"] > 0 and actions["modify"] == 0:
            subject = f"add new {scope} module"
        elif actions["delete"] > 0 and actions["add"] == 0:
            subject = f"clean up and remove {scope} resources"
        else:
            subject = f"update {scope} workflows and related features"

    # Context tag if framework is detected
    fw_tag = f" in {stack.framework}" if stack.framework and stack.framework != "Generic Project" else ""

    # Clean up formatted message
    message = f"{c_type}: {subject}{fw_tag}"
    return message


def generate_commit_message(
    changes: list[tuple[str, str]],
    stack: ProjectStack,
    custom_msg: Optional[str] = None,
    root: Optional[Path] = None,
    diff_summary: Optional[str] = None,
    allow_ai: bool = True,
) -> tuple[str, Optional[str]]:
    """
    Generates an accurate conventional commit message.
    1. Returns custom_msg directly if provided by user.
    2. If allow_ai is True, queries internal AI or active session context.
    3. Falls back to dynamic heuristic inspection of changed files and git diff.
    """
    if custom_msg and custom_msg.strip():
        return custom_msg.strip(), None

    if not changes:
        return f"chore: sync project updates [{stack.language}]", None

    # Check internal AI if enabled
    if allow_ai:
        try:
            from autopush.ai_commit import generate_ai_commit_message
            ai_msg, ai_source = generate_ai_commit_message(
                changes=changes,
                stack=stack,
                diff_summary=diff_summary or "",
                root=root or Path.cwd(),
            )
            if ai_msg:
                return ai_msg, ai_source
        except Exception:
            pass

    # Dynamic fallback based on actual file roles and diff contents
    default_msg = generate_default_commit_message(changes, stack, diff_summary=diff_summary)
    return default_msg, None
