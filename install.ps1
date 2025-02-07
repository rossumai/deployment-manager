# Ensure Git & Pipx exist
if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
    Write-Host "Installing pipx..."
    winget install pypa.pipx --silent --accept-package-agreements
}

# Clone and install
git clone https://github.com/rossumai/deployment-manager.git
cd deployment-manager
pipx install .
