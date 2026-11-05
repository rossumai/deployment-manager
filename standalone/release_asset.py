"""Prints "<name> <download URL> <SHA-256>" of the first GitHub release asset whose name matches a regex.

Usage: release_asset.py <release.json> <name regex>
"""

import json
import re
import sys

with open(sys.argv[1]) as release_file:
    release = json.load(release_file)

for asset in release["assets"]:
    if re.fullmatch(sys.argv[2], asset["name"]):
        # GitHub publishes a digest per asset; Git for Windows also lists checksums in its release notes.
        sha256 = (asset.get("digest") or "").removeprefix("sha256:")
        if not sha256:
            match = re.search(re.escape(asset["name"]) + r"\s*\|\s*([0-9a-fA-F]{64})", release.get("body") or "")
            sha256 = match.group(1) if match else ""
        print(asset["name"], asset["browser_download_url"], sha256)
        break
