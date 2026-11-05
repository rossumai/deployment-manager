#!/bin/sh
# Builds a self-contained prd2 bundle for macOS: its own Python, all dependencies and git.
# Users unpack it and run install.sh inside; nothing is downloaded at install time.
#
#   standalone/macos/build.sh
#
# Writes dist/prd2-<version>-macos-<arch>.tar.gz (+ .sha256) for this machine's architecture.
# Needs Xcode Command Line Tools (to compile git) and access to github.com, pypi.org and kernel.org.
# Pin the inputs with PYTHON_RELEASE (python-build-standalone tag, e.g. 20250918) and GIT_VERSION (e.g. 2.51.0).

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
. "$SCRIPT_DIR/../common.sh"

GIT_MIRROR="https://mirrors.edge.kernel.org/pub/software/scm/git"
# Oldest macOS the bundle supports. 14.0 because ruamel.yaml.clib 0.2.12 has no older Apple Silicon wheel.
MACOS_MIN="14.0"
export MACOSX_DEPLOYMENT_TARGET="$MACOS_MIN"

REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
BUILD_DIR="$REPO_DIR/build/macos"
DOWNLOADS="$BUILD_DIR/downloads"
STAGE="$BUILD_DIR/bundle"
DIST_DIR="$REPO_DIR/dist"

install_prd2() {
    py="$STAGE/python/bin/python3"
    # pip must not refuse to install into the bundled interpreter
    rm -f "$STAGE"/python/lib/python3.*/EXTERNALLY-MANAGED
    "$py" -I -m pip --version >/dev/null 2>&1 || "$py" -I -m ensurepip >/dev/null

    say "Building the deployment-manager wheel"
    rm -rf "$BUILD_DIR/wheel"
    "$py" -I -m pip wheel --quiet --no-deps --wheel-dir "$BUILD_DIR/wheel" "$REPO_DIR"
    wheel="$(ls "$BUILD_DIR"/wheel/deployment_manager-*.whl)"
    VERSION="$(basename "$wheel" | cut -d - -f 2)"

    "$py" -I "$REPO_DIR/standalone/lock_to_constraints.py" "$REPO_DIR/poetry.lock" >"$BUILD_DIR/constraints.txt"

    # Left alone, pip picks wheels for the build machine's own macOS, which can be newer than MACOS_MIN.
    say "Downloading dependencies for macOS $MACOS_MIN+"
    rm -rf "$BUILD_DIR/wheelhouse"
    "$py" -I -m pip download --quiet --only-binary=:all: --platform "macosx_$(echo "$MACOS_MIN" | tr . _)_$ARCH" \
        --constraint "$BUILD_DIR/constraints.txt" --dest "$BUILD_DIR/wheelhouse" "$wheel"

    say "Installing deployment-manager $VERSION and its dependencies"
    "$py" -I -m pip install --quiet --no-index --find-links "$BUILD_DIR/wheelhouse" --no-warn-script-location \
        --constraint "$BUILD_DIR/constraints.txt" "$wheel"

    # pip writes absolute interpreter paths into bin/ scripts; they break once the bundle moves, and prd2 has its own launcher.
    for script in "$STAGE"/python/bin/*; do
        if [ -f "$script" ] && [ "$(head -c 2 "$script")" = "#!" ] && head -n 3 "$script" | grep -qF "$STAGE/"; then
            rm "$script"
        fi
    done

    site_packages="$("$py" -I -c 'import sysconfig; print(sysconfig.get_path("purelib"))')"
    # Wheels can need a newer macOS than Python itself; the newest wheel tag sets the bundle's minimum.
    MIN_MACOS="$(cat "$site_packages"/*.dist-info/WHEEL | sed -n 's/^Tag: .*-macosx_\([0-9]*\)_\([0-9]*\)_.*/\1.\2/p' |
        { cat; echo "$MACOSX_DEPLOYMENT_TARGET"; } | sort -t . -k 1,1n -k 2,2n | tail -n 1)"
}

build_git() {
    if [ -z "${GIT_VERSION:-}" ]; then
        GIT_VERSION="$(curl -fsSL "$GIT_MIRROR/" | grep -o 'git-[0-9]*\.[0-9]*\.[0-9]*\.tar\.xz' |
            sed 's/^git-//; s/\.tar\.xz$//' | sort -u -t . -k 1,1n -k 2,2n -k 3,3n | tail -n 1)"
        [ -n "$GIT_VERSION" ] || fail "Could not determine the latest git version from $GIT_MIRROR."
    fi
    git_tarball="$DOWNLOADS/git-$GIT_VERSION.tar.xz"
    say "Downloading git $GIT_VERSION"
    download "$GIT_MIRROR/git-$GIT_VERSION.tar.xz" "$git_tarball"
    curl -fsSL "$GIT_MIRROR/sha256sums.asc" -o "$DOWNLOADS/git-sha256sums.asc" || fail "Could not download git checksums."
    verify_sha256 "$git_tarball" "$(awk -v name="git-$GIT_VERSION.tar.xz" '$2 == name { print $1 }' "$DOWNLOADS/git-sha256sums.asc")"

    rm -rf "$BUILD_DIR/git-$GIT_VERSION"
    tar -xJf "$git_tarball" -C "$BUILD_DIR"

    # RUNTIME_PREFIX makes git find its helpers relative to its own location, so the bundle can be moved.
    # It links only against system libcurl, zlib and iconv; no gettext, Perl, Python or Tcl parts.
    # NO_RUST uses the C implementations, so no Rust toolchain is needed (until Git 3.0 makes Rust mandatory).
    say "Compiling git $GIT_VERSION (log: $BUILD_DIR/git-build.log)"
    make -C "$BUILD_DIR/git-$GIT_VERSION" -j "$(sysctl -n hw.ncpu 2>/dev/null || echo 4)" prefix="$STAGE/git" \
        RUNTIME_PREFIX=YesPlease NO_GETTEXT=YesPlease NO_PERL=YesPlease NO_PYTHON=YesPlease \
        NO_TCLTK=YesPlease NO_EXPAT=YesPlease NO_OPENSSL=YesPlease NO_RUST=YesPlease SKIP_DASHED_BUILT_INS=YesPlease \
        install >"$BUILD_DIR/git-build.log" 2>&1 || { tail -n 30 "$BUILD_DIR/git-build.log"; fail "Compiling git failed."; }
}

