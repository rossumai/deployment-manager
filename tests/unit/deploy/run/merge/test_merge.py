import pytest

from deployment_manager.commands.deploy.subcommands.run.merge.merge import (
    create_rebase_diff,
    deep_three_way_merge,
    get_nested_value,
    is_primitive,
    set_nested_value,
)


class TestIsPrimitive:
    @pytest.mark.parametrize("v", ["str", 1, 1.5, True, None])
    def test_true_for_primitives(self, v):
        assert is_primitive(v)

    @pytest.mark.parametrize("v", [[], {}, set(), (1,)])
    def test_false_for_containers(self, v):
        assert not is_primitive(v)


class TestDeepThreeWayMerge:
    def test_no_changes(self):
        la = {"a": 1, "b": "x"}
        s = {"a": 1, "b": "x"}
        t = {"a": 1, "b": "x"}
        merged, conflicts, rebases = deep_three_way_merge(la, s, t)
        assert merged == {"a": 1, "b": "x"}
        assert conflicts == {}
        assert rebases == {}

    def test_source_only_change(self):
        la = {"a": 1}
        s = {"a": 2}  # source changed
        t = {"a": 1}  # target unchanged
        merged, conflicts, rebases = deep_three_way_merge(la, s, t)
        assert merged["a"] == 2
        assert conflicts == {}
        assert rebases == {}

    def test_target_only_change_becomes_rebase(self):
        la = {"a": 1}
        s = {"a": 1}  # source unchanged
        t = {"a": 99}  # target changed
        merged, conflicts, rebases = deep_three_way_merge(la, s, t)
        # Source value wins in merged output, but rebase is suggested
        assert merged["a"] == 1
        assert rebases == {"a": 99}
        assert conflicts == {}

    def test_conflict(self):
        la = {"a": 1}
        s = {"a": 2}
        t = {"a": 3}
        merged, conflicts, rebases = deep_three_way_merge(la, s, t)
        assert conflicts == {"a": (2, 3)}
        assert merged["a"] == 2  # default to source

    def test_prefer_source_on_conflict(self):
        la = {"a": 1}
        s = {"a": 2}
        t = {"a": 3}
        merged, conflicts, rebases = deep_three_way_merge(la, s, t, prefer="source")
        assert merged["a"] == 2
        assert conflicts == {}

    def test_prefer_target_on_conflict(self):
        la = {"a": 1}
        s = {"a": 2}
        t = {"a": 3}
        merged, conflicts, rebases = deep_three_way_merge(la, s, t, prefer="target")
        assert merged["a"] == 3
        assert conflicts == {}

    def test_override_field_wins_source(self):
        la = {"a": 1}
        s = {"a": 2}
        t = {"a": 3}
        merged, conflicts, rebases = deep_three_way_merge(
            la, s, t, override_fields=["a"]
        )
        assert merged["a"] == 2
        assert conflicts == {}

    def test_ignored_field_just_passes_through(self):
        la = {"a": 1}
        s = {"a": 2}
        t = {"a": 3}
        merged, conflicts, rebases = deep_three_way_merge(
            la, s, t, ignored_fields=["a"]
        )
        assert merged["a"] == 2
        assert conflicts == {}

    def test_derived_field_not_in_source(self):
        la = {}
        s = {}
        t = {"a": 999}
        merged, conflicts, rebases = deep_three_way_merge(
            la, s, t, derived_fields=["a"]
        )
        assert merged["a"] == 999

    def test_list_unchanged(self):
        la = {"ids": [1, 2]}
        s = {"ids": [1, 2]}
        t = {"ids": [1, 2]}
        merged, conflicts, rebases = deep_three_way_merge(la, s, t)
        assert set(merged["ids"]) == {1, 2}

    def test_list_source_only_change(self):
        la = {"ids": [1, 2]}
        s = {"ids": [1, 2, 3]}
        t = {"ids": [1, 2]}
        merged, conflicts, rebases = deep_three_way_merge(la, s, t)
        assert set(merged["ids"]) == {1, 2, 3}

    def test_list_target_only_change_is_rebase(self):
        la = {"ids": [1, 2]}
        s = {"ids": [1, 2]}
        t = {"ids": [1, 2, 3]}
        merged, conflicts, rebases = deep_three_way_merge(la, s, t)
        assert set(merged["ids"]) == {1, 2}
        assert "ids" in rebases

    def test_list_conflict(self):
        la = {"ids": [1]}
        s = {"ids": [2]}
        t = {"ids": [3]}
        merged, conflicts, rebases = deep_three_way_merge(la, s, t)
        assert "ids" in conflicts

    def test_nested_dict_recursion(self):
        la = {"settings": {"locale": "en_US"}}
        s = {"settings": {"locale": "en_GB"}}
        t = {"settings": {"locale": "en_US"}}
        merged, conflicts, rebases = deep_three_way_merge(la, s, t)
        assert merged["settings"]["locale"] == "en_GB"
        assert conflicts == {}

    def test_nested_conflict_path(self):
        la = {"settings": {"locale": "en_US"}}
        s = {"settings": {"locale": "en_GB"}}
        t = {"settings": {"locale": "cs_CZ"}}
        merged, conflicts, rebases = deep_three_way_merge(la, s, t)
        assert "settings.locale" in conflicts

    def test_new_key_only_in_source(self):
        la = {}
        s = {"new_field": "value"}
        t = {}
        merged, _, _ = deep_three_way_merge(la, s, t)
        assert merged["new_field"] == "value"


class TestGetSetNestedValue:
    def test_get_flat(self):
        assert get_nested_value({"a": 1}, "a") == 1

    def test_get_nested(self):
        assert get_nested_value({"a": {"b": {"c": 5}}}, "a.b.c") == 5

    def test_get_missing_returns_default(self):
        assert get_nested_value({"a": 1}, "missing") is None
        assert get_nested_value({"a": 1}, "missing", "default") == "default"

    def test_get_missing_through_non_dict(self):
        assert get_nested_value({"a": 5}, "a.b.c") is None

    def test_set_flat(self):
        obj = {}
        set_nested_value(obj, "a", 42)
        assert obj == {"a": 42}

    def test_set_nested_creates_path(self):
        obj = {}
        set_nested_value(obj, "a.b.c", "v")
        assert obj == {"a": {"b": {"c": "v"}}}

    def test_set_nested_overwrites(self):
        obj = {"a": {"b": "old"}}
        set_nested_value(obj, "a.b", "new")
        assert obj["a"]["b"] == "new"


class TestCreateRebaseDiff:
    def test_string_diff(self):
        diff = create_rebase_diff("hello", "world")
        assert "hello" in diff
        assert "world" in diff

    def test_dict_diff_pretty_printed(self):
        diff = create_rebase_diff({"a": 1}, {"a": 2})
        assert "1" in diff
        assert "2" in diff

    def test_identical_values_empty(self):
        assert create_rebase_diff("x", "x") == ""
