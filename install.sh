#!/bin/sh
# One-command installer for the Rossum deployment manager (prd2) on macOS/Linux.
#
#   curl -LsSf https://raw.githubusercontent.com/rossumai/deployment-manager/main/install.sh | sh
#
# Install a specific version by passing its tag:
#
#   curl -LsSf https://raw.githubusercontent.com/rossumai/deployment-manager/main/install.sh | sh -s -- v2.7.0a
#
# Uses `uv` (https://docs.astral.sh/uv/), which brings its own Python 3.12 and
# keeps prd2 in an isolated environment, so nothing else needs to be installed.
# Safe to re-run: it upgrades an existing installation.

set -eu

REPO="rossumai/deployment-manager"
TAG="${1:-}"

say() { printf '%s\n' "$*"; }
fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }

# On a fresh Mac /usr/bin/git is a stub, so `command -v` is not enough: run it.
if ! git --version >/dev/null 2>&1; then
    case "$(uname -s)" in
        Darwin)
            say "Git is missing. Opening the macOS installer for the Command Line Tools..."
            xcode-select --install >/dev/null 2>&1 || true
            fail "Click 'Install' in the dialog, wait for it to finish, then run this installer again."
            ;;
        *) fail "Git is required but not installed. Install it with your package manager (e.g., 'sudo apt install git'), then run this installer again." ;;
    esac
fi

if ! command -v uv >/dev/null 2>&1; then
    say "Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    export PATH
    command -v uv >/dev/null 2>&1 || fail "uv was installed but could not be found on PATH. Open a new terminal and run this installer again."
fi

if [ -n "$TAG" ]; then
    API_URL="https://api.github.com/repos/$REPO/releases/tags/$TAG"
else
    API_URL="https://api.github.com/repos/$REPO/releases/latest"
fi

say "Looking up the release..."
RELEASE_JSON="$(curl -fsSL "$API_URL")" || fail "Could not find the release${TAG:+ $TAG} on GitHub."
WHEEL_URL="$(printf '%s' "$RELEASE_JSON" | grep -o '"browser_download_url": *"[^"]*\.whl"' | head -n 1 | sed 's/.*: *"\(.*\)"/\1/')"
[ -n "$WHEEL_URL" ] || fail "No installable release found${TAG:+ for tag $TAG}."

say "Installing $WHEEL_URL"
uv tool install --force --python 3.12 "$WHEEL_URL"

# Adds uv's tool directory to the shell profile if it is not on PATH yet.
uv tool update-shell >/dev/null 2>&1 || true

say ""
say "Done! Open a NEW terminal window and run:  prd2 --help"
