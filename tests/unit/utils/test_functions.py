import asyncio

import pytest
from anyio import Path

from deployment_manager.utils.functions import (
    FORBIDDEN_CHARS_REGEX,
    apply_concurrency_override,
    coro,
    detemplatize_name_id,
    extract_id_from_url,
    find_all_hook_paths_in_destination,
    find_all_object_paths,
    find_all_schema_paths_in_destination,
    find_object_by_id,
    find_object_by_key,
    find_object_in_project,
    flatten,
    gather_with_concurrency,
    templatize_name_id,
)


class TestTemplatizeNameId:
    def test_basic(self):
        assert templatize_name_id("My WS", 42) == "My WS_[42]"

    def test_removes_forbidden_chars(self):
        assert templatize_name_id('a/b\\c"d\'e`f', 1) == "abcdef_[1]"

    def test_negative_id(self):
        assert templatize_name_id("queue", -1) == "queue_[-1]"

    def test_empty_name(self):
        assert templatize_name_id("", 10) == "_[10]"

    def test_name_with_numbers(self):
        assert templatize_name_id("Q1 [PROD]", 99) == "Q1 [PROD]_[99]"


class TestDetemplatizeNameId:
    def test_string_input(self):
        assert detemplatize_name_id("myname_[42]") == ("myname", 42)

    def test_string_with_underscores_in_name(self):
        assert detemplatize_name_id("my_very_special_name_[99]") == ("my_very_special_name", 99)

    def test_path_for_queue(self):
        path = Path("org/sub/workspaces/ws_[1]/queues/q_[5]/queue.json")
        assert detemplatize_name_id(path) == ("q", 5)

    def test_path_for_workspace(self):
        path = Path("org/sub/workspaces/ws_[1]/workspace.json")
        assert detemplatize_name_id(path) == ("ws", 1)

    def test_path_for_inbox(self):
        path = Path("org/sub/workspaces/ws_[1]/queues/q_[5]/inbox.json")
        assert detemplatize_name_id(path) == ("q", 5)

    def test_path_for_schema(self):
        path = Path("org/sub/workspaces/ws_[1]/queues/q_[5]/schema.json")
        assert detemplatize_name_id(path) == ("q", 5)

    def test_path_for_hook_file(self):
        path = Path("org/sub/hooks/myhook_[17].json")
        assert detemplatize_name_id(path) == ("myhook", 17)

    def test_path_for_email_template(self):
        path = Path("org/sub/email_templates/greeter_[3].json")
        assert detemplatize_name_id(path) == ("greeter", 3)

    def test_roundtrip(self):
        # After removing forbidden characters, roundtrip should hold
        name, id_ = "some name", 77
        templated = templatize_name_id(name, id_)
        detemplated_name, detemplated_id = detemplatize_name_id(templated)
        assert detemplated_name == name
        assert detemplated_id == id_


class TestExtractIdFromUrl:
    def test_basic(self):
        assert extract_id_from_url("https://api.rossum.ai/api/v1/hooks/1234") == 1234

    def test_none(self):
        assert extract_id_from_url(None) is None

    def test_empty(self):
        assert extract_id_from_url("") is None

    def test_only_id(self):
        assert extract_id_from_url("42") == 42


class TestFlatten:
    def test_flat_list(self):
        assert flatten([1, 2, 3]) == [1, 2, 3]

    def test_nested_list(self):
        assert flatten([1, [2, 3], [4, [5, 6]]]) == [1, 2, 3, 4, 5, 6]

    def test_empty(self):
        assert flatten([]) == []

    def test_deeply_nested(self):
        assert flatten([[[[1]]], 2]) == [1, 2]

    def test_mixed_types(self):
        assert flatten(["a", ["b", "c"], 1]) == ["a", "b", "c", 1]


class TestFindObjectBy:
    def test_find_by_key(self):
        objs = [{"name": "a", "id": 1}, {"name": "b", "id": 2}]
        assert find_object_by_key("name", "b", objs) == {"name": "b", "id": 2}

    def test_find_by_key_missing(self):
        objs = [{"name": "a", "id": 1}]
        assert find_object_by_key("name", "c", objs) is None

    def test_find_by_id(self):
        objs = [{"id": 1}, {"id": 2}]
        assert find_object_by_id(2, objs) == {"id": 2}

    def test_find_by_id_missing(self):
        assert find_object_by_id(99, [{"id": 1}]) is None

    def test_find_by_id_empty_list(self):
        assert find_object_by_id(1, []) is None


