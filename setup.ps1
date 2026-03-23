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
}
else {
    Write-Host "uv is already installed." -ForegroundColor Green
}

# 2. Check for node/npm (needed for Gemini CLI)
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "npm not found. Installing npm..." -ForegroundColor Yellow
    winget install --disable-interactivity --accept-source-agreements --accept-package-agreements OpenJS.NodeJS
    # Add to current path for immediate use
    $env:PATH += ";c:\Program Files\nodejs"
}
else {
    Write-Host "npm is already installed." -ForegroundColor Green
}

# 3. Check for Gemini CLI
if (!(Get-Command gemini -ErrorAction SilentlyContinue)) {
    Write-Host "Gemini CLI not found. Installing Gemini CLI..." -ForegroundColor Yellow
    npm install -g @google/gemini-cli
}
else {
    Write-Host "Gemini CLI is already installed." -ForegroundColor Green
}

# 4. Run the main install script via uv
Write-Host "Running project setup with uv..." -ForegroundColor Cyan
uv run scripts/install.py

Write-Host "--- Setup Complete ---" -ForegroundColor Green
Write-Host "You can now use 'rag-gemini.bat' to start the Gemini CLI with rag-dnd context."
