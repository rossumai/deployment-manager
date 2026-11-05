"""Prints a pip constraints file pinning every package to its poetry.lock version, so bundles match `poetry install`."""

import sys

import tomllib

with open(sys.argv[1], "rb") as lock_file:
    for package in tomllib.load(lock_file)["package"]:
        print(f"{package['name']}=={package['version']}")
