import pytest
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.attribute_override import (
    AttributeOverrideException,
    AttributeOverrider,
    create_regex_override_syntax,
    parse_parent_and_key,
    parse_regex_attribute_override,
    perform_search,
    recursive_override,
    traverse_mapping,
)
from deployment_manager.utils.consts import settings


class TestParseParentAndKey:
    def test_plain_key(self):
        parent, key, create_if = parse_parent_and_key("name")
        assert parent is None
        assert key == "name"
        assert create_if is False

    def test_nested_dot(self):
        parent, key, create_if = parse_parent_and_key("settings.foo")
        assert parent == "settings"
        assert key == "foo"

    def test_jmespath_with_pipe(self):
        parent, key, create_if = parse_parent_and_key("settings | foo")
        assert parent == "settings"
        assert key == "foo"

    def test_bracket_query_with_key(self):
        parent, key, create_if = parse_parent_and_key("settings.configurations[*].queue_ids")
        assert parent == "settings.configurations[*]"
        assert key == "queue_ids"

    def test_create_if_not_exists_stripped(self):
        parent, key, create_if = parse_parent_and_key("settings.new_key!")
        assert parent == "settings"
        assert key == "new_key"
        assert create_if is True


class TestParseRegexAttributeOverride:
    def test_plain_value(self):
        regex, value = parse_regex_attribute_override("hello")
        assert regex == ""
        assert value == "hello"

    def test_with_separator(self):
        sep = settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR
        regex, value = parse_regex_attribute_override(f"prefix_\\d+{sep}newprefix_42")
        assert regex == "prefix_\\d+"
        assert value == "newprefix_42"


class TestCreateRegexOverrideSyntax:
    def test_joins_with_separator(self):
        sep = settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR
        assert create_regex_override_syntax("a", "b") == f"a{sep}b"


class TestPerformSearch:
    def test_no_parent_returns_root(self):
        obj = {"name": "foo"}
        assert perform_search(None, obj) == [obj]

    def test_simple_jmespath(self):
        obj = {"settings": {"k": "v"}}
        assert perform_search("settings", obj) == [{"k": "v"}]

    def test_empty_result_raises(self):
        obj = {"settings": {"k": "v"}}
        with pytest.raises(AttributeOverrideException):
            perform_search("nonexistent", obj)

    def test_list_flattens(self):
        obj = {"items": [{"x": 1}, {"x": 2}]}
        result = perform_search("items[*]", obj)
        assert result == [{"x": 1}, {"x": 2}]


class TestRecursiveOverride:
    def test_string_match(self):
        import re

        assert recursive_override("hello world", re.compile("hello"), "HELLO") == "HELLO world"

    def test_nested_dict(self):
        import re

        data = {"a": "old_1", "b": {"c": "old_2"}}
        result = recursive_override(data, re.compile(r"old_(\d+)"), r"new_\1")
        assert result == {"a": "new_1", "b": {"c": "new_2"}}

    def test_list(self):
        import re

        data = ["item_1", "item_2"]
        result = recursive_override(data, re.compile("item"), "thing")
        assert result == ["thing_1", "thing_2"]

    def test_non_string_untouched(self):
        import re

        data = {"num": 42, "bool": True, "null": None}
        assert recursive_override(data, re.compile("x"), "y") == data


class TestTraverseMapping:
    def test_walks_dicts(self):
        mapping = {"organization": {"id": 1, "targets": [{"target_id": 2}]}}
        yielded = list(traverse_mapping(mapping))
        # "targets" is in MAPPING_TRAVERSE_IGNORE_FIELDS; shouldn't be descended into
        assert {"id": 1, "targets": [{"target_id": 2}]} in yielded
        assert not any(d.get("target_id") == 2 for d in yielded)

    def test_walks_lists(self):
        mapping = [{"a": 1}, {"b": 2}]
        yielded = list(traverse_mapping(mapping))
        assert {"a": 1} in yielded
        assert {"b": 2} in yielded


class TestAttributeOverrider:
    def test_override_simple_string(self):
        overrider = AttributeOverrider(type=Resource.Workspace)
        obj = {"name": "old"}
        overrider.override_attribute_v2(obj, "name", "new")
        assert obj["name"] == "new"

    def test_override_nested_string(self):
        overrider = AttributeOverrider(type=Resource.Queue)
        obj = {"settings": {"locale": "en_US"}}
        overrider.override_attribute_v2(obj, "settings.locale", "cs_CZ")
        assert obj["settings"]["locale"] == "cs_CZ"

    def test_override_skips_missing_key_by_default(self):
        overrider = AttributeOverrider(type=Resource.Queue)
        obj = {"settings": {"locale": "en_US"}}
        overrider.override_attribute_v2(obj, "settings.not_there", "value")
        assert "not_there" not in obj["settings"]

    def test_override_creates_key_with_bang_suffix(self):
        overrider = AttributeOverrider(type=Resource.Queue)
        obj = {"settings": {"locale": "en_US"}}
        overrider.override_attribute_v2(obj, "settings.new_key!", "v")
        assert obj["settings"]["new_key"] == "v"

    def test_override_dict_merges(self):
        overrider = AttributeOverrider(type=Resource.Queue)
        obj = {"metadata": {"keep": "me", "replace": "old"}}
        overrider.override_attribute_v2(obj, "metadata", {"replace": "new"})
        assert obj["metadata"] == {"keep": "me", "replace": "new"}

    def test_override_list_replaces(self):
        overrider = AttributeOverrider(type=Resource.Queue)
        obj = {"tags": ["a", "b"]}
        overrider.override_attribute_v2(obj, "tags", ["c", "d"])
        assert obj["tags"] == ["c", "d"]

    def test_override_regex(self):
        overrider = AttributeOverrider(type=Resource.Queue)
        obj = {"name": "Queue_123"}
        sep = settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR
        overrider.override_attribute_v2(obj, "name", f"Queue_\\d+{sep}Queue_999")
        assert obj["name"] == "Queue_999"

    def test_override_attributes_v2_multiple(self):
        overrider = AttributeOverrider(type=Resource.Workspace)
        obj = {"name": "old", "metadata": {"v": 1}}
        overrider.override_attributes_v2(obj, {"name": "new", "metadata": {"v": 2}})
        assert obj["name"] == "new"
        assert obj["metadata"] == {"v": 2}

    def test_override_attributes_v2_empty_object_raises(self):
        overrider = AttributeOverrider(type=Resource.Workspace)
        with pytest.raises(Exception):
            overrider.override_attributes_v2(None, {"x": "y"})


class TestReverseAttributes:
    def test_reverse_single_changed_value(self):
        overrider = AttributeOverrider(type=Resource.Workspace)
        source = {"name": "original", "metadata": {"m": 1}}
        target = {"name": "DIFFERENT", "metadata": {"m": 1}}
        reversed_ = overrider.reverse_attributes_v2(source, target, {"name": "ignored"})
        assert reversed_ == {"name": "original"}

    def test_reverse_no_diff_returns_empty(self):
        overrider = AttributeOverrider(type=Resource.Workspace)
        source = {"name": "same"}
        target = {"name": "same"}
        assert overrider.reverse_attributes_v2(source, target, {"name": "x"}) == {}

    def test_reverse_nested_path(self):
        overrider = AttributeOverrider(type=Resource.Queue)
        source = {"settings": {"locale": "en_US"}}
        target = {"settings": {"locale": "cs_CZ"}}
        result = overrider.reverse_attributes_v2(source, target, {"settings.locale": "x"})
        assert result == {"settings.locale": "en_US"}
