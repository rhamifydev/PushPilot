"""
AI Commit Generator for PushPilot.
Detects if the developer is coding with AI (e.g. Google Antigravity, Cursor,
Aider, Claude Code, Cline, or via Gemini/OpenAI/Anthropic/Groq/Ollama APIs)
and generates ultra-accurate, semantic conventional commit messages.

If the developer is not coding with AI, this module returns None, allowing
PushPilot to seamlessly fall back to the default rule-based generator.
"""

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from autopush.detector import ProjectStack, classify_file_role


@dataclass
class AiContext:
    is_coding_with_ai: bool
    source_name: str
    recent_task: Optional[str] = None
    ai_actions: list[str] = None
    ai_summary_title: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    model_name: Optional[str] = None

    def __post_init__(self):
        if self.ai_actions is None:
            self.ai_actions = []

def detect_antigravity_session(root: Path) -> Optional[tuple[str, Optional[str], list[str], Optional[str]]]:
    """
    Detects active Google Antigravity IDE session matching current project workspace.
    Extracts:
    1. AI file edit descriptions (what the AI actually implemented).
    2. AI summary title (the feature name or heading).
    3. Developer prompt (for supplemental context).
    """
    try:
        brain_dir = Path.home() / ".gemini" / "antigravity-ide" / "brain"
        if not brain_dir.is_dir():
            return None

        import time
        now = time.time()

        # Collect all transcripts and sort by transcript file modification time
        transcripts = []
        for s in brain_dir.iterdir():
            if not s.is_dir():
                continue
            t = s / ".system_generated" / "logs" / "transcript.jsonl"
            if not t.exists():
                t = s / "transcript.jsonl"
            if t.exists():
                try:
                    transcripts.append((t, t.stat().st_mtime))
                except Exception:
                    pass

        transcripts.sort(key=lambda x: x[1], reverse=True)
        if not transcripts:
            return None

        root_name = root.name.lower()
        root_str = str(root).lower().replace("/", "\\")
        root_str_fwd = str(root).lower().replace("\\", "/")

        meta_patterns = [
            r"^(git\s+push|push\s+|publish|release)",
            r"^(proceed|yes|no|ok|okay|continue|thanks|thank you)\b",
            r"^(am\s+still\s+not\s+safisfied|am\s+still\s+not\s+satisfied|commit message|why is it|why is the)",
            r"^(is it the last update|can you update|how can i update)",
        ]

        # Search for a session that belongs to this project workspace
        for transcript_path, mtime in transcripts:
            if (now - mtime) > 172800:
                continue

            try:
                t_content = transcript_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            content_lower = t_content.lower()
            if root_name not in content_lower and root_str not in content_lower and root_str_fwd not in content_lower:
                continue

            # Read lines in reverse to extract what the AI actually built
            lines = t_content.splitlines()
            task = None
            ai_actions = []
            heading_title = None

            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue

                # Check AI responses for feature headings and file modifications
                if record.get("type") == "PLANNER_RESPONSE":
                    content_str = record.get("content", "")
                    if not heading_title and content_str:
                        m_h = re.search(r"^###\s+([^|\n\r]+)", content_str, re.MULTILINE)
                        if m_h:
                            raw_h = m_h.group(1).strip()
                            if not any(raw_h.lower().startswith(x) for x in ["summary", "implementation summary", "verification", "progress"]):
                                heading_title = raw_h
                            elif " - " in raw_h or ": " in raw_h:
                                heading_title = re.split(r"[-:]", raw_h, maxsplit=1)[-1].strip()

                    for call in record.get("tool_calls", []):
                        name = call.get("name", "")
                        if name in ("replace_file_content", "write_to_file", "multi_replace_file_content"):
                            args = call.get("args", {})
                            desc = args.get("Description", "") or args.get("Instruction", "")
                            if desc:
                                clean_desc = desc.strip(""' ")
                                if clean_desc and clean_desc not in ai_actions:
                                    ai_actions.append(clean_desc)
                                if len(ai_actions) >= 5:
                                    break

                elif record.get("type") == "USER_INPUT" and not task:
                    raw = record.get("content", "")
                    match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", raw, re.DOTALL)
                    candidate = match.group(1).strip() if match else raw.strip()
                    candidate_lower = candidate.lower().strip()
                    if not any(re.search(pat, candidate_lower) for pat in meta_patterns):
                        if len(candidate) > 5:
                            task = candidate

                if (ai_actions or heading_title) and task:
                    break

            if ai_actions or heading_title or task:
                return ("Google Antigravity AI", task, ai_actions, heading_title)
    except Exception:
        pass
    return None

def detect_aider_session(root: Path) -> Optional[tuple[str, str]]:
    """Detects active Aider chat session in repository."""
    try:
        import time
        for name in [".aider.chat.history.md", ".aider.input.history"]:
            p = root / name
            if p.exists() and (time.time() - p.stat().st_mtime) < 3600:
                lines = [l.strip() for l in p.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
                if lines:
                    last_line = lines[-1]
                    # Filter out commands
                    if not last_line.startswith("/"):
                        return ("Aider AI", last_line)
                    return ("Aider AI", "refactor code with aider")
    except Exception:
        pass
    return None


def detect_cursor_session(root: Path) -> Optional[tuple[str, str]]:
    """Detects active Cursor editor environment."""
    try:
        if (root / ".cursor").is_dir() or (root / ".cursorrules").exists():
            return ("Cursor AI", "")
        if os.environ.get("CURSOR_AGENT") or os.environ.get("CURSOR_IDE"):
            return ("Cursor AI", "")
    except Exception:
        pass
    return None


def detect_claude_session(root: Path) -> Optional[tuple[str, str]]:
    """Detects Claude Code CLI session."""
    try:
        import time
        claude_dir = Path.home() / ".claude"
        if claude_dir.is_dir() and (time.time() - claude_dir.stat().st_mtime) < 3600:
            return ("Claude Code AI", "")
        if (root / ".claude").is_dir():
            return ("Claude Code AI", "")
    except Exception:
        pass
    return None


def detect_cline_session(root: Path) -> Optional[tuple[str, str]]:
    """Detects Cline / Roo Code AI environment."""
    try:
        if (root / ".cline").is_dir() or (root / ".roomodes").exists():
            return ("Cline AI", "")
    except Exception:
        pass
    return None


def detect_local_ollama() -> Optional[str]:
    """Probes if Ollama is running locally with a lightweight 0.4s timeout."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "PushPilot"})
        with urllib.request.urlopen(req, timeout=0.4) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                if models:
                    return models[0].get("name", "llama3")
                return "llama3"
    except Exception:
        pass
    return None


def detect_ai_context(root: Path) -> Optional[AiContext]:
    """
    Checks if the developer is coding with AI.
    Returns AiContext if AI signals are found; otherwise returns None (not coding with AI).
    """
    # 1. Check AI API keys in environment
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")

    # 2. Check local Ollama model
    ollama_model = detect_local_ollama()

    # 3. Check active AI IDE/assistant sessions
    antigravity_info = detect_antigravity_session(root)
    aider_info = detect_aider_session(root)
    cursor_info = detect_cursor_session(root)
    claude_info = detect_claude_session(root)
    cline_info = detect_cline_session(root)

    # Gather detected assistant
    assistant_name = None
    assistant_task = None

    ai_actions = []
    ai_summary_title = None

    if antigravity_info:
        assistant_name, assistant_task, ai_actions, ai_summary_title = antigravity_info
    elif aider_info:
        assistant_name, assistant_task = aider_info
    elif cursor_info:
        assistant_name, assistant_task = cursor_info
    elif claude_info:
        assistant_name, assistant_task = claude_info
    elif cline_info:
        assistant_name, assistant_task = cline_info

    # Explicit AI flag
    explicit_ai = os.environ.get("PUSHPILOT_AI") or os.environ.get("AI_CODING") or os.environ.get("CODING_WITH_AI")

    # Determine if any AI presence exists
    has_ai = any([
        gemini_key,
        openai_key,
        anthropic_key,
        groq_key,
        ollama_model,
        assistant_name,
        explicit_ai,
    ])

    if not has_ai:
        return None  # The developer is NOT coding with AI! Use default generator.

    # Match provider if available
    provider = None
    api_key = None
    model_name = None

    if gemini_key:
        provider = "gemini"
        api_key = gemini_key
        model_name = "gemini-1.5-flash"
    elif openai_key:
        provider = "openai"
        api_key = openai_key
        model_name = "gpt-4o-mini"
    elif groq_key:
        provider = "groq"
        api_key = groq_key
        model_name = "llama-3.1-8b-instant"
    elif anthropic_key:
        provider = "anthropic"
        api_key = anthropic_key
        model_name = "claude-3-5-haiku-20241022"
    elif ollama_model:
        provider = "ollama"
        model_name = ollama_model

    source_label = assistant_name or (f"API ({provider})" if provider else "AI Environment")

    return AiContext(
        is_coding_with_ai=True,
        source_name=source_label,
        recent_task=assistant_task,
        ai_actions=ai_actions,
        ai_summary_title=ai_summary_title,
        provider=provider,
        api_key=api_key,
        model_name=model_name,
    )


def query_llm_api(
    ctx: AiContext,
    diff_summary: str,
    stack: ProjectStack,
) -> Optional[str]:
    """Queries configured LLM API (Gemini/OpenAI/Anthropic/Groq/Ollama) with 3.5s timeout."""
    if not ctx.provider:
        return None

    prompt = (
        "You are an expert Git commit assistant. Generate ONE concise conventional commit message "
        "describing the following changes.\n"
        "Rules:\n"
        "- Follow format: <type>(<scope>): <subject>\n"
        "- Types allowed: feat, fix, docs, style, refactor, perf, test, chore, build, ci\n"
        "- Keep under 72 characters.\n"
        "- Use lowercase subject without a period at the end.\n"
        "- Return ONLY the single commit line.\n\n"
        f"Stack: {stack.language} ({stack.framework or 'None'})\n"
    )
    if ctx.ai_summary_title:
        prompt += f"Feature Implemented by AI: {ctx.ai_summary_title}\n"
    if ctx.ai_actions:
        prompt += f"AI File Modifications:\n- " + "\n- ".join(ctx.ai_actions[:3]) + "\n"
    if ctx.recent_task:
        prompt += f"Active Developer Task: {ctx.recent_task[:200]}\n"
    prompt += f"Git Changes & Diff:\n{diff_summary[:2000]}\n\nCommit Message:"

    try:
        if ctx.provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{ctx.model_name or 'gemini-1.5-flash'}:generateContent?key={ctx.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 60},
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return clean_commit_line(parts[0].get("text", ""))

        elif ctx.provider in ("openai", "groq"):
            endpoint = (
                "https://api.openai.com/v1/chat/completions"
                if ctx.provider == "openai"
                else "https://api.groq.com/openai/v1/chat/completions"
            )
            payload = {
                "model": ctx.model_name,
                "messages": [
                    {"role": "system", "content": "You output only a single conventional commit line."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 60,
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ctx.api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    return clean_commit_line(choices[0].get("message", {}).get("content", ""))

        elif ctx.provider == "anthropic":
            endpoint = "https://api.anthropic.com/v1/messages"
            payload = {
                "model": ctx.model_name,
                "max_tokens": 60,
                "messages": [{"role": "user", "content": prompt}],
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": ctx.api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("content", [])
                if content:
                    return clean_commit_line(content[0].get("text", ""))

        elif ctx.provider == "ollama":
            endpoint = "http://localhost:11434/api/generate"
            payload = {
                "model": ctx.model_name,
                "prompt": prompt,
                "stream": False,
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return clean_commit_line(data.get("response", ""))

    except Exception:
        pass
    return None


def clean_commit_line(text: str) -> Optional[str]:
    """Validates and cleans a conventional commit string."""
    if not text:
        return None
    # Take the first non-empty line
    lines = [l.strip().strip("`'\"") for l in text.strip().splitlines() if l.strip()]
    if not lines:
        return None
    candidate = lines[0]
    # Check if matches conventional commit format
    pattern = r"^(feat|fix|docs|style|refactor|perf|test|chore|build|ci)(\([a-zA-Z0-9_\-\.\/]+\))?:\s*.+$"
    if re.match(pattern, candidate, re.IGNORECASE):
        # Format properly
        return candidate.rstrip(". ")
    return None


def task_to_conventional_commit(
    task: str,
    changes: list[tuple[str, str]],
    stack: ProjectStack,
) -> str:
    """
    Transforms the active developer's AI task / prompt directly into a clean,
    highly accurate Conventional Commit message when offline or without an API key.
    """
    cleaned = task.strip().split("\n")[0].strip()

    # Remove conversational prefixes common in AI prompts
    cleaned = re.sub(
        r"^(please\s+|can\s+you\s+|could\s+you\s+|i\s+want\s+(to\s+)?|let(\x27s)?\s+|we\s+need\s+to\s+|help\s+me\s+|proceed\s+(and\s+)?)+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"^(make\s+this\s+project\s+to\s+|make\s+this\s+project\s+|make\s+|configure\s+this\s+project\s+to\s+|update\s+this\s+project\s+to\s+)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    # Strip contextual location openers like 'on the server and vps page, '
    cleaned = re.sub(r"^(on\s+the\s+[^,]+,\s*)", "", cleaned, flags=re.IGNORECASE).strip()

    # Convert click interaction phrasing: 'when i click X it should Y' -> 'Y on X click'
    m_click = re.search(r"when\s+(?:i\s+)?click\s+(?:on\s+)?(.*?)\s+(?:it\s+should\s+|to\s+)(.*)", cleaned, re.IGNORECASE)
    if m_click:
        target = m_click.group(1).strip()
        action = m_click.group(2).strip()
        action = re.split(r"\b(as\s+narrated|and\s+many\s+other|and\s+so\s+on)\b", action, flags=re.IGNORECASE)[0].strip()
        cleaned = f"{action} on {target} click"

    # Split off subordinate/conditional clauses (if..., so that..., in order to...)
    parts = re.split(r"\b(so\s+that\b|in\s+order\s+to\b|and\s+use\b|as\s+narrated\b)", cleaned, maxsplit=1, flags=re.IGNORECASE)
    if parts and parts[0].strip():
        cleaned = parts[0].strip()

    # 1. Determine dominant scope from actual changed files
    comp_counts: dict[str, int] = {}
    roles: dict[str, int] = {}
    for status, file_path in changes:
        role, comp = classify_file_role(file_path)
        roles[role] = roles.get(role, 0) + 1
        comp_clean = comp.lower().replace("layout", "").replace("index", "").strip()
        if comp_clean and len(comp_clean) > 2:
            comp_counts[comp_clean] = comp_counts.get(comp_clean, 0) + 1

    if comp_counts:
        scope = sorted(comp_counts.items(), key=lambda x: x[1], reverse=True)[0][0]
    else:
        scope = Path(changes[0][1]).stem.lower() if changes else "core"

    scope = re.sub(r"[^\w-]", "", scope)[:16] or "core"

    # If changes involve ai commit / commit generator, use ai scope
    if any("ai" in f.lower() or "commit" in f.lower() for _, f in changes):
        scope = "ai"

    # 2. Determine commit type
    c_type = "feat"
    if re.search(r"\b(fix|resolve|bug|issue|error|broken|patch|prevent|handle error)\b", cleaned, re.IGNORECASE):
        c_type = "fix"
    elif re.search(r"\b(refactor|clean|cleanup|reorganize|restructure|optimize|simplify)\b", cleaned, re.IGNORECASE):
        c_type = "refactor"
    elif re.search(r"\b(test|tests|spec|coverage|unit test)\b", cleaned, re.IGNORECASE):
        c_type = "test"
    elif re.search(r"\b(doc|docs|readme|documentation|guide)\b", cleaned, re.IGNORECASE):
        c_type = "docs"
    elif re.search(r"\b(chore|dependency|dependencies|bump|package|release|setup|install)\b", cleaned, re.IGNORECASE):
        c_type = "chore"

    # 3. Clean up subject line
    cleaned = re.sub(r"[\s,\.:;!?\-_]+$", "", cleaned).strip()
    words = cleaned.split()
    if len(" ".join(words)) > 55:
        truncated = []
        for w in words:
            if len(" ".join(truncated + [w])) <= 52:
                truncated.append(w)
            else:
                break
        cleaned = " ".join(truncated)

    cleaned = re.sub(r"[\s,\.:;!?\-_]+$", "", cleaned).strip()
    return f"{c_type}({scope}): {cleaned.lower()}"


def synthesize_ai_implemented_feature(
    ctx: AiContext,
    changes: list[tuple[str, str]],
    stack: ProjectStack,
) -> Optional[str]:
    """
    Synthesizes a conventional commit message from what the AI actually implemented:
    1. AI summary heading or feature name from the conversation.
    2. Tool call descriptions / instructions showing what code the AI changed.
    3. Developer prompt fallback.
    """
    # 1. Determine dominant scope from changed files
    comp_counts: dict[str, int] = {}
    for status, fp in changes:
        role, comp = classify_file_role(fp)
        comp_clean = comp.lower().replace("layout", "").replace("index", "").strip()
        if comp_clean and len(comp_clean) > 2:
            comp_counts[comp_clean] = comp_counts.get(comp_clean, 0) + 1

    if comp_counts:
        scope = sorted(comp_counts.items(), key=lambda x: x[1], reverse=True)[0][0]
    else:
        scope = Path(changes[0][1]).stem.lower() if changes else "core"

    scope = re.sub(r"[^\w-]", "", scope)[:16] or "core"
    if any("ai" in f.lower() or "commit" in f.lower() for _, f in changes):
        scope = "ai"

    fw_tag = f" in {stack.framework}" if stack.framework and stack.framework != "Generic Project" else ""

    # 2. Priority 1: Use AI summary title (e.g. 'Redesign & Remote File Explorer Implementation')
    if ctx.ai_summary_title:
        title = ctx.ai_summary_title.strip().strip("#: ")
        title = re.sub(r"\b(Implementation|Summary|Overview|Update|Feature)\b", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"[\s&/\\-]+", " ", title).strip()
        if len(title) > 4:
            c_type = "refactor" if ("redesign" in title.lower() or "refactor" in title.lower()) else "feat"
            return f"{c_type}({scope}): implement {title.lower()}{fw_tag}"

    # 3. Priority 2: Use AI file modification descriptions
    if ctx.ai_actions:
        top_edit = ctx.ai_actions[0].strip()
        # Clean file paths out of description
        cleaned = re.sub(r"\b(in|at|for|to)\s+[A-Za-z0-9_/\\-]+\.(jsx?|tsx?|php|py|vue|html|css|json)\b", "", top_edit, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b[A-Za-z0-9_/\\-]+\.(jsx?|tsx?|php|py|vue|html|css|json)\b", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Determine conventional commit type
        c_type = "feat"
        if re.search(r"^(fix|resolve|prevent|patch|handle)\b", cleaned, re.IGNORECASE):
            c_type = "fix"
        elif re.search(r"^(redesign|refactor|clean|cleanup|reorganize|optimize)\b", cleaned, re.IGNORECASE):
            c_type = "refactor"
        elif re.search(r"^(doc|docs|readme)\b", cleaned, re.IGNORECASE):
            c_type = "docs"
        elif re.search(r"^(test|tests)\b", cleaned, re.IGNORECASE):
            c_type = "test"

        words = cleaned.split()
        if len(" ".join(words)) > 55:
            words = words[:8]
            cleaned = " ".join(words)
        cleaned = re.sub(r"[\s,\.:;!?\-_]+$", "", cleaned).strip()

        if cleaned and len(cleaned) > 5:
            return f"{c_type}({scope}): {cleaned.lower()}{fw_tag}"

    # 4. Priority 3: Fall back to developer task
    if ctx.recent_task:
        return task_to_conventional_commit(ctx.recent_task, changes, stack)

    return None

def generate_ai_commit_message(
    changes: list[tuple[str, str]],
    stack: ProjectStack,
    diff_summary: str,
    root: Path,
) -> tuple[Optional[str], Optional[str]]:
    """
    Checks if coding with AI and generates an accurate commit message.

    Returns:
        (commit_message, ai_source_description) if coding with AI and generation succeeded.
        (None, None) if the developer is NOT coding with AI or if generation yielded no result.
    """
    ctx = detect_ai_context(root)
    if not ctx or not ctx.is_coding_with_ai:
        return None, None  # NOT coding with AI -> caller uses default!

    # 1. Try querying LLM API if key/local model exists
    if ctx.provider:
        llm_msg = query_llm_api(ctx, diff_summary, stack)
        if llm_msg:
            return llm_msg, f"{ctx.source_name} ({ctx.model_name})"

    # 2. Synthesize what the AI actually implemented (feature summary & file modifications)
    synthesized_msg = synthesize_ai_implemented_feature(ctx, changes, stack)
    if synthesized_msg:
        return synthesized_msg, ctx.source_name

    # 3. If AI environment detected (like Cursor or AI flag) but no task/API available,
    # generate an AI-tailored conventional message using stack and changes
    return None, None
