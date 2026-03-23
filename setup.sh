#!/bin/bash
set -e

echo -e "\033[0;36m--- rag-dnd Setup ---\033[0m"

# 1. Check for uv
if ! command -v uv &> /dev/null; then
    echo -e "\033[0;33muv not found. Installing uv...\033[0m"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
else
    echo -e "\033[0;32muv is already installed.\033[0m"
fi

# 2. Check for node/npm
if ! command -v npm &> /dev/null; then
    echo -e "\033[0;31mWarning: npm not found. Gemini CLI installation might fail.\033[0m"
    echo -e "\033[0;33mPlease install Node.js and run this script again.\033[0m"
fi

# 3. Run the main install script via uv
echo -e "\033[0;36mRunning project setup with uv...\033[0m"
uv run scripts/install.py

echo -e "\033[0;32m--- Setup Complete ---\033[0m"
echo -e "You can now use './rag-gemini.sh' to start the Gemini CLI with rag-dnd context."
