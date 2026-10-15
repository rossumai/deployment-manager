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
DOWNLOAD_PREFIX="https://github.com/$REPO/releases/download/"

# uv version used when this installer has to install uv itself. Bumped manually;
# it does not affect an already installed uv.
UV_VERSION="0.13.1"

say() { printf '%s\n' "$*"; }
fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }

# The tag ends up in a URL, so accept only things that look like a version tag.
validate_tag() {
    case "$1" in
        "") ;;
        v[0-9]*) case "$1" in *[!A-Za-z0-9._-]*) fail "Invalid version tag: $1" ;; esac ;;
        *) fail "Invalid version tag: $1" ;;
    esac
}

# Only ever download release assets from this repository.
require_release_url() {
    case "$1" in
        "$DOWNLOAD_PREFIX"*) ;;
        *) fail "Unexpected download URL: $1" ;;
    esac
}

# Prints the SHA-256 of a file (sha256sum on Linux, shasum on macOS).
file_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | cut -d ' ' -f 1
    else
        shasum -a 256 "$1" | cut -d ' ' -f 1
    fi
}

# $1 = wheel, $2 = .sha256 file in `sha256sum` format ("<hash>  <filename>").
verify_checksum() {
    expected="$(cut -d ' ' -f 1 "$2" | tr 'A-F' 'a-f')"
    actual="$(file_sha256 "$1" | tr 'A-F' 'a-f')"
    [ -n "$expected" ] || fail "The checksum file is empty."
    [ "$expected" = "$actual" ] || fail "Checksum mismatch for $(basename "$1"): expected $expected, got $actual. Aborting."
}

main() {
    TAG="${1:-}"
    validate_tag "$TAG"

    # Needed to verify the download; checked here so it fails before anything is installed.
    if ! command -v sha256sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then
        fail "Neither sha256sum nor shasum is available to verify the download."
    fi

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
        say "Installing uv $UV_VERSION (Python package manager). Its installer may add uv to your shell profile (PATH)."
        curl -LsSf "https://astral.sh/uv/$UV_VERSION/install.sh" | sh
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
    SHA_URL="$(printf '%s' "$RELEASE_JSON" | grep -o '"browser_download_url": *"[^"]*\.whl\.sha256"' | head -n 1 | sed 's/.*: *"\(.*\)"/\1/')"
    [ -n "$SHA_URL" ] || fail "Refusing to install: no checksum published for this release."
    require_release_url "$WHEEL_URL"
    require_release_url "$SHA_URL"

    # The wheel keeps its original filename because uv validates it.
    TMP_DIR="$(mktemp -d)"
    trap 'rm -rf "$TMP_DIR"' EXIT
    trap 'exit 1' INT TERM HUP
    WHEEL_FILE="$TMP_DIR/${WHEEL_URL##*/}"
    SHA_FILE="$TMP_DIR/checksum.sha256"

    say "Downloading $WHEEL_URL"
    curl -fsSL "$WHEEL_URL" -o "$WHEEL_FILE" || fail "Could not download the wheel."
    curl -fsSL "$SHA_URL" -o "$SHA_FILE" || fail "Could not download the checksum."
    verify_checksum "$WHEEL_FILE" "$SHA_FILE"
    say "Checksum OK."

    uv tool install --force --python 3.12 "$WHEEL_FILE"

    # Adds uv's tool directory to the shell profile if it is not on PATH yet.
    uv tool update-shell >/dev/null 2>&1 || true

    say ""
    say "Done! Open a NEW terminal window and run:  prd2 --help"
}

main "$@"
