#!/bin/sh
# Builds a self-contained prd2 bundle for Windows x64 on macOS (or Linux): its own Python,
# all dependencies and Git for Windows. Users unzip it and run install.cmd inside.
#
#   standalone/windows/build.sh
#
# Writes dist/prd2-<version>-windows-x64.zip (+ .sha256). Needs git and access to github.com and pypi.org.
# Windows programs cannot run here, so the bundle is only checked file by file; smoke-test.ps1 tests it on Windows.
# Pin the inputs with PYTHON_RELEASE (python-build-standalone tag, e.g. 20250918)
# and GIT_RELEASE (Git for Windows tag, e.g. v2.51.0.windows.1).

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
. "$SCRIPT_DIR/../common.sh"

TARGET_TRIPLE="x86_64-pc-windows-msvc"
# Same uv as install.sh. Unlike pip, it resolves dependencies for another platform (e.g., click's colorama on Windows).
UV_VERSION="0.13.1"

REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
BUILD_DIR="$REPO_DIR/build/windows"
DOWNLOADS="$BUILD_DIR/downloads"
HOST_DIR="$BUILD_DIR/host"
STAGE="$BUILD_DIR/bundle"
DIST_DIR="$REPO_DIR/dist"

# Python and uv for this machine, which do the building.
fetch_host_tools() {
    fetch_python "$HOST_TRIPLE" "$HOST_DIR"
    HOST_PY="$HOST_DIR/python/bin/python3"

    uv_archive="$DOWNLOADS/uv-$UV_VERSION-$HOST_TRIPLE.tar.gz"
    uv_url="https://github.com/astral-sh/uv/releases/download/$UV_VERSION/uv-$HOST_TRIPLE.tar.gz"
    say "Downloading uv $UV_VERSION"
    download "$uv_url" "$uv_archive"
    curl -fsSL "$uv_url.sha256" -o "$DOWNLOADS/uv.sha256" || fail "Could not download $uv_url.sha256"
    verify_sha256 "$uv_archive" "$(cut -d ' ' -f 1 "$DOWNLOADS/uv.sha256")"
    mkdir -p "$HOST_DIR/uv"
    tar -xzf "$uv_archive" -C "$HOST_DIR/uv" --strip-components 1
    UV="$HOST_DIR/uv/uv"
}

install_prd2() {
    say "Building the deployment-manager wheel"
    "$HOST_PY" -I -m pip wheel --quiet --no-deps --wheel-dir "$BUILD_DIR/wheel" "$REPO_DIR"
    wheel="$(ls "$BUILD_DIR"/wheel/deployment_manager-*.whl)"
    VERSION="$(basename "$wheel" | cut -d - -f 2)"

    "$HOST_PY" -I "$SCRIPT_DIR/../lock_to_constraints.py" "$REPO_DIR/poetry.lock" >"$BUILD_DIR/constraints.txt"

    # Installs Windows wheels into the Windows Python; uv evaluates the dependencies' platform markers for Windows.
    say "Installing deployment-manager $VERSION and its dependencies for Windows"
    SITE_PACKAGES="$STAGE/python/Lib/site-packages"
    mkdir -p "$SITE_PACKAGES"
    UV_CACHE_DIR="$BUILD_DIR/uv-cache" UV_PYTHON_DOWNLOADS=never "$UV" pip install --quiet \
        --python "$HOST_PY" --target "$SITE_PACKAGES" \
        --python-platform "$TARGET_TRIPLE" --python-version "$PYTHON_VERSION" \
        --only-binary :all: --link-mode copy --constraint "$BUILD_DIR/constraints.txt" "$wheel"
    # Entry-point launchers are not needed; prd2 has its own.
    rm -rf "$SITE_PACKAGES/bin" "$SITE_PACKAGES/Scripts"

    # Hash-checked .pyc files stay valid after unzipping, which shifts file times (zip stores local time, 2 s precision).
    "$HOST_PY" -I -m compileall -q --invalidation-mode checked-hash "$SITE_PACKAGES" >/dev/null ||
        say "Some files could not be precompiled; Python compiles them on first use."
}

