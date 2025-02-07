#!/usr/bin/env sh

# Detect if running in PowerShell
if [ -z "$PSModulePath" ]; then
    # Bash Section
    echo "Running in Bash"

    PRD_GIT_URL=https://github.com/rossumai/deployment-manager.git
    TEMP_GIT_DIR=$(mktemp -d)

    cd "$TEMP_GIT_DIR" || exit
    git clone "$PRD_GIT_URL"
    cd deployment-manager || exit

    if [ -n "$BRANCH" ]; then
        git checkout "$BRANCH"
    fi

    if ! command -v pipx &> /dev/null; then
        echo 'pipx not found, attempting install...'
        if command -v brew &> /dev/null; then
            brew install pipx
        else
            echo 'brew not found, please install pipx manually'
            exit 1
        fi
    fi

    pipx install . --force

else
    # PowerShell Section
    echo "Running in PowerShell"

    $PRD_GIT_URL = "https://github.com/rossumai/deployment-manager.git"
    $TEMP_GIT_DIR = [System.IO.Path]::GetTempPath() + [System.IO.Path]::GetRandomFileName()
    New-Item -ItemType Directory -Path $TEMP_GIT_DIR | Out-Null

    Set-Location -Path $TEMP_GIT_DIR
    git clone $PRD_GIT_URL
    Set-Location -Path "$TEMP_GIT_DIR\deployment-manager"

    if ($env:BRANCH) {
        git checkout $env:BRANCH
    }

    if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
        Write-Host 'pipx not found, attempting install...'
        if (Get-Command brew -ErrorAction SilentlyContinue) {
            brew install pipx
        } else {
            Write-Host 'brew not found, please install pipx manually'
            exit 1
        }
    }

    pipx install . --force
fi
