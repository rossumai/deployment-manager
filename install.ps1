# One-command installer for the Rossum deployment manager (prd2) on Windows.
#
#   powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/rossumai/deployment-manager/main/install.ps1 | iex"
#
# Install a specific version by setting PRD_VERSION first:
#
#   $env:PRD_VERSION = "v2.7.0a"; irm https://raw.githubusercontent.com/rossumai/deployment-manager/main/install.ps1 | iex
#
# Uses uv (https://docs.astral.sh/uv/), which brings its own Python 3.12 and
# keeps prd2 in an isolated environment, so nothing else needs to be installed.
# Safe to re-run: it upgrades an existing installation.

$ErrorActionPreference = "Stop"

$Repo = "rossumai/deployment-manager"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Git is missing. Installing it via winget..."
        winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
        $env:Path = "$env:ProgramFiles\Git\cmd;$env:Path"
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Host "Error: Git is required but not installed." -ForegroundColor Red
        Write-Host "Install it from https://git-scm.com/downloads/win, then open a new terminal and run this installer again."
        return
    }
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv (Python package manager)..."
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "Error: uv was installed but could not be found. Open a new terminal and run this installer again." -ForegroundColor Red
        return
    }
}

if ($env:PRD_VERSION) {
    $ApiUrl = "https://api.github.com/repos/$Repo/releases/tags/$env:PRD_VERSION"
} else {
    $ApiUrl = "https://api.github.com/repos/$Repo/releases/latest"
}

Write-Host "Looking up the release..."
try {
    $Release = Invoke-RestMethod -Uri $ApiUrl
} catch {
    Write-Host "Error: Could not find the release ($ApiUrl)." -ForegroundColor Red
    return
}
$WheelUrl = $Release.assets | Where-Object { $_.name -like "*.whl" } | Select-Object -First 1 -ExpandProperty browser_download_url
if (-not $WheelUrl) {
    Write-Host "Error: No installable release found." -ForegroundColor Red
    return
}

Write-Host "Installing $WheelUrl"
uv tool install --force --python 3.12 $WheelUrl
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: installation failed." -ForegroundColor Red
    return
}

# Adds uv's tool directory to the user PATH if it is not there yet.
uv tool update-shell 2>$null | Out-Null

Write-Host ""
Write-Host "Done! Open a NEW terminal window and run:  prd2 --help"
