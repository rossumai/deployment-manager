import pytest

from deployment_manager.common.mapping import (
    adjust_keys,
    create_empty_mapping,
    enrich_mapping_with_previous_properties,
    enrich_mapping_with_previous_targets,
    extract_flat_lookup_table,
    extract_source_target_pairs,
    extract_sources_targets,
    extract_target_ids,
    find_mapping_of_object,
    get_attributes_for_mapping,
    get_default_targets,
    get_mapping_key_index,
    index_mappings_by_object_id,
    read_mapping,
    sort_mapping,
    write_mapping,
)
from deployment_manager.utils.consts import settings


class TestAdjustKeys:
    def test_lowercases_matching_keys(self):
        result = adjust_keys({"WORKSPACES": 1, "OTHER": 2}, ["workspaces"])
        assert result == {"workspaces": 1, "OTHER": 2}

    def test_uppercases_when_lower_false(self):
        result = adjust_keys({"workspaces": 1}, ["workspaces"], lower=False)
        assert result == {"WORKSPACES": 1}

    def test_recurses_into_lists(self):
        result = adjust_keys([{"WORKSPACES": 1}], ["workspaces"])
        assert result == [{"workspaces": 1}]

    def test_leaves_primitives(self):
        assert adjust_keys("hello", ["workspaces"]) == "hello"
        assert adjust_keys(42, ["workspaces"]) == 42


class TestGetMappingKeyIndex:
    def test_known_key_returns_index(self):
        assert get_mapping_key_index("id") == settings.MAPPING_KEYS_ORDER.index("id")

    def test_unknown_returns_inf(self):
        from math import inf

        assert get_mapping_key_index("not_a_known_key") == inf


class TestSortMapping:
    def test_sorts_by_known_order(self):
        result = sort_mapping(
            {"targets": [], "name": "x", "id": 1, "comment": "c"}
        )
        keys = list(result.keys())
        assert keys.index("comment") < keys.index("id")
        assert keys.index("id") < keys.index("name")
        assert keys.index("name") < keys.index("targets")

    def test_recurses_into_lists(self):
        result = sort_mapping([{"name": "x", "id": 1}])
        assert list(result[0].keys()) == ["id", "name"]


class TestCreateEmptyMapping:
    def test_basic_structure(self):
        m = create_empty_mapping()
        assert "organization" in m
        for key in ("workspaces", "hooks", "engines", "schemas"):
            assert key in m["organization"]
        assert m["organization"]["targets"] == [{"target_id": None}]


class TestGetAttributesForMapping:
    def test_has_id_name_targets(self):
        attrs = get_attributes_for_mapping({"id": 1, "name": "foo", "other": "x"})
        assert attrs == {"id": 1, "name": "foo", "targets": []}


class TestGetDefaultTargets:
    def test_returns_single_null_target(self):
        assert get_default_targets() == [{"target_id": None}]


class TestIndexMappings:
    def test_indexes_by_id(self):
        sub = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        result = index_mappings_by_object_id(sub)
        assert result[1]["name"] == "a"
        assert result[2]["name"] == "b"

    def test_empty(self):
        assert index_mappings_by_object_id([]) == {}


class TestEnrichPreviousProperties:
    def test_preserves_missing_keys(self):
        new = {"id": 1}
        old = {"id": 1, "comment": "old note", "ignore": True}
        enrich_mapping_with_previous_properties(new, old)
        assert new["comment"] == "old note"
        assert new["ignore"] is True

    def test_does_not_overwrite_existing(self):
        new = {"id": 1, "comment": "NEW"}
        old = {"id": 1, "comment": "OLD"}
        enrich_mapping_with_previous_properties(new, old)
        assert new["comment"] == "NEW"

    def test_handles_none_old(self):
        new = {"id": 1}
        enrich_mapping_with_previous_properties(new, None)
        assert new == {"id": 1}


class TestEnrichPreviousTargets:
    def test_copies_existing_targets(self):
        new = {"id": 1}
        old = {"id": 1, "targets": [{"target_id": 5}, {"target_id": 6}]}
        enrich_mapping_with_previous_targets(new, old, new_ids=[5, 6])
        assert new["targets"] == [{"target_id": 5}, {"target_id": 6}]

    def test_drops_removed_targets(self):
        new = {"id": 1}
        old = {"id": 1, "targets": [{"target_id": 5}, {"target_id": 999}]}
        enrich_mapping_with_previous_targets(new, old, new_ids=[5])
        assert new["targets"] == [{"target_id": 5}]

    def test_fallback_to_default_when_empty(self):
        new = {"id": 1}
        old = {"id": 1, "targets": []}
        enrich_mapping_with_previous_targets(new, old, new_ids=[])
        assert new["targets"] == get_default_targets()

    def test_keeps_null_target(self):
        # target_id=None is kept regardless of new_ids
        new = {"id": 1}
        old = {"id": 1, "targets": [{"target_id": None}]}
        enrich_mapping_with_previous_targets(new, old, new_ids=[])
        assert new["targets"] == [{"target_id": None}]


