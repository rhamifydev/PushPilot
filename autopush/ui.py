"""
PushPilot Modern Terminal UI & Theme Engine.
Provides clean ANSI styling, semantic color badges, elegant banners,
and formatted status indicators with zero external dependencies.
"""

import os
import sys
from typing import Optional

# Enable Virtual Terminal Processing on Windows consoles
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # Enable VT100 console mode
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        os.system("")

# Detect color support
COLOR_ENABLED = (
    "NO_COLOR" not in os.environ
    and (
        hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        or os.environ.get("TERM") in ("xterm", "xterm-256color", "vt100")
        or "WT_SESSION" in os.environ
    )
)


class Style:
    RESET = "\033[0m" if COLOR_ENABLED else ""
    BOLD = "\033[1m" if COLOR_ENABLED else ""
    DIM = "\033[2m" if COLOR_ENABLED else ""
    UNDERLINE = "\033[4m" if COLOR_ENABLED else ""

    # Foreground colors
    BLACK = "\033[30m" if COLOR_ENABLED else ""
    RED = "\033[31m" if COLOR_ENABLED else ""
    GREEN = "\033[32m" if COLOR_ENABLED else ""
    YELLOW = "\033[33m" if COLOR_ENABLED else ""
    BLUE = "\033[34m" if COLOR_ENABLED else ""
    MAGENTA = "\033[35m" if COLOR_ENABLED else ""
    CYAN = "\033[36m" if COLOR_ENABLED else ""
    WHITE = "\033[37m" if COLOR_ENABLED else ""

    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m" if COLOR_ENABLED else ""
    BRIGHT_RED = "\033[91m" if COLOR_ENABLED else ""
    BRIGHT_GREEN = "\033[92m" if COLOR_ENABLED else ""
    BRIGHT_YELLOW = "\033[93m" if COLOR_ENABLED else ""
    BRIGHT_BLUE = "\033[94m" if COLOR_ENABLED else ""
    BRIGHT_MAGENTA = "\033[95m" if COLOR_ENABLED else ""
    BRIGHT_CYAN = "\033[96m" if COLOR_ENABLED else ""
    BRIGHT_WHITE = "\033[97m" if COLOR_ENABLED else ""

    # Backgrounds
    BG_BLUE = "\033[44m" if COLOR_ENABLED else ""
    BG_MAGENTA = "\033[45m" if COLOR_ENABLED else ""
    BG_CYAN = "\033[46m" if COLOR_ENABLED else ""


def banner(version: str) -> None:
    """Prints a modern, elegant CLI header banner."""
    b = Style.BOLD
    c = Style.BRIGHT_CYAN
    m = Style.BRIGHT_MAGENTA
    w = Style.BRIGHT_WHITE
    d = Style.DIM
    r = Style.RESET

    print(f"\n{c}╭─────────────────────────────────────────────────────────────╮{r}")
    print(f"{c}│{r}   {b}🚀 {w}PUSHPILOT{r} {c}v{version}{r}{' ' * (44 - len(version))}{c}│{r}")
    print(f"{c}│{r}   {d}Intelligent Multi-Framework Git & GitHub Autopilot{r}        {c}│{r}")
    print(f"{c}╰─────────────────────────────────────────────────────────────╯{r}\n")


def badge(label: str, title: str, subtitle: Optional[str] = None, color: str = Style.BRIGHT_CYAN) -> None:
    """Prints a styled badge tag with primary title and optional detail."""
    b = Style.BOLD
    d = Style.DIM
    r = Style.RESET
    sub = f" {d}({subtitle}){r}" if subtitle else ""
    print(f"{color}{b}[{label}]{r} {b}{title}{r}{sub}")


def info(msg: str) -> None:
    print(f"{Style.BRIGHT_BLUE}ℹ{Style.RESET} {msg}")


def success(msg: str) -> None:
    print(f"{Style.BRIGHT_GREEN}{Style.BOLD}✔ {msg}{Style.RESET}")


def warn(msg: str) -> None:
    print(f"{Style.BRIGHT_YELLOW}{Style.BOLD}▲ {msg}{Style.RESET}")


def error(msg: str) -> None:
    print(f"{Style.BRIGHT_RED}{Style.BOLD}✖ {msg}{Style.RESET}")


def dry_run_badge(msg: str) -> None:
    print(f"{Style.BRIGHT_YELLOW}{Style.BOLD}[DRY-RUN]{Style.RESET} {msg}")


def format_change_item(status: str, file_path: str) -> str:
    """Formats a git file change line with color and symbol."""
    status = (status or "").strip()
    r = Style.RESET
    d = Style.DIM

    if "?" in status:
        symbol = f"{Style.BRIGHT_CYAN}+ [NEW]{r}"
    elif "A" in status:
        symbol = f"{Style.BRIGHT_GREEN}+ [ADD]{r}"
    elif "D" in status:
        symbol = f"{Style.BRIGHT_RED}- [DEL]{r}"
    elif "M" in status or "R" in status:
        symbol = f"{Style.BRIGHT_YELLOW}~ [MOD]{r}"
    else:
        symbol = f"{Style.BRIGHT_WHITE}• [{status or 'CHG'}]{r}"

    # Highlight filename stem
    parts = file_path.replace("\\", "/").rsplit("/", 1)
    if len(parts) == 2:
        dir_part, filename = parts
        return f"   {symbol} {d}{dir_part}/{r}{Style.BOLD}{filename}{r}"
    return f"   {symbol} {Style.BOLD}{file_path}{r}"
