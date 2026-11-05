import difflib
import json
from copy import deepcopy

from rich.markup import escape


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

            code_diff = difflib.unified_diff(before_code, after_code, fromfile="before", tofile="after", lineterm="")
            code_diff = "\n".join(list(code_diff))

            if code_diff:
                code_diff = f"{'*'*80}\nconfig.code diff:\n{'*'*80}\n{code_diff}"

        # difflib instead of the diff command, which Windows does not have
        diff = difflib.unified_diff(
            json.dumps(before_object_copy, indent=2, sort_keys=True).splitlines(),
            json.dumps(after_object_copy, indent=2, sort_keys=True).splitlines(),
            lineterm="",
        )
        return "".join(f"{line}\n" for line in diff) + code_diff

    @classmethod
    def parse_diff(cls, diff: str):
        if not diff:
            return ""

        colorized_lines = []
        split_lines = []

        for line in diff.splitlines():
            if line.startswith("--- ") or line.startswith("+++ ") or (line.startswith("@@ ") and line.endswith(" @@")):
                continue
            split_lines.append(line)

        for index, line in enumerate(split_lines):
            if line.startswith("-"):
                colorized_line = f"[red]{escape(line)}[/red]"
            elif line.startswith("+"):
                colorized_line = f"[green]{escape(line)}[/green]"
            # The second is a CRLF issue related to diff
            elif line.startswith("@@") or "newline at end of file" in line:
                del split_lines[index]
            else:
                colorized_line = line
            colorized_lines.append(colorized_line)
        return "\n".join(colorized_lines)