class TestFindMappingOfObject:
    def test_found(self):
        sub = [{"id": 1}, {"id": 2}]
        assert find_mapping_of_object(sub, 2) == {"id": 2}

    def test_not_found(self):
        assert find_mapping_of_object([{"id": 1}], 99) is None


class TestExtractTargetIds:
    def test_extracts_only_non_null(self):
        submapping = {"targets": [{"target_id": 1}, {"target_id": None}, {"target_id": 5}]}
        assert extract_target_ids(submapping) == [1, 5]

    def test_handles_empty(self):
        assert extract_target_ids({}) == []
        assert extract_target_ids({"targets": []}) == []


class TestExtractSourcesTargets:
    def test_none_mapping_returns_empty(self):
        sources, targets = extract_sources_targets(None)
        assert sources["workspaces"] == []
        assert targets["workspaces"] == []

    def test_full_extraction(self):
        mapping = create_empty_mapping()
        mapping["organization"]["id"] = 100
        mapping["organization"]["targets"] = [{"target_id": 200}]
        mapping["organization"]["workspaces"] = [
            {
                "id": 1,
                "targets": [{"target_id": 11}],
                "queues": [
                    {
                        "id": 2,
                        "targets": [{"target_id": 12}],
                        "inbox": {"id": 3, "targets": [{"target_id": 13}]},
                    }
                ],
            }
        ]
        mapping["organization"]["hooks"] = [{"id": 4, "targets": [{"target_id": 14}]}]
        mapping["organization"]["schemas"] = [{"id": 5, "targets": [{"target_id": 15}]}]

        sources, targets = extract_sources_targets(mapping)

        assert sources["organization"] == 100
        assert sources["workspaces"] == [1]
        assert sources["queues"] == [2]
        assert sources["inboxes"] == [3]
        assert sources["hooks"] == [4]
        assert sources["schemas"] == [5]

        assert targets["organization"] == [200]
        assert targets["workspaces"] == [11]
        assert targets["queues"] == [12]
        assert targets["inboxes"] == [13]
        assert targets["hooks"] == [14]
        assert targets["schemas"] == [15]

    def test_exclude_organization(self):
        mapping = create_empty_mapping()
        mapping["organization"]["id"] = 100
        sources, targets = extract_sources_targets(mapping, include_organization=False)
        assert "organization" not in sources
        assert "organization" not in targets


class TestExtractSourceTargetPairs:
    def test_basic_extraction(self):
        mapping = create_empty_mapping()
        mapping["organization"]["workspaces"] = [
            {
                "id": 1,
                "targets": [{"target_id": 11}],
                "queues": [
                    {
                        "id": 2,
                        "targets": [{"target_id": 12}, {"target_id": 22}],
                        "inbox": {"id": 3, "targets": [{"target_id": 13}]},
                    }
                ],
            }
        ]
        mapping["organization"]["hooks"] = [{"id": 4, "targets": [{"target_id": 14}]}]
        mapping["organization"]["schemas"] = [{"id": 5, "targets": [{"target_id": 15}]}]

        pairs = extract_source_target_pairs(mapping)
        assert pairs["workspaces"] == {1: [11]}
        assert pairs["queues"] == {2: [12, 22]}
        assert pairs["inboxes"] == {3: [13]}
        assert pairs["hooks"] == {4: [14]}
        assert pairs["schemas"] == {5: [15]}


class TestExtractFlatLookupTable:
    def test_produces_flat_source_to_targets(self):
        mapping = create_empty_mapping()
        mapping["organization"]["hooks"] = [{"id": 1, "targets": [{"target_id": 10}]}]
        mapping["organization"]["schemas"] = [{"id": 2, "targets": [{"target_id": 20}]}]
        flat = extract_flat_lookup_table(mapping)
        assert flat == {1: [10], 2: [20]}


@pytest.mark.asyncio
class TestReadWriteMapping:
    async def test_write_and_read(self, tmp_path):
        mapping = create_empty_mapping()
        mapping["organization"]["id"] = 123
        mapping["organization"]["name"] = "acme"

        path = tmp_path / settings.MAPPING_FILENAME
        await write_mapping(path, mapping)
        loaded = await read_mapping(path)
        # Keys are lowercased back on read
        assert loaded["organization"]["id"] == 123
        assert loaded["organization"]["name"] == "acme"

    async def test_read_missing_returns_none(self, tmp_path):
        path = tmp_path / "missing.yaml"
        assert await read_mapping(path) is None
