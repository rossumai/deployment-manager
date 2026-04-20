from deployment_manager.commands.deploy.subcommands.run.deploy_objects.deploy_differ import (
    DeployObjectDiffer,
)


class TestCreateOverrideDiff:
    def test_identical_objects_produce_empty_diff(self):
        before = {"id": 1, "name": "foo", "a": "b"}
        after = {"id": 1, "name": "foo", "a": "b"}
        diff = DeployObjectDiffer.create_override_diff(before, after)
        assert diff == ""

    def test_id_and_url_not_in_diff(self):
        before = {"id": 1, "url": "https://src/1", "name": "foo"}
        after = {"id": 2, "url": "https://tgt/2", "name": "foo"}
        diff = DeployObjectDiffer.create_override_diff(before, after)
        # Since name is the same and id+url are stripped, diff should be empty
        assert diff == ""

    def test_does_not_mutate_after_object(self):
        """id and url must be preserved on the original object."""
        before = {"id": 1, "url": "u1", "name": "a"}
        after = {"id": 2, "url": "u2", "name": "b"}
        _ = DeployObjectDiffer.create_override_diff(before, after)
        assert after == {"id": 2, "url": "u2", "name": "b"}
        assert before == {"id": 1, "url": "u1", "name": "a"}

    def test_name_change_shows_in_diff(self):
        before = {"id": 1, "name": "old"}
        after = {"id": 1, "name": "new"}
        diff = DeployObjectDiffer.create_override_diff(before, after)
        assert "old" in diff
        assert "new" in diff

    def test_config_code_separate_diff(self):
        before = {"id": 1, "config": {"code": "a = 1\n"}}
        after = {"id": 1, "config": {"code": "a = 2\n"}}
        diff = DeployObjectDiffer.create_override_diff(before, after)
        # Our diff block header is present
        assert "config.code diff" in diff
        assert "a = 1" in diff
        assert "a = 2" in diff


class TestParseDiff:
    def test_empty_diff(self):
        assert DeployObjectDiffer.parse_diff("") == ""

    def test_headers_stripped(self):
        diff = "--- before\n+++ after\n@@ -1,1 +1,1 @@\n-old line\n+new line"
        parsed = DeployObjectDiffer.parse_diff(diff)
        assert "before" not in parsed.split("\n")[0]
        assert "old line" in parsed
        assert "new line" in parsed

    def test_colorization_red_green(self):
        diff = "-old\n+new\n context"
        parsed = DeployObjectDiffer.parse_diff(diff)
        assert "[red]" in parsed
        assert "[green]" in parsed
        assert " context" in parsed

    def test_newline_at_end_line_skipped(self):
        diff = "-a\n\\ No newline at end of file"
        parsed = DeployObjectDiffer.parse_diff(diff)
        # The warning line is removed from output
        assert "newline at end of file" not in parsed

    def test_brackets_in_content_escaped(self):
        diff = "-value with [brackets]"
        parsed = DeployObjectDiffer.parse_diff(diff)
        # escape() from rich.markup is used; literal "[brackets]" gets escaped
        # to prevent rich treating it as markup
        assert "[red]" in parsed
        # ensure our original text appears in some form
        assert "brackets" in parsed
