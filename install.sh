#!/usr/bin/env bash

PRD_GIT_URL=https://github.com/rossumai/deployment-manager.git

# Ensure Homebrew is installed (required for installing Git and pipx)
if ! command -v brew &> /dev/null
then
    echo "Homebrew not found, installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Ensure Git is installed
if ! command -v git &> /dev/null
then
    echo "Git not found, installing..."
    brew install git
fi

# Create a temporary directory for cloning the repository
TEMP_GIT_DIR=$(mktemp -d)

cd "$TEMP_GIT_DIR" || { echo "Failed to change directory"; exit 1; }

git clone "$PRD_GIT_URL"

cd deployment-manager || { echo "Failed to enter repository directory"; exit 1; }

# Checkout specified branch if provided
if [ -n "$BRANCH" ]
then
    git checkout "$BRANCH"
fi

# Ensure pipx is installed
if ! command -v pipx &> /dev/null
then
    echo "pipx not found, attempting install..."
    brew install pipx
    pipx ensurepath
fi   

# Install Deployment Manager
pipx install . --force
