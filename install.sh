#!/usr/bin/env bash

PRD_GIT_URL="https://github.com/rossumai/deployment-manager.git"

# Detect OS
OS=$(uname -s)

# Function to check Python version
check_python_version() {
    if command -v python3 &>/dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
        if [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -ge 12 ]]; then
            return 0  # Python version is valid
        fi
    fi
    return 1  # Python version is too old or not found
}

# macOS-specific setup
if [[ "$OS" == "Darwin" ]]; then
    # Ensure Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found, installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    # Ensure Git is installed
    if ! command -v git &> /dev/null; then
        echo "Git not found, installing via Homebrew..."
        brew install git
    fi

    # Ensure correct Python version is installed
    if ! check_python_version; then
        echo "Installing/Upgrading Python to 3.12+..."
        brew install python@3.12
        brew link --force --overwrite python@3.12
    fi

    # Ensure pipx is installed
    if ! command -v pipx &> /dev/null; then
        echo "pipx not found, installing via Homebrew..."
        brew install pipx
        pipx ensurepath
    fi
else
    # Linux-specific setup
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        if [[ "$ID_LIKE" == "debian" || "$ID" == "ubuntu" ]]; then
            sudo apt update
            sudo apt install -y git software-properties-common
            if ! check_python_version; then
                echo "Adding PPA and Installing Python 3.12..."
                sudo add-apt-repository ppa:deadsnakes/ppa -y
                sudo apt update
                sudo apt install -y python3.12 python3.12-venv python3.12-distutils
                sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
            fi
        elif [[ "$ID_LIKE" == "rhel fedora" || "$ID" == "fedora" ]]; then
            sudo dnf install -y git
            if ! check_python_version; then
                echo "Installing Python 3.12..."
                sudo dnf install -y python3.12
                sudo alternatives --set python3 /usr/bin/python3.12
            fi
        elif [[ "$ID_LIKE" == "arch" || "$ID" == "arch" ]]; then
            sudo pacman -Sy --noconfirm git
            if ! check_python_version; then
                echo "Installing Python 3.12..."
                sudo pacman -Sy --noconfirm python
            fi
        else
            echo "Unsupported Linux distribution. Install Python 3.12 manually."
            exit 1
        fi
    fi

    # Install pipx if missing
    if ! command -v pipx &> /dev/null; then
        echo "pipx not found, installing..."
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    fi
fi

# Clone repository
TEMP_GIT_DIR=$(mktemp -d)
cd "$TEMP_GIT_DIR" || { echo "Failed to change directory"; exit 1; }
git clone "$PRD_GIT_URL"
cd deployment-manager || { echo "Failed to enter repository directory"; exit 1; }

# Checkout specified branch if provided
if [ -n "$BRANCH" ]; then
    git checkout "$BRANCH"
fi

# Install Deployment Manager
pipx install . --force
