from anyio import Path
import re

from deployment_manager.common.read_write import read_object_from_json
from deployment_manager.utils.consts import display_error
import subprocess
import tarfile
from io import BytesIO
from urllib.parse import urlparse

async def load_hook_object(hook_path: Path):
    try:
        if hook_path.suffix != ".json":
            raise Exception(f"Incorrect suffix for {hook_path}")
        return await read_object_from_json(hook_path)
    except Exception as e:
        display_error(f"Error while loading hook with path {hook_path}: {e}")


def get_project_path_from_hook_path(hook_path: Path):
    # project_path / org-dir / subdir / hooks / hook.json
    return hook_path.parent.parent.parent.parent


def get_org_name_from_hook_path(hook_path: Path):
    # project_path / org-dir / subdir / hooks / hook.json
    return hook_path.parent.parent.parent.stem


def get_annotation_id_from_frontend_url(url: str):
    match = re.search(r"/document/(\d+)", url)

    if match:
        return match.group(1)

    return ""

def parse_git_file_url(file_url):
    """
    Parses a direct file URL from common Git hosting services (GitHub, GitLab, Bitbucket)
    to extract the SSH repository URL, branch, and file path.

    Args:
        file_url (str): The URL of the file (e.g., https://github.com/user/repo/blob/main/path/to/file.txt).

    Returns:
        tuple: (ssh_repo_url, branch, file_path) or (None, None, None) if parsing fails.
    """
    parsed_url = urlparse(file_url)
    path_parts = parsed_url.path.strip('/').split('/')

    hostname = parsed_url.hostname

    # GitHub pattern: /user/repo/blob/branch/path/to/file
    # GitLab pattern: /user/repo/-/blob/branch/path/to/file (sometimes with -/tree)
    # Bitbucket pattern: /user/repo/src/branch/path/to/file

    if hostname in ("github.com", "www.github.com"):
        if len(path_parts) >= 5 and path_parts[2] == "blob":
            user = path_parts[0]
            repo = path_parts[1]
            branch = path_parts[3]
            file_path = '/'.join(path_parts[4:])
            ssh_repo_url = f"git@github.com:{user}/{repo}.git"
            return ssh_repo_url, branch, file_path
    elif hostname in ("gitlab.com", "www.gitlab.com") or \
         (hostname and "gitlab" in hostname and "." in hostname): # Custom GitLab instances
        if len(path_parts) >= 6 and (path_parts[2] == "-" and path_parts[3] == "blob"):
            # e.g., group/subgroup/repo/-/blob/branch/path/to/file
            repo_path_segments = []
            for i, part in enumerate(path_parts):
                if part == "-" and i + 1 < len(path_parts) and path_parts[i+1] == "blob":
                    repo_path_segments = path_parts[:i]
                    branch = path_parts[i+2]
                    file_path = '/'.join(path_parts[i+3:])
                    break
            if repo_path_segments:
                user_repo_combined = '/'.join(repo_path_segments)
                ssh_repo_url = f"git@{hostname}:{user_repo_combined}.git"
                return ssh_repo_url, branch, file_path
        elif len(path_parts) >= 4 and (path_parts[2] == "blob"): # Older GitLab or simpler paths
             user_repo_combined = '/'.join(path_parts[0:2]) # Adjust if more segments are part of repo name
             branch = path_parts[3]
             file_path = '/'.join(path_parts[4:])
             ssh_repo_url = f"git@{hostname}:{user_repo_combined}.git"
             return ssh_repo_url, branch, file_path
    elif hostname in ("bitbucket.org", "www.bitbucket.org") or \
         (hostname and "bitbucket" in hostname and "." in hostname): # Custom Bitbucket instances
        if len(path_parts) >= 5 and path_parts[2] == "src":
            user = path_parts[0]
            repo = path_parts[1]
            branch = path_parts[3]
            file_path = '/'.join(path_parts[4:])
            ssh_repo_url = f"git@bitbucket.org:{user}/{repo}.git"
            return ssh_repo_url, branch, file_path

    display_error(f"Warning: Could not parse URL '{file_url}' into Git repository components.")
    return None, None, None

def get_git_file_content_from_url_ssh(file_url):
    """
    Fetches the content of a file from a Git repository using its direct URL,
    leveraging the system's 'git' command and SSH key configuration.

    Args:
        file_url (str): The direct URL of the file (e.g., https://github.com/user/repo/blob/main/path/to/file.txt).

    Returns:
        bytes: The content of the file as bytes, or None if an error occurs.
    """
    ssh_repo_url, branch, file_path = parse_git_file_url(file_url)

    if not all([ssh_repo_url, branch, file_path]):
        print(f"Failed to parse the file URL: {file_url}. Cannot proceed with Git command.")
        return None

    git_command = [
        "git",
        "archive",
        f"--remote={ssh_repo_url}",
        branch,
        file_path,
        "--format=tar"
    ]

    try:
        result = subprocess.run(
            git_command,
            capture_output=True,
            check=True,
            shell=False
        )

        tar_data = BytesIO(result.stdout)
        with tarfile.open(fileobj=tar_data, mode="r") as tar:
            try:
                member = tar.getmember(file_path)
                file_obj = tar.extractfile(member)
                if file_obj:
                    return file_obj.read()
                else:
                    display_error(f"Error: Could not extract file object from archive for '{file_path}'.")
                    return None
            except KeyError:
                display_error(f"Error: File '{file_path}' not found in the remote repository or branch's archive. "
                      f"Check file path and branch.")
                return None

    except subprocess.CalledProcessError as e:
        display_error(f"Git command failed with error code {e.returncode} for URL: {file_url}")
        display_error(f"STDOUT: {e.stdout.decode('utf-8', errors='ignore')}")
        display_error(f"STDERR: {e.stderr.decode('utf-8', errors='ignore')}")
        return None
    except FileNotFoundError:
        display_error("Error: 'git' command not found. Make sure Git is installed and in your PATH.")
        return None
    except Exception as e:
        display_error(f"An unexpected error occurred: {e}")
        return None