# Setup script for rag-dnd on Windows (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "--- rag-dnd Setup ---" -ForegroundColor Cyan

# 0. Check for Microsoft Visual C++ Redistributable (Required for PyTorch)
Write-Host "Checking for Microsoft Visual C++ Redistributable..." -ForegroundColor Cyan
winget install --id Microsoft.VCRedist.2015+.x64 --source winget --disable-interactivity --accept-source-agreements --accept-package-agreements

# Function to persistently add a path to the User environment
function Add-PersistentPath ($newPath) {
    if (-not (Test-Path $newPath)) { return }
    $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -split ";" -notcontains $newPath) {
        $sep = if ($currentPath -and !$currentPath.EndsWith(";")) { ";" } else { "" }
        $updatedPath = $currentPath + $sep + $newPath
        [System.Environment]::SetEnvironmentVariable("Path", $updatedPath, "User")
        Write-Host "Added $newPath to persistent User PATH." -ForegroundColor Green
    }
}

# 1. Check for uv
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Installing uv..." -ForegroundColor Yellow
    # Using the canonical installation command for Windows
    Invoke-RestMethod -Uri https://astral.sh/uv/install.ps1 | Invoke-Expression
    
    # Persistent update
    $uvPath = "$HOME\.local\bin"
    Add-PersistentPath $uvPath
    # Session update
    $env:PATH += ";$uvPath"
}
else {
    Write-Host "uv is already installed." -ForegroundColor Green
}

# 2. Check for node/npm (needed for Gemini CLI)
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "npm not found. Installing Node.js via winget..." -ForegroundColor Yellow
    winget install --id OpenJS.NodeJS --source winget --disable-interactivity --accept-source-agreements --accept-package-agreements
    
    # Refresh session PATH from registry
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}
else {
    Write-Host "npm is already installed." -ForegroundColor Green
}

# 3. Check for Gemini CLI
if (!(Get-Command gemini -ErrorAction SilentlyContinue)) {
    Write-Host "Gemini CLI not found. Installing Gemini CLI..." -ForegroundColor Yellow
    npm install -g @google/gemini-cli
    
    # Add npm global bin to PATH
    $npmConfigPrefix = (npm config get prefix).Trim()
    if ($npmConfigPrefix) {
        Add-PersistentPath $npmConfigPrefix
        $env:PATH += ";$npmConfigPrefix"
    } else {
        # Fallback to common Windows npm path
        $npmFallback = "$env:APPDATA\npm"
        Add-PersistentPath $npmFallback
        $env:PATH += ";$npmFallback"
    }
}
else {
    Write-Host "Gemini CLI is already installed." -ForegroundColor Green
}

# 4. Run the main install script via uv
Write-Host "Running project setup with uv..." -ForegroundColor Cyan
# Pass the current session's PATH to the child process to ensure it sees newly installed tools
$env:PYTHONUNBUFFERED = "1"
uv run scripts/install.py

Write-Host "--- Setup Complete ---" -ForegroundColor Green
Write-Host "You can now use 'rag-gemini.bat' to start the Gemini CLI with rag-dnd context."
