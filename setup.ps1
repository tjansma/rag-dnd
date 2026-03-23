# Setup script for rag-dnd on Windows (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "--- rag-dnd Setup ---" -ForegroundColor Cyan

# 1. Check for uv
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Installing uv..." -ForegroundColor Yellow
    # Using the canonical installation command for Windows
    Invoke-RestMethod -Uri https://astral.sh/uv/install.ps1 | Invoke-Expression
    # Add to current path for immediate use
    $env:PATH += ";$HOME\.local\bin"
} else {
    Write-Host "uv is already installed." -ForegroundColor Green
}

# 2. Check for node/npm (needed for Gemini CLI)
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "Warning: npm not found. Gemini CLI installation might fail." -ForegroundColor Red
    Write-Host "Please install Node.js (https://nodejs.org/) and run this script again." -ForegroundColor Yellow
}

# 3. Run the main install script via uv
Write-Host "Running project setup with uv..." -ForegroundColor Cyan
uv run scripts/install.py

Write-Host "--- Setup Complete ---" -ForegroundColor Green
Write-Host "You can now use 'rag-gemini.bat' to start the Gemini CLI with rag-dnd context."
