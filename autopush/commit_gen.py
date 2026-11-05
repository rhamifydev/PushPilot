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


def _extract_diff_keywords(diff_text: str) -> list[str]:
    """Extracts meaningful technical keywords from diff text for subject generation."""
    if not diff_text:
        return []

    keywords: list[str] = []
    diff_lower = diff_text.lower()

    # Detect layout-related patterns
    layout_terms = []
    if re.search(r"(flex|grid|responsive|mobile|desktop|tablet|breakpoint|media\s*query|@media)", diff_lower):
        if re.search(r"(mobile|sm:|max-width:\s*\d+)", diff_lower):
            layout_terms.append("mobile-first")
        if re.search(r"(responsive|breakpoint|@media|media\s*query)", diff_lower):
            layout_terms.append("responsive")
        if re.search(r"(grid|flex-wrap|grid-template)", diff_lower):
            layout_terms.append("grid")
        if re.search(r"(flex|flexbox|flex-direction)", diff_lower):
            layout_terms.append("flex")

    # Detect UI component patterns
    ui_terms = []
    component_patterns = [
        (r"(carousel|slider|swipe|swiper)", "carousel"),
        (r"(modal|dialog|popup|overlay)", "modal"),
        (r"(banner|hero|header\s+banner|jumbotron)", "banner"),
        (r"(sidebar|side-bar|drawer|nav-drawer)", "sidebar"),
        (r"(navbar|nav-bar|navigation\s+bar|top-bar)", "navbar"),
        (r"(dropdown|drop-down|select\s+menu|popover)", "dropdown"),
        (r"(table|data-table|datagrid|data\s+grid)", "table"),
        (r"(form|input\s+field|text-field|form-group)", "form"),
        (r"(card|card-group|card\s+list|tile)", "card"),
        (r"(tab|tabs|tab-bar|tab\s+panel)", "tabs"),
        (r"(accordion|collapsible|expandable)", "accordion"),
        (r"(toast|snackbar|notification|alert)", "notification"),
        (r"(pagination|paginator|page-nav)", "pagination"),
        (r"(breadcrumb|breadcrumbs)", "breadcrumb"),
        (r"(tooltip|popover|hint)", "tooltip"),
        (r"(chart|graph|visualization|pie-chart|bar-chart)", "chart"),
        (r"(avatar|profile\s*pic|user\s*icon)", "avatar"),
        (r"(badge|chip|tag|label)", "badge"),
        (r"(stepper|wizard|multi-step)", "stepper"),
        (r"(skeleton|shimmer|placeholder\s+load)", "skeleton loader"),
        (r"(search\s*bar|search\s*input|search\s*field)", "search"),
        (r"(file\s*upload|dropzone|drag.{0,5}drop)", "file upload"),
    ]
    for pattern, term in component_patterns:
        if re.search(pattern, diff_lower):
            ui_terms.append(term)

    # Detect feature / domain patterns
    feature_terms = []
    feature_patterns = [
        (r"(auth|login|sign.?in|sign.?up|register|oauth|jwt|session)", "authentication"),
        (r"(database|db|migration|schema|sequelize|prisma|typeorm|mongoose|sql)", "database"),
        (r"(api|endpoint|route|controller|handler|middleware|rest|graphql)", "API"),
        (r"(websocket|socket\.io|real.?time|sse|event.?stream)", "real-time"),
        (r"(cache|redis|memcached|caching|invalidat)", "caching"),
        (r"(upload|download|file.?manag|blob|storage|s3)", "file management"),
        (r"(email|smtp|sendgrid|mailgun|notification|push.?notif)", "notifications"),
        (r"(payment|stripe|paypal|billing|checkout|invoice)", "payments"),
        (r"(i18n|locale|translation|intl|localization)", "localization"),
        (r"(dark.?mode|theme|color.?scheme|theming)", "theming"),
        (r"(animation|transition|motion|animate|keyframe)", "animation"),
        (r"(scroll|infinite.?scroll|virtual.?scroll|lazy.?load)", "scroll behavior"),
        (r"(test|spec|coverage|jest|vitest|pytest|mocha)", "test coverage"),
        (r"(deploy|ci|cd|pipeline|workflow|docker|k8s)", "deployment"),
        (r"(error.?handl|try.?catch|error.?boundar|fallback)", "error handling"),
        (r"(permission|role|rbac|acl|access.?control)", "permissions"),
        (r"(settings|config|preference|option)", "settings"),
        (r"(dashboard|admin|analytics|metrics)", "dashboard"),
        (r"(profile|account|user.?settings)", "user profile"),
        (r"(comment|review|rating|feedback)", "user feedback"),
    ]
    for pattern, term in feature_patterns:
        if re.search(pattern, diff_lower):
            feature_terms.append(term)

    # Detect action / verb patterns from diff hunks
    action_terms = []
    action_patterns = [
        (r"\+.*\b(horizontal|swipe|scroll-snap|overflow-x)", "horizontal swipe"),
        (r"\+.*\b(compact|condensed|mini|small|dense)", "compact"),
        (r"\+.*\b(drag|drop|sortable|reorder)", "drag-and-drop"),
        (r"\+.*\b(filter|sort|search|query)", "filtering"),
        (r"\+.*\b(validate|validation|required|pattern)", "validation"),
        (r"\+.*\b(loading|spinner|skeleton|progress)", "loading state"),
        (r"\+.*\b(debounce|throttle|rate.?limit)", "performance"),
        (r"\+.*\b(lazy|defer|suspend|async)", "lazy loading"),
        (r"\+.*\b(cache|memo|useMemo|useCallback|memoize)", "memoization"),
    ]
    for pattern, term in action_patterns:
        if re.search(pattern, diff_text):
            action_terms.append(term)

    keywords = layout_terms + action_terms + ui_terms + feature_terms
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
    return unique[:5]


