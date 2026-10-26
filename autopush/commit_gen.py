"""
Conventional Commit Message Generator.
Generates human-readable, semantic, and professional commit messages:
1. If the developer is coding with AI (Google Antigravity, Cursor, Aider,
   Claude Code, Cline, or configured Gemini/OpenAI/Anthropic/Groq/Ollama APIs),
   it leverages the internal AI context to produce an ultra-accurate commit message.
2. If the developer is not coding with AI, it automatically falls back to the
   default rule-based heuristic generator.
"""

from pathlib import Path
from typing import Optional

from autopush.detector import ProjectStack, classify_file_role


def generate_default_commit_message(
    changes: list[tuple[str, str]],
    stack: ProjectStack,
) -> str:
    """Default rule-based conventional commit generator (used when not coding with AI)."""
    if not changes:
        return f"chore: sync project updates [{stack.language}]"

    # Analyze change classifications
    roles: dict[str, list[str]] = {}
    actions = {"add": 0, "modify": 0, "delete": 0}

    for status, file_path in changes:
        if "?" in status or "A" in status:
            actions["add"] += 1
        elif "D" in status:
            actions["delete"] += 1
        else:
            actions["modify"] += 1

        role, comp = classify_file_role(file_path)
        roles.setdefault(role, []).append(Path(file_path).name)

    # Determine primary role
    # Priority: auth > api > ai > model > ui > service > test > docs > config > core
    priority_order = ["auth", "api", "ai", "model", "ui", "service", "test", "docs", "config", "core"]
    primary_role = "core"
    for r in priority_order:
        if r in roles:
            primary_role = r
            break

    # Determine Conventional Commit Prefix
    if primary_role == "docs":
        prefix = "docs"
    elif primary_role == "test":
        prefix = "test"
    elif primary_role == "config":
        prefix = "chore(deps)" if any("package" in f or "req" in f or "cargo" in f for f in roles[primary_role]) else "chore(config)"
    elif actions["add"] > actions["modify"]:
        prefix = f"feat({primary_role})"
    elif actions["delete"] > (actions["add"] + actions["modify"]):
        prefix = f"refactor({primary_role})"
    else:
        prefix = f"refactor({primary_role})" if actions["modify"] > 0 else f"feat({primary_role})"

    # Construct descriptive subject
    primary_files = roles.get(primary_role, [Path(changes[0][1]).name])
    file_sample = primary_files[0]
    stem_name = Path(file_sample).stem.replace("_", " ").replace("-", " ").title()

    if primary_role == "docs":
        subject = "update project documentation and guides"
    elif primary_role == "config":
        subject = "update configuration and dependencies"
    elif primary_role == "test":
        subject = f"add/update test suite for {stem_name}"
    elif primary_role == "auth":
        subject = f"implement authentication workflow ({stem_name})"
    elif primary_role == "api":
        subject = f"update API endpoints and handlers ({stem_name})"
    elif primary_role == "model":
        subject = f"update database schemas and data models ({stem_name})"
    elif primary_role == "ui":
        subject = f"update UI components and layouts ({stem_name})"
    elif primary_role == "style":
        subject = f"improve styling and visual presentation ({stem_name})"
    elif primary_role == "ai":
        subject = f"integrate AI-assisted features and enhancements ({stem_name})"
    else:
        if actions["add"] > 0 and actions["modify"] == 0:
            subject = f"add new {stem_name} module"
        elif actions["delete"] > 0 and actions["add"] == 0:
            subject = f"clean up and remove {stem_name}"
        else:
            subject = f"update {stem_name} and related features"

    # Context tag if framework is detected
    fw_tag = f" in {stack.framework}" if stack.framework and stack.framework != "Generic Project" else ""

    return f"{prefix}: {subject}{fw_tag}"


def generate_commit_message(
    changes: list[tuple[str, str]],
    stack: ProjectStack,
    custom_msg: Optional[str] = None,
    root: Optional[Path] = None,
    diff_summary: Optional[str] = None,
    allow_ai: bool = True,
) -> tuple[str, Optional[str]]:
    """
    Generates a professional conventional commit message.

    Workflow:
    1. If user provided a custom commit message (-m / --message), use it directly.
    2. If allow_ai is True, checks if the developer is coding with AI (Antigravity IDE,
       Cursor, Aider, Claude Code, Cline, or configured Gemini/OpenAI/Anthropic/Groq/Ollama APIs).
       If AI is detected, generates an accurate message using the internal AI context.
    3. If the developer is NOT coding with AI, seamlessly uses the default heuristic generator.

    Returns:
        (commit_message, ai_source_description_or_none)
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

    # Seamless fallback to default rule-based commit generator
    default_msg = generate_default_commit_message(changes, stack)
    return default_msg, None