fetch_git() {
    github_release_json "git-for-windows/git" "${GIT_RELEASE:-}" >"$BUILD_DIR/git-release.json"
    # The .tar.bz2 holds the same files as the installer and, unlike PortableGit's .7z.exe, unpacks without Windows.
    asset="$("$HOST_PY" -I "$SCRIPT_DIR/../release_asset.py" "$BUILD_DIR/git-release.json" 'Git-[0-9.]+-64-bit\.tar\.bz2')"
    [ -n "$asset" ] || fail "No Git-<version>-64-bit.tar.bz2 in Git for Windows ${GIT_RELEASE:-latest}."
    git_name="${asset%% *}"
    rest="${asset#* }"
    git_url="${rest%% *}"
    git_sha="${rest#* }"
    GIT_VERSION="$(printf '%s' "$git_name" | sed 's/^Git-\(.*\)-64-bit\.tar\.bz2$/\1/')"

    say "Downloading $git_name"
    download "$git_url" "$DOWNLOADS/$git_name"
    verify_sha256 "$DOWNLOADS/$git_name" "$git_sha"

    rm -rf "$BUILD_DIR/git-unpacked"
    mkdir -p "$BUILD_DIR/git-unpacked"
    tar -xjf "$DOWNLOADS/$git_name" -C "$BUILD_DIR/git-unpacked"
    # Git's root is wherever cmd/git.exe is, whether or not the archive has a top-level folder.
    git_exe="$(find "$BUILD_DIR/git-unpacked" -maxdepth 3 -path '*/cmd/git.exe' | head -n 1)"
    [ -n "$git_exe" ] || fail "$git_name has no cmd/git.exe."
    mv "$(dirname "$(dirname "$git_exe")")" "$STAGE/git"
}

# What can be checked without running Windows programs.
check_bundle() {
    # sh and sed run prd2's modified_by git filter.
    for file in python/python.exe python/Lib/site-packages/deployment_manager/main.py \
        git/cmd/git.exe git/usr/bin/sh.exe git/usr/bin/sed.exe prd2.cmd install.cmd install.ps1; do
        [ -f "$STAGE/$file" ] || fail "The bundle has no $file."
    done
    native_for_build_machine="$(find "$SITE_PACKAGES" \( -name '*.so' -o -name '*.dylib' \) | head -n 3)"
    [ -z "$native_for_build_machine" ] || fail "Packages for the build machine instead of Windows got installed: $native_for_build_machine"
}

main() {
    case "$(uname -s)-$(uname -m)" in
        Darwin-arm64) HOST_TRIPLE="aarch64-apple-darwin" ;;
        Darwin-x86_64) HOST_TRIPLE="x86_64-apple-darwin" ;;
        Linux-x86_64) HOST_TRIPLE="x86_64-unknown-linux-gnu" ;;
        Linux-aarch64) HOST_TRIPLE="aarch64-unknown-linux-gnu" ;;
        *) fail "Unsupported build machine: $(uname -s) $(uname -m)" ;;
    esac
    command -v git >/dev/null 2>&1 || fail "git is needed: the wheel's version is computed from git tags."
    command -v zip >/dev/null 2>&1 || fail "zip is needed to pack the bundle."
    ignore_user_package_config

    rm -rf "$STAGE" "$HOST_DIR" "$BUILD_DIR/wheel"
    mkdir -p "$STAGE" "$HOST_DIR" "$DOWNLOADS" "$DIST_DIR"

    fetch_host_tools
    # Last, so PYTHON_VERSION is the bundled one.
    fetch_python "$TARGET_TRIPLE" "$STAGE"
    install_prd2
    fetch_git

    for file in prd2.cmd install.cmd install.ps1; do
        # CRLF line endings, which cmd.exe expects, whatever git's checkout settings were.
        tr -d '\r' <"$SCRIPT_DIR/$file" | awk '{ printf "%s\r\n", $0 }' >"$STAGE/$file"
    done
    cat >"$STAGE/prd2-bundle.json" <<EOF
{"version": "$VERSION", "platform": "windows-x64", "python": "$PYTHON_VERSION", "git": "$GIT_VERSION"}
EOF

    say "Checking the bundle"
    check_bundle

    name="prd2-$VERSION-windows-x64"
    rm -rf "${BUILD_DIR:?}/$name"
    mv "$STAGE" "$BUILD_DIR/$name"

    archive="$DIST_DIR/$name.zip"
    rm -f "$archive"
    # -X leaves out Unix owners and permissions, which mean nothing on Windows.
    (cd "$BUILD_DIR" && zip -qrX "$archive" "$name")
    printf '%s  %s\n' "$(file_sha256 "$archive")" "$name.zip" >"$archive.sha256"

    say "Built $archive ($(du -h "$archive" | cut -f 1)): Python $PYTHON_VERSION, Git for Windows $GIT_VERSION"
    say "Test it on Windows: powershell -ExecutionPolicy Bypass -File standalone\\windows\\smoke-test.ps1 <unzipped folder>"
}

main "$@"