def _collect_page_names(changes: list[tuple[str, str]]) -> list[str]:
    """Extracts human-readable page/feature names from file paths.
    Prefers the parent feature folder (e.g. 'database' from 'pages/database/DatabasePage.tsx')
    over raw filenames, and splits camelCase/PascalCase into readable words.
    """
    page_names = []
    skip_names = {
        "index", "app", "layout", "main", "root", "base", "home",
        "component", "components", "page", "pages", "view", "views",
        "src", "lib", "utils", "helpers", "styles", "assets", "public",
        "api", "routes", "controllers", "services", "models", "config",
        "http", "resources", "js", "ts", "jsx", "tsx", "css",
        "docs", "doc", "test", "tests", "spec", "specs",
    }
    for _, fp in changes:
        parts = Path(fp).parts
        # Walk backwards through path segments, preferring feature folder names
        found = None
        for part in reversed(parts[:-1]):  # Skip the filename itself first
            name = part.lower().replace("_", " ").replace("-", " ")
            name_clean = re.sub(r"[^a-z0-9]", "", name)
            if name_clean and name_clean not in skip_names and len(name_clean) > 2:
                found = name
                break
        if not found:
            # Fall back to the filename stem, split camelCase
            stem = Path(parts[-1]).stem
            name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", stem).lower()
            name = name.replace("_", " ").replace("-", " ")
            # Strip generic suffixes
            name = re.sub(r"\b(page|view|controller|handler|component|service|model|screen)\b", "", name, flags=re.IGNORECASE).strip()
            name = re.sub(r"\s+", " ", name).strip()
            name_clean = re.sub(r"[^a-z0-9]", "", name)
            if name_clean and name_clean not in skip_names and len(name_clean) > 2:
                found = name
        if found:
            page_names.append(found)

    # Count and return most frequent, deduplicating
    counts: dict[str, int] = {}
    for n in page_names:
        counts[n] = counts.get(n, 0) + 1
    return [n for n, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)][:3]