class TestForbiddenCharsRegex:
    def test_matches_slash(self):
        assert FORBIDDEN_CHARS_REGEX.search("a/b") is not None

    def test_matches_backslash(self):
        assert FORBIDDEN_CHARS_REGEX.search("a\\b") is not None

    def test_matches_quotes(self):
        assert FORBIDDEN_CHARS_REGEX.search('a"b') is not None
        assert FORBIDDEN_CHARS_REGEX.search("a'b") is not None
        assert FORBIDDEN_CHARS_REGEX.search("a`b") is not None

    def test_no_match_normal(self):
        assert FORBIDDEN_CHARS_REGEX.search("normal_name 42") is None


class TestCoro:
    def test_wraps_async_function(self):
        @coro
        async def _impl(x):
            return x * 2

        assert _impl(3) == 6

    def test_coro_with_args_and_kwargs(self):
        @coro
        async def _impl(a, b, c=0):
            return a + b + c

        assert _impl(1, 2, c=3) == 6


@pytest.mark.asyncio
class TestGatherWithConcurrency:
    async def test_results_in_order(self):
        async def _task(n):
            await asyncio.sleep(0)
            return n

        results = await gather_with_concurrency(*[_task(i) for i in range(5)], n=2)
        assert results == [0, 1, 2, 3, 4]

    async def test_concurrency_limit_respected(self):
        max_running = 0
        running = 0

        async def _task():
            nonlocal running, max_running
            running += 1
            max_running = max(max_running, running)
            await asyncio.sleep(0.01)
            running -= 1
            return True

        await gather_with_concurrency(*[_task() for _ in range(10)], n=3)
        assert max_running <= 3

    async def test_zero_coros(self):
        results = await gather_with_concurrency(n=2)
        assert results == []


class TestApplyConcurrencyOverride:
    def test_none_leaves_unchanged(self):
        from deployment_manager.utils.consts import settings

        original = settings.CONCURRENCY
        try:
            apply_concurrency_override(None)
            assert settings.CONCURRENCY == original
        finally:
            settings.CONCURRENCY = original

    def test_sets_value(self):
        from deployment_manager.utils.consts import settings

        original = settings.CONCURRENCY
        try:
            apply_concurrency_override(7)
            assert settings.CONCURRENCY == 7
        finally:
            settings.CONCURRENCY = original


@pytest.mark.asyncio
class TestFindAllObjectPaths:
    async def test_finds_json_files_recursive(self, tmp_path):
        await (tmp_path / "a").mkdir()
        await (tmp_path / "a" / "b").mkdir()
        await (tmp_path / "a" / "q.json").write_text("{}")
        await (tmp_path / "a" / "b" / "r.json").write_text("{}")
        await (tmp_path / "a" / "not.txt").write_text("skip me")

        found = await find_all_object_paths(tmp_path)
        found_names = sorted([p.name for p in found])
        assert found_names == ["q.json", "r.json"]


@pytest.mark.asyncio
class TestFindHookAndSchemaPaths:
    async def test_hooks_dir_missing(self, tmp_path):
        result = await find_all_hook_paths_in_destination(tmp_path)
        assert result == []

    async def test_hooks_found(self, tmp_path):
        hooks = tmp_path / "hooks"
        await hooks.mkdir()
        await (hooks / "h1.json").write_text("{}")
        await (hooks / "h2.json").write_text("{}")
        await (hooks / "skip.txt").write_text("x")

        result = await find_all_hook_paths_in_destination(tmp_path)
        names = sorted([p.name for p in result])
        assert names == ["h1.json", "h2.json"]

    async def test_schemas_dir_missing(self, tmp_path):
        result = await find_all_schema_paths_in_destination(tmp_path)
        assert result == []

    async def test_schemas_found(self, tmp_path):
        schemas = tmp_path / "schemas"
        await schemas.mkdir()
        await (schemas / "s1.json").write_text("{}")
        await (schemas / "s2.json").write_text("{}")

        result = await find_all_schema_paths_in_destination(tmp_path)
        assert len(result) == 2


@pytest.mark.asyncio
class TestFindObjectInProject:
    async def test_not_found_when_missing(self, tmp_path):
        result = await find_object_in_project({"name": "foo", "id": 1}, tmp_path)
        assert not result

    async def test_finds_directory_based(self, tmp_path):
        ws_dir = tmp_path / "workspaces" / templatize_name_id("myws", 99)
        await ws_dir.mkdir(parents=True)
        result = await find_object_in_project(
            {"name": "myws", "id": 99}, tmp_path / "workspaces"
        )
        assert result

    async def test_finds_json_file(self, tmp_path):
        await tmp_path.mkdir(parents=True, exist_ok=True)
        json_path = tmp_path / f"{templatize_name_id('hook', 5)}.json"
        await json_path.write_text("{}")
        result = await find_object_in_project({"name": "hook", "id": 5}, tmp_path)
        assert result
