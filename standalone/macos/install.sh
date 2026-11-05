#!/bin/sh
# Installs this prd2 bundle for the current user. Works offline.
#
#   sh install.sh
#
# Copies the bundle to ~/.local/share/prd2 and links ~/.local/bin/prd2 to it.
# Safe to re-run: it replaces the previously installed bundle.

set -eu

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd -P)"
INSTALL_DIR="$HOME/.local/share/prd2"
BIN_DIR="$HOME/.local/bin"

say() { printf '%s\n' "$*"; }

if [ "$SOURCE_DIR" != "$INSTALL_DIR" ]; then
    # Copy next to the old bundle first, so a failed copy leaves the old one working.
    mkdir -p "$(dirname "$INSTALL_DIR")"
    rm -rf "$INSTALL_DIR.new"
    cp -R "$SOURCE_DIR" "$INSTALL_DIR.new"
    rm -rf "$INSTALL_DIR"
    mv "$INSTALL_DIR.new" "$INSTALL_DIR"
fi

# Browsers quarantine downloads, and Gatekeeper would then refuse to run the bundled binaries.
xattr -dr com.apple.quarantine "$INSTALL_DIR" 2>/dev/null || true

mkdir -p "$BIN_DIR"
if [ -e "$BIN_DIR/prd2" ] && [ "$(readlink "$BIN_DIR/prd2")" != "$INSTALL_DIR/prd2" ]; then
    say "Replacing the existing $BIN_DIR/prd2 (e.g., an installation made with uv)."
fi
ln -sf "$INSTALL_DIR/prd2" "$BIN_DIR/prd2"

case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
        PROFILE="$HOME/.zshrc"
        PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
        if ! grep -qsF "$PATH_LINE" "$PROFILE"; then
            printf '\n%s\n' "$PATH_LINE" >>"$PROFILE"
            say "Added ~/.local/bin to your PATH in $PROFILE."
        fi
        ;;
esac

say "Installed $("$INSTALL_DIR/prd2" --version) to $INSTALL_DIR"
say "Open a NEW terminal window and run:  prd2 --help"
