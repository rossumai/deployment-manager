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
1. Create a root directory for your organization.
2. `cd` into the directory.
3. Create an `.env` file based on the example in this repository and fill in the required credentials (`API_BASE`, `USERNAME`, `PASSWORD`).
4. Inside the directory, run `prd download`

## Development Guide
For faster development, you can run the tool using `poetry run prd`.