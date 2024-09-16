#!/usr/bin/env bash
PRD_GIT_URL=https://github.com/rossumai/deployment-manager.git

TEMP_GIT_DIR=$(mktemp -d)

cd "$TEMP_GIT_DIR"

git clone "$PRD_GIT_URL"

cd prd

if ! command -v pipx &> /dev/null
then
    echo 'pipx not found, attempting install...'
    brew install pipx
fi   

pipx install . --force


