"""Tests for the script-level run/attribute_override.py module.

This module is distinct from deploy_objects/attribute_override.py — it is still imported
by template/helpers.py (for create_regex_override_syntax) and hook/sync/sync.py
(for AttributeOverrider.parse_diff)."""

import pytest
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.attribute_override import (
    AttributeOverrideException,
    AttributeOverrider,
    create_regex_override_syntax,
    parse_parent_and_key,
    parse_regex_attribute_override,
    perform_search,
)
from deployment_manager.utils.consts import settings


class _FakeTarget:
    """A minimal stand-in for Target — we only need .id and .data."""

    def __init__(self, id_, data):
        self.id = id_
        self.data = data


class TestParseParentAndKey:
    def test_plain_key(self):
        parent, key = parse_parent_and_key("name")
        assert parent is None
        assert key == "name"

    def test_dot_separator(self):
        parent, key = parse_parent_and_key("settings.foo")
        assert parent == "settings"
        assert key == "foo"

    def test_pipe_separator(self):
        parent, key = parse_parent_and_key("settings | foo")
        assert parent == "settings"
        assert key == "foo"

    def test_dot_takes_precedence_when_later(self):
        # The implementation picks the last dot if any dots exist
        parent, key = parse_parent_and_key("a | b.c")
        assert parent == "a | b"
        assert key == "c"


class TestParseRegexAttributeOverride:
    def test_plain_value(self):
        regex, value = parse_regex_attribute_override("hello")
        assert regex == ""
        assert value == "hello"

    def test_with_separator(self):
        sep = settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR
        regex, value = parse_regex_attribute_override(f"DEV{sep}PROD")
        assert regex == "DEV"
        assert value == "PROD"


class TestCreateRegexOverrideSyntax:
    def test_combines_with_separator(self):
        result = create_regex_override_syntax("foo", "bar")
        assert settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR in result
        assert result.startswith("foo")
        assert result.endswith("bar")


class TestPerformSearch:
    def test_returns_object_when_no_parent(self):
        obj = {"key": "value"}
        result = perform_search(None, obj)
        assert result == [obj]

    def test_returns_jmespath_match(self):
        obj = {"settings": {"foo": "bar"}}
        result = perform_search("settings", obj)
        assert result == [{"foo": "bar"}]

    def test_raises_when_no_match(self):
        with pytest.raises(AttributeOverrideException):
            perform_search("missing", {"x": 1})

    def test_flattens_list_results(self):
        obj = {
            "settings": {
                "configurations": [
                    {"queues": [{"id": 1}, {"id": 2}]},
                    {"queues": [{"id": 3}]},
                ]
            }
        }
        # JMESPath gives back nested lists; perform_search flattens
        result = perform_search("settings.configurations[*].queues", obj)
        # Three queue dicts in total
        assert len(result) == 3


class TestParseDiff:
    def test_strips_diff_headers(self):
        diff = "--- file1\n+++ file2\n@@ -1,3 +1,3 @@\n line\n-removed\n+added"
        result = AttributeOverrider.parse_diff(diff)
        # Headers gone
        assert "--- file1" not in result
        assert "+++ file2" not in result
        # Hunk markers gone
        assert "@@ -1,3 +1,3 @@" not in result

    def test_colorizes_added_and_removed(self):
        diff = "-removed_line\n+added_line"
        result = AttributeOverrider.parse_diff(diff)
        assert "[red]-removed_line[/red]" in result
        assert "[green]+added_line[/green]" in result

    def test_unchanged_lines_pass_through(self):
        diff = " context_line"
        result = AttributeOverrider.parse_diff(diff)
        assert result == " context_line"

    def test_empty_diff(self):
        assert AttributeOverrider.parse_diff("") == ""


