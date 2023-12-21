## Installation Guide
1. Install pipx:
```
brew install pipx
pipx ensurepath
```
2. Install the tool:
```
pipx install .
```
3. Restart your terminal.

## User Guide

### Downloading an unversioned organization from Rossum
1. Run `prd init <project_name>` which will initialize an empty GIT repository.
2. Fill in the required credentials in the `.env` file (`API_BASE`, `USERNAME`, `PASSWORD`).
3. **Inside the directory**, run `prd download`.

## Development Guide
For faster development, you can run the tool using `poetry run prd`.