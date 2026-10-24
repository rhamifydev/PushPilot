"""
Conventional Commit Message Generator.
Generates human-readable, semantic, and professional commit messages
using file categorization, change diff heuristics, and framework context.
"""

from pathlib import Path
from autopush.detector import ProjectStack, classify_file_role


def generate_commit_message(
    changes: list[tuple[str, str]],
    stack: ProjectStack,
    custom_msg: str | None = None,
) -> str:
    """Generates a professional conventional commit message.
    e.g.:
      - feat(auth): add login endpoint in FastAPI
      - feat(ui): add NavigationBar component in React
      - fix(api): resolve user update route handling
      - chore(deps): update project dependencies
      - docs: update README and setup guides
    """
    if custom_msg and custom_msg.strip():
        return custom_msg.strip()

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
    # Priority: auth > api > model > ui > service > test > docs > config > core
    priority_order = ["auth", "api", "model", "ui", "service", "test", "docs", "config", "core"]
    primary_role = "core"
    for r in priority_order:
        if r in roles:
            primary_role = r
            break

    # Determine Conventional Commit Prefix
    if primary_role == "docs":
        prefix = "docs"
        scope = None
    elif primary_role == "test":
        prefix = "test"
        scope = roles[primary_role][0].split(".")[0] if roles[primary_role] else None
    elif primary_role == "config":
        prefix = "chore(deps)" if any("package" in f or "req" in f or "cargo" in f for f in roles[primary_role]) else "chore(config)"
        scope = None
    elif actions["add"] > actions["modify"]:
        prefix = f"feat({primary_role})"
        scope = None
    elif actions["delete"] > (actions["add"] + actions["modify"]):
        prefix = f"refactor({primary_role})"
        scope = None
    else:
        prefix = f"refactor({primary_role})" if actions["modify"] > 0 else f"feat({primary_role})"
        scope = None

    # Construct descriptive subject
    primary_files = roles.get(primary_role, [Path(changes[0][1]).name])
    file_sample = primary_files[0]
    stem_name = Path(file_sample).stem.replace("_", " ").replace("-", " ").title()

    if primary_role == "docs":
        subject = f"update project documentation and guides"
    elif primary_role == "config":
        subject = f"update configuration and dependencies"
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
    else:
        if actions["add"] > 0 and actions["modify"] == 0:
            subject = f"add new {stem_name} module"
        elif actions["delete"] > 0 and actions["add"] == 0:
            subject = f"clean up and remove {stem_name}"
        else:
            subject = f"update {stem_name} and related features"

    # Context tag if framework is detected
    fw_tag = f" in {stack.framework}" if stack.framework and stack.framework != "Generic Project" else ""

    message = f"{prefix}: {subject}{fw_tag}"
    return message