def generate_default_commit_message(
    changes: list[tuple[str, str]],
    stack: ProjectStack,
    diff_summary: Optional[str] = None,
) -> str:
    """
    Generates descriptive, human-quality conventional commit messages.
    Analyzes actual diff content, UI patterns, and feature domains to produce
    messages that describe *what was built*, not just which files changed.
    """
    if not changes:
        return "chore: sync project updates"

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

        comp_clean = comp.lower().replace("layout", "").replace("index", "").strip()
        weight = 0 if (is_deleted and has_active_edits) else 1

        if weight > 0:
            if comp_clean and len(comp_clean) > 2:
                comp_counts[comp_clean] = comp_counts.get(comp_clean, 0) + 1
            elif comp:
                comp_counts[comp.lower()] = comp_counts.get(comp.lower(), 0) + 1

    # 2. Determine dominant role
    dominant_role = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[0][0] if role_counts else "core"

    # 3. Determine conventional commit type (without scope in parentheses)
    diff_lower = (diff_summary or "").lower()
    if dominant_role == "docs":
        c_type = "docs"
    elif dominant_role == "test":
        c_type = "test"
    elif dominant_role == "config":
        c_type = "chore"
    elif re.search(r"\b(fix|bug|resolve|error|patch|broken|crash|regression)\b", diff_lower):
        c_type = "fix"
    elif re.search(r"\b(refactor|cleanup|reorganize|simplify|restructure|optimize)\b", diff_lower):
        c_type = "refactor"
    elif actions["delete"] > (actions["add"] + actions["modify"]):
        c_type = "refactor"
    elif dominant_role == "style":
        c_type = "style"
    elif re.search(r"\b(perf|performance|speed|latency|benchmark|optimize)\b", diff_lower):
        c_type = "perf"
    else:
        c_type = "feat"

    # 4. Build a descriptive subject from diff content analysis
    diff_keywords = _extract_diff_keywords(diff_summary or "")
    page_names = _collect_page_names(changes)

    # Extract specific diff context (function names, UI text)
    diff_hint = extract_diff_context(diff_summary or "")

    # 5. Compose natural, descriptive subject
    if diff_keywords:
        # We have meaningful keywords from the actual diff — compose from them
        page_context = f" {page_names[0]} page" if page_names else ""
        keyword_str = " ".join(diff_keywords[:4])

        # Build subject with keywords and page context
        if page_context:
            subject = f"{page_context.strip()} layout with {keyword_str}" if "layout" in " ".join(diff_keywords) or dominant_role == "ui" else f"{keyword_str} for{page_context}"
        else:
            subject = keyword_str

        # If we have a strong diff hint (specific function/UI element), weave it in
        if diff_hint and diff_hint.lower() not in subject.lower():
            if len(subject) + len(diff_hint) < 58:
                subject = f"{subject} and {diff_hint}"

    elif diff_hint:
        # We have a specific code-level hint but no broad keywords
        page_ctx = f" in {page_names[0]}" if page_names else ""
        subject = f"{diff_hint}{page_ctx}"

    elif page_names:
        # No diff keywords, but we know which pages/features were touched
        pages_str = ", ".join(page_names[:2])
        if dominant_role == "docs":
            subject = f"update {pages_str} documentation"
        elif dominant_role == "config":
            if any("package" in f or "req" in f or "composer" in f or "cargo" in f for _, f in changes):
                subject = f"update {pages_str} dependencies"
            else:
                subject = f"update {pages_str} configuration"
        elif dominant_role == "ui":
            if actions["add"] > actions["modify"]:
                subject = f"{pages_str} page layout and components"
            else:
                subject = f"refine {pages_str} page UI and interactions"
        elif dominant_role == "api":
            subject = f"{pages_str} API endpoints and request handling"
        elif dominant_role == "model":
            subject = f"{pages_str} data models and schema updates"
        elif dominant_role == "auth":
            # Avoid "auth auth" duplication
            if any(p.lower() == "auth" for p in page_names[:2]):
                subject = "authentication flow and session management"
            else:
                subject = f"{pages_str} auth flow and session management"
        elif dominant_role == "style":
            subject = f"{pages_str} styling and visual refinements"
        elif dominant_role == "service":
            subject = f"{pages_str} service layer and business logic"
        elif dominant_role == "test":
            subject = f"add and update {pages_str} test coverage"
        else:
            if actions["add"] > 0 and actions["modify"] == 0:
                subject = f"add {pages_str} module"
            elif actions["delete"] > 0 and actions["add"] == 0:
                subject = f"remove {pages_str} resources"
            else:
                subject = f"update {pages_str} logic and structure"
    else:
        # Absolute fallback — still try to be descriptive
        if dominant_role == "docs":
            subject = "update project documentation"
        elif dominant_role == "config":
            if any("package" in f or "req" in f or "composer" in f or "cargo" in f for _, f in changes):
                subject = "update project dependencies"
            else:
                subject = "update project configuration"
        elif dominant_role == "test":
            subject = "add and update test coverage"
        elif actions["add"] > 0 and actions["modify"] == 0:
            subject = "add new project modules"
        elif actions["delete"] > 0 and actions["add"] == 0:
            subject = "clean up unused code and resources"
        else:
            subject = "update project structure and logic"

    # 6. Clean and finalize
    subject = subject.strip()
    subject = re.sub(r"\s+", " ", subject)
    # Enforce lowercase start
    if subject:
        subject = subject[0].lower() + subject[1:]
    # Trim to conventional commit length (~72 chars total)
    max_subject_len = 68 - len(c_type)
    if len(subject) > max_subject_len:
        words = subject.split()
        trimmed = []
        for w in words:
            if len(" ".join(trimmed + [w])) <= max_subject_len:
                trimmed.append(w)
            else:
                break
        subject = " ".join(trimmed)
    subject = re.sub(r"[\s,\.:;!?\-_]+$", "", subject).strip()

    return f"{c_type}: {subject}"


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
