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
    echo -e "\033[0;33mnpm not found. Attempting to install Node.js...\033[0m"
    if command -v apt-get &> /dev/null; then
        echo -e "\033[0;33mUsing apt-get to install nodejs and npm...\033[0m"
        sudo apt-get update && sudo apt-get install -y nodejs npm
    elif command -v brew &> /dev/null; then
        echo -e "\033[0;33mUsing brew to install node...\033[0m"
        brew install node
    else
        echo -e "\033[0;31mWarning: Could not automatically install Node.js.\033[0m"
        echo -e "\033[0;33mPlease install Node.js manually and run this script again.\033[0m"
    fi
else
    echo -e "\033[0;32mnpm is already installed.\033[0m"
fi

# 3. Check for Gemini CLI
if ! command -v gemini &> /dev/null; then
    echo -e "\033[0;33mGemini CLI not found. Installing Gemini CLI...\033[0m"
    # Try to install globally; may require sudo if not using a node version manager
    if [ -w "$(npm config get prefix)/lib/node_modules" ] 2>/dev/null; then
        npm install -g @google/gemini-cli
    else
        echo -e "\033[0;33mAttempting global install with sudo...\033[0m"
        sudo npm install -g @google/gemini-cli
    fi
    
    # Add npm global bin to current path if not there
    NPM_BIN=$(npm config get prefix)/bin
    if [[ ":$PATH:" != *":$NPM_BIN:"* ]]; then
        export PATH="$PATH:$NPM_BIN"
    fi
else
    echo -e "\033[0;32mGemini CLI is already installed.\033[0m"
fi

# 3. Run the main install script via uv
echo -e "\033[0;36mRunning project setup with uv...\033[0m"
uv run scripts/install.py

echo -e "\033[0;32m--- Setup Complete ---\033[0m"
echo -e "You can now use './rag-gemini.sh' to start the Gemini CLI with rag-dnd context."
