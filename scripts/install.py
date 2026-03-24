import json
import os
import subprocess
import sys
from pathlib import Path
import re

SETTINGS_TEMPLATE = {
    "tools": {
        "enableHooks": True
    },
    "hooks": {
        "disabled": [],
        "enabled": [],
        "notifications": [],
        "BeforeAgent": [
            {
                "hooks": [
                    {
                        "name": "dnd-rag-context",
                        "type": "command",
                        "command": "uv --directory DIRECTORY_PLACEHOLDER run rag-hook-context",
                        "timeout": 30000
                    }
                ]
            }
        ],
        "AfterAgent": [
            {
                "hooks": [
                    {
                        "name": "dnd-rag-logger",
                        "type": "command",
                        "command": "uv --directory DIRECTORY_PLACEHOLDER run rag-hook-logger",
                        "timeout": 5000
                    }
                ]
            }
        ]
    },
    "mcpServers": {
        "rag-mcp": {
            "command": "uv",
            "args": [
                "--directory",
                "DIRECTORY_PLACEHOLDER",
                "run",
                "rag-mcp"
            ]
        }
    }
}

def print_cyan(text):
    print(f"\033[96m{text}\033[0m")

def print_green(text):
    print(f"\033[92m{text}\033[0m")

def print_yellow(text):
    print(f"\033[93m{text}\033[0m")

def print_red(text):
    print(f"\033[91m{text}\033[0m")

def run_command(command, shell=True):
    try:
        subprocess.run(command, shell=shell, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print_red(f"Error running command: {command}")
        print_red(e.stderr)
        return False

def check_npm():
    try:
        # Prefer 'npm.cmd' on Windows to avoid issues with basic 'npm' command in some environments
        cmd = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.run([cmd, "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_gemini_cli():
    print_cyan("Checking for Gemini CLI...")
    # Try multiple ways to find 'gemini'
    found = False
    try:
        cmd = "gemini.cmd" if os.name == "nt" else "gemini"
        subprocess.run([cmd, "--version"], check=True, capture_output=True)
        found = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback check for common paths on Windows
        if os.name == "nt":
            npm_path = Path(os.environ.get("APPDATA", "")) / "npm" / "gemini.cmd"
            if npm_path.exists():
                found = True
        else:
            # Fallback check for common paths on Linux
            home_bin = Path.home() / ".npm-global" / "bin" / "gemini"
            usr_local_bin = Path("/usr/local/bin/gemini")
            if home_bin.exists() or usr_local_bin.exists():
                found = True
    
    if found:
        print_green("Gemini CLI is available.")
        return True

    print_yellow("Gemini CLI not found in PATH. Attempting to install/find via npm...")
    if check_npm():
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        if run_command(f"{npm_cmd} install -g @google/gemini-cli"):
            print_green("Gemini CLI installed successfully.")
            return True
        else:
            print_red("Failed to install Gemini CLI.")
            return False
    else:
        print_red("npm not found. Cannot install Gemini CLI automatically.")
        return False

def configure_settings(project_root: Path):
    print_cyan("Configuring .gemini/settings.json...")
    settings_path = project_root / ".gemini" / "settings.json"
    
    if not settings_path.exists():
        print_yellow(f".gemini/settings.json not found. Creating from template...")
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = SETTINGS_TEMPLATE
    else:
        with open(settings_path, 'r') as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                print_red(f"Error: {settings_path} is not a valid JSON file.")
                return

    # Update paths to be absolute based on the current project location
    root_posix = project_root.resolve().as_posix()
    
    # Update Hooks
    if "hooks" in settings:
        # Ensure hooks are enabled
        enabled_hooks = settings["hooks"].get("enabled", [])
        for hook_name in ["dnd-rag-context", "dnd-rag-logger"]:
            if hook_name not in enabled_hooks:
                enabled_hooks.append(hook_name)
        settings["hooks"]["enabled"] = enabled_hooks

        for phase in ["BeforeAgent", "AfterAgent"]:
            if phase in settings["hooks"]:
                for hook_group in settings["hooks"][phase]:
                    for hook in hook_group.get("hooks", []):
                        if "command" in hook:
                            cmd = hook["command"]
                            import re
                            # Pattern matches --directory followed by a path (possibly quoted)
                            pattern = r'(--directory\s+)("[^"]+"|[^\s]+)'
                            # Smart quoting: only add quotes if the path contains spaces
                            replacement = lambda m: f'{m.group(1)}"{root_posix}"' if " " in root_posix else f'{m.group(1)}{root_posix}'
                            hook["command"] = re.sub(pattern, replacement, cmd)

    # Update MCP
    if "mcpServers" in settings:
        for server_name, server_config in settings["mcpServers"].items():
            if "args" in server_config:
                args = server_config["args"]
                try:
                    idx = args.index("--directory")
                    args[idx+1] = root_posix
                except (ValueError, IndexError):
                    pass

    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)
    print_green("Settings updated with absolute paths.")

def create_system_prompt(project_root: Path):
    system_prompt_path = project_root / "system.md"
    if not system_prompt_path.exists():
        print_cyan("Creating system.md...")
        content = """# rag-dnd System Prompt

You are an AI assistant helping with the **rag-dnd** project.
This project is a Retrieval-Augmented Generation system for D&D session logs.

Refer to the `GEMINI.md` file for project documentation and architecture overview.

When answering questions about the campaign, always check the RAG context provided by the hooks.
"""
        with open(system_prompt_path, 'w') as f:
            f.write(content)
        print_green("system.md created.")
    else:
        print_green("system.md already exists.")

def create_launchers(project_root: Path):
    print_cyan("Creating launchers...")
    root_str = str(project_root.resolve())
    
    # Windows Launcher
    bat_path = project_root / "rag-gemini.bat"
    bat_content = f"""@echo off
set "GEMINI_SYSTEM_MD={root_str}\\system.md"
cd /d "{root_str}"
echo [rag-dnd] Starting API server in background...
start /b uv run rag-server >nul 2>&1
timeout /t 2 >nul
gemini
"""
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    # Linux Launcher
    sh_path = project_root / "rag-gemini.sh"
    sh_content = f"""#!/bin/bash
export GEMINI_SYSTEM_MD="{root_str}/system.md"
cd "{root_str}"
echo "[rag-dnd] Starting API server in background..."
uv run rag-server > /dev/null 2>&1 &
sleep 2
gemini
"""
    with open(sh_path, 'w', encoding='utf-8') as f:
        f.write(sh_content)
    os.chmod(sh_path, 0o755)
    
    print_green("Launchers created (rag-gemini.bat, rag-gemini.sh).")

def main():
    project_root = Path(__file__).parent.parent
    
    print_cyan("Step 1: Syncing project dependencies...")
    if run_command("uv sync"):
        print_green("Project synced.")
    else:
        print_red("Failed to sync project.")
        return

    print_cyan("Step 2: Setting up Gemini CLI...")
    if not install_gemini_cli():
        print_red("Critical dependency 'gemini' missing and could not be installed. Setup stopped.")
        sys.exit(1)

    print_cyan("Step 3: Configuring project context...")
    configure_settings(project_root)
    create_system_prompt(project_root)
    create_launchers(project_root)

    print_green("\nSetup successfully completed!")

if __name__ == "__main__":
    main()
