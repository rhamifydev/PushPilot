#!/usr/bin/env bash
# PushPilot One-Command Unix Installer (macOS, Linux, WSL)
# Installs PushPilot and ensures user bin directory is in PATH

set -e

echo -e "\n\033[1;36m=== Installing PushPilot ===\033[0m"

# 1. Install or upgrade PushPilot
python3 -m pip install --upgrade pushpilot --no-warn-script-location

# 2. Automatically ensure user bin directory is in PATH
USER_BIN=$(python3 -c "import sysconfig; print(sysconfig.get_path('scripts', 'posix_user'))" 2>/dev/null || echo "$HOME/.local/bin")

if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
    SHELL_RC="$HOME/.bashrc"
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_RC="$HOME/.zshrc"
    fi
    if [ -f "$SHELL_RC" ]; then
        if ! grep -q "$USER_BIN" "$SHELL_RC"; then
            echo "export PATH=\"\$PATH:$USER_BIN\"" >> "$SHELL_RC"
            echo -e "\033[1;32m✔ Added $USER_BIN to $SHELL_RC\033[0m"
        fi
    fi
    export PATH="$PATH:$USER_BIN"
fi

echo -e "\n\033[1;32m🚀 PushPilot installed successfully!\033[0m"
echo -e "\033[1;36mTry running: pushpilot\033[0m\n"
