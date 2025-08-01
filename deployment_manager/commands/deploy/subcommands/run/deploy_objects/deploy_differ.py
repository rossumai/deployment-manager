from copy import deepcopy
import difflib
import json
import subprocess
import tempfile


class DeployObjectDiffer:

    @classmethod
    def create_override_diff(cls, before_object: dict, after_object: dict):
        """Displays both implicit and explicit overrides (the explicit applied already when uploading the file itself)"""
        # Do not display diffs in ID, but the ID must be retained for later reference

        after_object_copy = deepcopy(after_object)
        after_object_copy.pop("id", None)
        after_object_copy.pop("url", None)

        before_object_copy = deepcopy(before_object)
        before_object_copy.pop("id", None)
        before_object_copy.pop("url", None)

        before_code = before_object_copy.get("config", {}).get("code", "")
        after_code = after_object_copy.get("config", {}).get("code", "")
        code_diff = ""

        if before_code and after_code:
            # codes will be compared separately
            del before_object_copy["config"]["code"]
            del after_object_copy["config"]["code"]

            before_code = before_code.splitlines()
            after_code = after_code.splitlines()

            code_diff = difflib.unified_diff(
                before_code, after_code, fromfile="before", tofile="after", lineterm=""
            )
            code_diff = "\n".join(list(code_diff))

            if code_diff:
                code_diff = f"{'*'*80}\nconfig.code diff:\n{'*'*80}\n{code_diff}"

        with tempfile.NamedTemporaryFile() as tf1, tempfile.NamedTemporaryFile() as tf2:
            tf1.write(
                bytes(json.dumps(before_object_copy, indent=2, sort_keys=True), "UTF-8")
            )
            tf2.write(
                bytes(json.dumps(after_object_copy, indent=2, sort_keys=True), "UTF-8")
            )
            # Has to be manually seeked back to start
            tf1.seek(0)
            tf2.seek(0)

            diff = subprocess.run(
                ["diff", tf1.name, tf2.name, "-U" "3"],
                capture_output=True,
                text=True,
            )

            return diff.stdout + code_diff

    @classmethod
    def parse_diff(cls, diff: str):
        if not diff:
            return ""

        colorized_lines = []
        split_lines = []

        for line in diff.splitlines():
            if (
                line.startswith("--- ")
                or line.startswith("+++ ")
                or (line.startswith("@@ ") and line.endswith(" @@"))
            ):
                continue
            split_lines.append(line)

        for index, line in enumerate(split_lines):
            if line.startswith("-"):
                colorized_line = f"[red]{line}[/red]"
            elif line.startswith("+"):
                colorized_line = f"[green]{line}[/green]"
            # The second is a CRLF issue related to diff
            elif line.startswith("@@") or "newline at end of file" in line:
                del split_lines[index]
            else:
                colorized_line = line
            colorized_lines.append(colorized_line)
        return "\n".join(colorized_lines)
