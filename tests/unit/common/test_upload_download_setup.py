from pathlib import PurePosixPath, PureWindowsPath

import pytest

from deployment_manager.commands.download.directory import OrganizationDirectory
from deployment_manager.common.upload_download_setup import (
    expand_destinations,
    mark_subdirectories_to_include,
)


def make_configured_directories():
    return {
        "sandbox-org": OrganizationDirectory(
            name="sandbox-org",
            org_id=1,
            api_base="https://api.elis.rossum.ai/v1",
            subdirectories={"dev": {}, "prod": {}},
        ),
        "other-org": OrganizationDirectory(
            name="other-org",
            org_id=2,
            api_base="https://api.elis.rossum.ai/v1",
            subdirectories={"dev": {}},
        ),
    }


def included(configured_directories):
    return {
        f"{dir_name}/{subdir_name}"
        for dir_name, dir_config in configured_directories.items()
        for subdir_name, subdir_config in dir_config.subdirectories.items()
        if subdir_config.include
    }


# NOTE: Pure paths simulate the Windows path flavour on any OS, where `str()` joins with backslashes.
@pytest.mark.parametrize("path_cls", [PurePosixPath, PureWindowsPath])
@pytest.mark.parametrize(
    "destination, expected",
    [
        ("sandbox-org", {"sandbox-org/dev", "sandbox-org/prod"}),
        ("sandbox-org/dev", {"sandbox-org/dev"}),
    ],
)
def test_destinations_mark_subdirectories_to_include(path_cls, destination, expected):
    configured_directories = make_configured_directories()
    project_path = path_cls(".")

    expanded_destinations = expand_destinations(
        destinations=(path_cls(destination),),
        project_path=project_path,
        configured_directories=configured_directories,
    )
    mark_subdirectories_to_include(
        configured_directories=configured_directories,
        expanded_destinations=expanded_destinations,
    )

    assert included(configured_directories) == expected
