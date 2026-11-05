# Helpers shared by the bundle build scripts (macos/build.sh, windows/build.sh). Sourced, not run.

PBS_REPO="astral-sh/python-build-standalone"

say() { printf '==> %s\n' "$*"; }
fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }

# Prints the SHA-256 of a file (sha256sum on Linux, shasum on macOS).
file_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | cut -d ' ' -f 1
    else
        shasum -a 256 "$1" | cut -d ' ' -f 1
    fi
}

# $1 = file, $2 = expected SHA-256
verify_sha256() {
    [ -n "$2" ] || fail "No published checksum found for $(basename "$1")."
    expected="$(printf '%s' "$2" | tr 'A-F' 'a-f')"
    actual="$(file_sha256 "$1")"
    [ "$actual" = "$expected" ] || fail "Checksum mismatch for $(basename "$1"): expected $expected, got $actual."
}

# $1 = URL, $2 = destination; reuses earlier downloads (they are verified again anyway).
download() {
    [ -f "$2" ] || curl -fsSL "$1" -o "$2.part" || fail "Could not download $1"
    [ -f "$2" ] || mv "$2.part" "$2"
}

# Ignores the builder's pip and uv settings (e.g., private indexes); everything in poetry.lock comes from PyPI.
ignore_user_package_config() {
    for var in $(env | sed -nE 's/^((PIP|UV)_[A-Za-z0-9_]*)=.*/\1/p'); do
        unset "$var"
    done
    export PIP_CONFIG_FILE=/dev/null UV_NO_CONFIG=1
}

# $1 = owner/repo, $2 = release tag (empty for the latest); prints the release JSON from the GitHub API.
github_release_json() {
    if [ -n "$2" ]; then
        api_url="https://api.github.com/repos/$1/releases/tags/$2"
    else
        api_url="https://api.github.com/repos/$1/releases/latest"
    fi
    curl -fsSL ${GITHUB_TOKEN:+-H "Authorization: Bearer $GITHUB_TOKEN"} "$api_url" ||
        fail "Could not look up the release ($api_url)."
}

# Downloads python-build-standalone's Python 3.12 for target triple $1 and unpacks it into $2 (as $2/python).
# Pinned with PYTHON_RELEASE; sets PYTHON_VERSION.
fetch_python() {
    release_json="$(github_release_json "$PBS_REPO" "${PYTHON_RELEASE:-}")"

    # Download URLs encode the "+" of asset names (cpython-3.12.11+20250918-...) as %2B.
    asset_re="cpython-3\.12\.[0-9]+(\+|%2B)[0-9]+-$1-install_only_stripped\.tar\.gz"
    python_url="$(printf '%s' "$release_json" | grep -oE "\"browser_download_url\": *\"[^\"]*/$asset_re\"" | head -n 1 | sed 's/.*: *"\(.*\)"/\1/')"
    sums_url="$(printf '%s' "$release_json" | grep -o '"browser_download_url": *"[^"]*/SHA256SUMS"' | head -n 1 | sed 's/.*: *"\(.*\)"/\1/')"
    [ -n "$python_url" ] || fail "No Python 3.12 build for $1 in python-build-standalone ${PYTHON_RELEASE:-latest}."
    [ -n "$sums_url" ] || fail "No SHA256SUMS published in python-build-standalone ${PYTHON_RELEASE:-latest}."

    asset_name="$(printf '%s' "${python_url##*/}" | sed 's/%2B/+/g')"
    python_tarball="$DOWNLOADS/$asset_name"
    say "Downloading $asset_name"
    download "$python_url" "$python_tarball"
    curl -fsSL "$sums_url" -o "$DOWNLOADS/SHA256SUMS" || fail "Could not download $sums_url"
    verify_sha256 "$python_tarball" "$(awk -v name="$asset_name" '$2 == name { print $1 }' "$DOWNLOADS/SHA256SUMS")"

    tar -xzf "$python_tarball" -C "$2"
    PYTHON_VERSION="$(printf '%s' "$asset_name" | sed 's/^cpython-\([0-9.]*\)+.*/\1/')"
}
