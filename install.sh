#!/usr/bin/env bash

PRD_GIT_URL="https://github.com/rossumai/deployment-manager.git"

# Detect OS
OS=$(uname -s)

# Function to check if Python 3.12 is installed and find its path
find_python312() {
    if command -v python3.12 &>/dev/null; then
        PYTHON312_PATH=$(command -v python3.12)
        return 0
    else
        return 1
    fi
}

# Function to refresh shell environment for pipx
refresh_shell() {
    echo "Refreshing shell to apply pipx changes..."
    eval "$PYTHON312_PATH -m pipx ensurepath"
    export PATH="$HOME/.local/bin:$PATH"
    hash -r  # Refresh shell command cache
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
    if ! find_python312; then
        echo "Installing Python 3.12..."
        brew install python@3.12
        brew link --force --overwrite python@3.12
        PYTHON312_PATH=$(brew --prefix python@3.12)/bin/python3.12
    fi

else
    # Linux-specific setup
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        if [[ "$ID_LIKE" == "debian" || "$ID" == "ubuntu" ]]; then
            sudo apt update
            sudo apt install -y git software-properties-common

            if ! find_python312; then
                echo "Installing Python 3.12..."
                sudo add-apt-repository ppa:deadsnakes/ppa -y
                sudo apt update
                sudo apt install -y python3.12 python3.12-venv python3.12-distutils
                PYTHON312_PATH=$(which python3.12)
            fi

            # Ensure python3 points to python3.12
            sudo update-alternatives --install /usr/bin/python3 python3 "$PYTHON312_PATH" 1
            sudo update-alternatives --set python3 "$PYTHON312_PATH"

        elif [[ "$ID_LIKE" == "rhel fedora" || "$ID" == "fedora" ]]; then
            sudo dnf install -y git

            if ! find_python312; then
                echo "Installing Python 3.12..."
                sudo dnf install -y python3.12
                PYTHON312_PATH=$(which python3.12)
            fi

            # Ensure python3 points to python3.12
            sudo alternatives --install /usr/bin/python3 python3 "$PYTHON312_PATH" 1
            sudo alternatives --set python3 "$PYTHON312_PATH"

        elif [[ "$ID_LIKE" == "arch" || "$ID" == "arch" ]]; then
            sudo pacman -Sy --noconfirm git

            if ! find_python312; then
                echo "Installing Python 3.12..."
                sudo pacman -Sy --noconfirm python
                PYTHON312_PATH=$(which python3)
            fi
        else
            echo "Unsupported Linux distribution. Install Python 3.12 manually."
            exit 1
        fi
    fi
fi

# Ensure pipx is installed for Python 3.12
if ! "$PYTHON312_PATH" -m pip show pipx &>/dev/null; then
    echo "Installing pipx for Python 3.12..."
    "$PYTHON312_PATH" -m ensurepip --upgrade
    "$PYTHON312_PATH" -m pip install --user --force-reinstall pipx
    refresh_shell
fi

# Ensure pipx works after installation
if ! command -v pipx &> /dev/null; then
    echo "pipx not found after installation. Adding it to PATH manually."
    export PATH="$HOME/.local/bin:$PATH"
    hash -r  # Refresh shell command cache
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

# Install Deployment Manager using Python 3.12 explicitly
"$PYTHON312_PATH" -m pipx install . --force