class TestOverrideAttributeV2:
    def test_simple_string_replace(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        obj = {"name": "old"}
        overrider.override_attribute_v2(obj, "name", "new")
        assert obj["name"] == "new"

    def test_regex_override(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        obj = {"settings": {"url": "https://dev.example.com/api"}}
        sep = settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR
        overrider.override_attribute_v2(obj, "settings.url", f"dev{sep}prod")
        assert obj["settings"]["url"] == "https://prod.example.com/api"

    def test_dict_merge(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        obj = {"settings": {"a": 1, "b": 2}}
        overrider.override_attribute_v2(obj, "settings", {"b": 99, "c": 3})
        # Existing keys merged + overridden
        assert obj["settings"] == {"a": 1, "b": 99, "c": 3}

    def test_list_replacement(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        obj = {"settings": {"items": [1, 2, 3]}}
        overrider.override_attribute_v2(obj, "settings.items", [9, 9])
        assert obj["settings"]["items"] == [9, 9]

    def test_skips_when_key_missing_in_some_parents(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        # Only the second config has 'queue_ids'
        obj = {
            "settings": {
                "configurations": [
                    {"name": "no-queues"},
                    {"name": "with-queues", "queue_ids": [1, 2]},
                ]
            }
        }
        overrider.override_attribute_v2(obj, "settings.configurations[*].queue_ids", [99])
        assert "queue_ids" not in obj["settings"]["configurations"][0]
        assert obj["settings"]["configurations"][1]["queue_ids"] == [99]


class TestOverrideAttributesV2:
    def test_applies_multiple_overrides(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        obj = {"name": "old", "settings": {"url": "x"}}
        overrider.override_attributes_v2(obj, {"name": "new", "settings.url": "y"})
        assert obj["name"] == "new"
        assert obj["settings"]["url"] == "y"

    def test_raises_on_none_object(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        # Calling with None triggers the explicit guard, which itself fails on `.get(...)` —
        # the implementation raises an exception of some kind.
        with pytest.raises(Exception):
            overrider.override_attributes_v2(None, {"name": "new"})


class TestReplaceIdInObject:
    def test_replaces_in_dict_value_string(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        obj = {"queue": "https://api/queues/100"}
        overrider.replace_id_in_object(
            object=obj, key="queue", value="https://api/queues/100", source_id=100, target_id=200
        )
        assert obj["queue"] == "https://api/queues/200"

    def test_replaces_in_list_value_int(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        obj = {"queues": [100, 300]}
        overrider.replace_id_in_object(object=obj, key="queues", value=100, source_id=100, target_id=200)
        assert obj["queues"] == [200, 300]


class TestRemoveIdFromList:
    def test_removes_value_from_list(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        obj = {"queues": [100, 200, 300]}
        overrider.remove_id_from_list(object=obj, key="queues", value=200)
        assert obj["queues"] == [100, 300]

    def test_deletes_key_when_not_a_list(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        obj = {"queue": "https://api/queues/100"}
        overrider.remove_id_from_list(object=obj, key="queue", value="https://api/queues/100")
        assert "queue" not in obj


class TestReplaceIdsInTargetObject:
    """The N:1 / N:N reference replacement logic for implicit (settings/metadata) overrides."""

    def _make_target(self, data):
        return _FakeTarget(id_="123", data=data)

    def test_n_to_one_uses_first_target(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        target = self._make_target({"settings": {"queue_url": "https://api/queues/100"}})
        # source_id 100 maps to a single target (one type, one target)
        lookup = {100: {Resource.Queue: [{"id": 200}]}}
        overrider.replace_ids_in_target_object(
            target=target, lookup_table=lookup, target_object_index=0, num_targets=1
        )
        assert target.data["settings"]["queue_url"] == "https://api/queues/200"

    def test_n_to_n_uses_indexed_target(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        target = self._make_target({"settings": {"queue_url": "https://api/queues/100"}})
        # 2 targets, current index = 1 → should pick the second target id (501)
        lookup = {100: {Resource.Queue: [{"id": 500}, {"id": 501}]}}
        overrider.replace_ids_in_target_object(
            target=target, lookup_table=lookup, target_object_index=1, num_targets=2
        )
        assert target.data["settings"]["queue_url"] == "https://api/queues/501"

    def test_skips_keys_not_in_implicit_override_keys(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        # Reference id outside of settings/metadata is ignored (nothing happens)
        target = self._make_target({"name": "https://api/queues/100"})
        lookup = {100: {Resource.Queue: [{"id": 200}]}}
        overrider.replace_ids_in_target_object(
            target=target, lookup_table=lookup, target_object_index=0, num_targets=1
        )
        assert target.data["name"] == "https://api/queues/100"

    def test_removes_id_when_lookup_has_multiple_types(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        target = self._make_target({"settings": {"refs": [100, 999]}})
        # Same source_id resolves to two different resource types -> ambiguous, removed
        lookup = {100: {Resource.Queue: [{"id": 200}], Resource.Hook: [{"id": 300}]}}
        overrider.replace_ids_in_target_object(
            target=target, lookup_table=lookup, target_object_index=0, num_targets=1
        )
        # 100 was removed because of the ambiguity, 999 untouched
        assert 100 not in target.data["settings"]["refs"]
        assert 999 in target.data["settings"]["refs"]


class TestCreateOverrideDiff:
    def test_no_diff_for_identical_objects(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        before = {"id": 1, "url": "x", "name": "same"}
        after = {"id": 1, "url": "x", "name": "same"}
        result = overrider.create_override_diff(before, after)
        # diff should be empty for identical content
        assert result == ""

    def test_shows_diff_for_changed_attribute(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        before = {"id": 1, "url": "x", "name": "old"}
        after = {"id": 1, "url": "x", "name": "new"}
        result = overrider.create_override_diff(before, after)
        assert "old" in result
        assert "new" in result

    def test_shows_code_diff_separately(self):
        overrider = AttributeOverrider(type=Resource.Hook, plan_only=False)
        before = {"id": 1, "url": "x", "config": {"code": "print('a')\n"}}
        after = {"id": 1, "url": "x", "config": {"code": "print('b')\n"}}
        result = overrider.create_override_diff(before, after)
        assert "config.code diff:" in result
        assert "print('a')" in result
        assert "print('b')" in result