# Fails if any binary links a library that does not ship with macOS (e.g., from Homebrew on the build machine).
check_linkage() {
    find "$1" -type f \( -perm -u+x -o -name '*.so' -o -name '*.dylib' \) -exec sh -c '
        for f do
            file -b "$f" | grep -q "^Mach-O" || continue
            own_id="$(otool -D "$f" | sed -n 2p)"
            otool -L "$f" | awk -v own_id="$own_id" "/^\t/ && \$1 != own_id { print \$1 }" |
                grep -Ev "^(/usr/lib/|/System/Library/|@rpath/|@loader_path/|@executable_path/)" | sed "s|^|$f: |"
        done' sh {} + >"$BUILD_DIR/foreign-libraries.txt"
    if [ -s "$BUILD_DIR/foreign-libraries.txt" ]; then
        cat "$BUILD_DIR/foreign-libraries.txt" >&2
        fail "The binaries above link libraries that users' Macs do not have."
    fi
}

# Runs the moved bundle like a fresh Mac would: system PATH only and no git config of the build user.
smoke_test() {
    work="$(mktemp -d "${TMPDIR:-/tmp}/prd2-smoke.XXXXXX")"
    clean_env() { (cd "$work" && env -i HOME="$work" PATH="/usr/bin:/bin:/usr/sbin:/sbin" TMPDIR="$work" GIT_CONFIG_NOSYSTEM=1 "$@"); }
    git="$1/git/bin/git"

    clean_env "$1/prd2" --version
    case "$(clean_env "$git" --exec-path)" in
        "$1/git/"*) ;;
        *) fail "The bundled git does not find its helpers inside the bundle." ;;
    esac
    clean_env "$git" init -q repo
    clean_env "$git" -C repo -c user.name=smoke -c user.email=smoke@test commit -q --allow-empty -m smoke
    clean_env "$git" ls-remote https://github.com/rossumai/deployment-manager HEAD >/dev/null ||
        fail "The bundled git cannot reach a repository over HTTPS."
    rm -rf "$work"
}

main() {
    case "$(uname -m)" in
        arm64) ARCH="arm64" PBS_TRIPLE="aarch64-apple-darwin" ;;
        x86_64) ARCH="x86_64" PBS_TRIPLE="x86_64-apple-darwin" ;;
        *) fail "Unsupported architecture: $(uname -m)" ;;
    esac
    xcode-select -p >/dev/null 2>&1 || fail "Xcode Command Line Tools are needed to compile git: xcode-select --install"
    ignore_user_package_config

    rm -rf "$STAGE"
    mkdir -p "$STAGE" "$DOWNLOADS" "$DIST_DIR"

    fetch_python "$PBS_TRIPLE" "$STAGE"
    install_prd2
    build_git

    cp "$SCRIPT_DIR/prd2" "$SCRIPT_DIR/install.sh" "$STAGE/"
    chmod +x "$STAGE/prd2" "$STAGE/install.sh"
    cat >"$STAGE/prd2-bundle.json" <<EOF
{"version": "$VERSION", "platform": "macos-$ARCH", "python": "$PYTHON_VERSION", "git": "$GIT_VERSION", "min_macos": "$MIN_MACOS"}
EOF

    say "Checking that the bundle only needs libraries macOS ships with"
    check_linkage "$STAGE"

    # Renaming to the final name doubles as a relocation test for the smoke test below.
    name="prd2-$VERSION-macos-$ARCH"
    rm -rf "${BUILD_DIR:?}/$name"
    mv "$STAGE" "$BUILD_DIR/$name"
    say "Smoke-testing the bundle"
    smoke_test "$BUILD_DIR/$name"

    archive="$DIST_DIR/$name.tar.gz"
    # COPYFILE_DISABLE keeps macOS metadata (._* files) out of the archive.
    COPYFILE_DISABLE=1 tar -C "$BUILD_DIR" -czf "$archive" "$name"
    (cd "$DIST_DIR" && shasum -a 256 "$name.tar.gz" >"$name.tar.gz.sha256")

    say "Built $archive ($(du -h "$archive" | cut -f 1)): Python $PYTHON_VERSION, git $GIT_VERSION, needs macOS $MIN_MACOS+"
}

main "$@"
