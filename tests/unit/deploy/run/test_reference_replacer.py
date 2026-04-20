from collections import defaultdict
from unittest.mock import MagicMock

import pytest

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.reference_replacer import (
    ReferenceReplacer,
)

# Trigger Target/DeployObject rebuild
from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (  # noqa: F401
    DeployOrchestrator,
)
from deployment_manager.commands.deploy.subcommands.run.models import Target
from rossum_api.domain_logic.resources import Resource


def _make_target(id_):
    t = Target(id=id_)
    return t


def _make_lookup(source_id: int, resource: Resource, targets: list):
    lut = defaultdict(dict)
    lut[source_id][resource] = targets
    return lut


def _make_reverse_lookup(resource: Resource, pairs: dict):
    rlut = defaultdict(dict)
    rlut[resource] = {str(k): v for k, v in pairs.items()}
    return rlut


def _make_parent(source_base_url="https://src.rossum.app/api/v1", target_base_url="https://tgt.rossum.app/api/v1"):
    parent = MagicMock()
    parent.deploy_file.source_client._http_client.base_url = source_base_url
    parent.deploy_file.client._http_client.base_url = target_base_url
    return parent


class TestReplaceBaseUrl:
    def test_same_base(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        url = "https://src.rossum.app/api/v1/hooks/500001"
        assert rr.replace_base_url(
            url, "https://src.rossum.app/api/v1", "https://tgt.rossum.app/api/v1"
        ) == "https://tgt.rossum.app/api/v1/hooks/500001"

    def test_no_replacement(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        url = "https://other.example/api/v1/hooks/500001"
        assert rr.replace_base_url(url, "https://src.rossum.app/api/v1", "https://tgt.rossum.app/api/v1") == url


class TestIsValidId:
    def test_int(self):
        assert ReferenceReplacer._is_valid_id(42) is True

    def test_digit_str(self):
        assert ReferenceReplacer._is_valid_id("42") is True

    def test_uuid_str(self):
        assert ReferenceReplacer._is_valid_id("a-b-c-d") is False

    def test_none(self):
        assert ReferenceReplacer._is_valid_id(None) is False

    def test_empty_str(self):
        assert ReferenceReplacer._is_valid_id("") is False


class TestReplaceIdInObject:
    def test_replace_in_list(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        obj = {"hooks": ["hook_ref_50000"]}
        rr.replace_id_in_object(obj, "hooks", "hook_ref_50000", 50000, 60000)
        assert obj["hooks"] == ["hook_ref_60000"]

    def test_replace_single_value_int(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        obj = {"hook_id": 50000}
        rr.replace_id_in_object(obj, "hook_id", 50000, 50000, 60000)
        assert obj["hook_id"] == 60000

    def test_replace_single_value_str(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        obj = {"hook_id": "abc_50000"}
        rr.replace_id_in_object(obj, "hook_id", "abc_50000", 50000, 60000)
        assert obj["hook_id"] == "abc_60000"

    def test_keeps_non_numeric_as_string(self):
        """When target is non-numeric (dummy id), should remain a string."""
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        obj = {"hook_id": 50000}
        rr.replace_id_in_object(obj, "hook_id", 50000, 50000, "<NEW COPY>[0](x)")
        assert obj["hook_id"] == "<NEW COPY>[0](x)"


class TestRemoveIdFromList:
    def test_removes_by_value(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        obj = {"items": ["a", "b", "c"]}
        rr.remove_id_from_list(obj, "items", "b")
        assert obj["items"] == ["a", "c"]

    def test_removes_single_key(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        obj = {"single": "x"}
        rr.remove_id_from_list(obj, "single", "x")
        assert "single" not in obj


class TestReplaceReferenceInUrl:
    def test_simple_replacement(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        targets = [_make_target(888888)]
        lut = _make_lookup(500001, Resource.Hook, targets)
        rlut = _make_reverse_lookup(Resource.Hook, {})

        source_url = "https://src.rossum.app/api/v1/hooks/500001"
        result = rr._replace_reference_in_url(
            source_dependency_url=source_url,
            lookup_table=lut,
            reverse_lookup_table=rlut,
            object_type=Resource.Hook,
            target_objects_count=1,
            target_index=0,
            use_dummy_references=True,
        )
        # ID and base URL replaced
        assert result == "https://tgt.rossum.app/api/v1/hooks/888888"

    def test_no_mapping_returns_none(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        lut = {}  # empty
        rlut = _make_reverse_lookup(Resource.Hook, {})
        result = rr._replace_reference_in_url(
            source_dependency_url="https://src.rossum.app/api/v1/hooks/500005",
            lookup_table=lut,
            reverse_lookup_table=rlut,
            object_type=Resource.Hook,
            target_objects_count=1,
            target_index=0,
            use_dummy_references=True,
        )
        assert result is None

    def test_source_id_is_already_target_id(self):
        """If source_id looks like a target-id that was replaced, we keep it."""
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        lut = {}
        # target id 500005 was originally source 5
        rlut = _make_reverse_lookup(Resource.Hook, {500005: 5})
        url = "https://src.rossum.app/api/v1/hooks/500005"
        result = rr._replace_reference_in_url(
            source_dependency_url=url,
            lookup_table=lut,
            reverse_lookup_table=rlut,
            object_type=Resource.Hook,
            target_objects_count=1,
            target_index=0,
            use_dummy_references=True,
        )
        # returns original URL unchanged
        assert result == url

    def test_nn_mapping_uses_index(self):
        """When num_targets == len(target_dependency_objects), use index-matched target."""
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        targets = [_make_target(100010), _make_target(100020), _make_target(100030)]
        lut = _make_lookup(500001, Resource.Hook, targets)
        rlut = _make_reverse_lookup(Resource.Hook, {})
        url = "https://src.rossum.app/api/v1/hooks/500001"
        result = rr._replace_reference_in_url(
            source_dependency_url=url,
            lookup_table=lut,
            reverse_lookup_table=rlut,
            object_type=Resource.Hook,
            target_objects_count=3,
            target_index=2,
            use_dummy_references=True,
        )
        assert result == "https://tgt.rossum.app/api/v1/hooks/100030"

    def test_n1_mapping_uses_first(self):
        """When len(targets) != num_targets, use the first target."""
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        targets = [_make_target(100010)]  # single
        lut = _make_lookup(500001, Resource.Hook, targets)
        rlut = _make_reverse_lookup(Resource.Hook, {})
        url = "https://src.rossum.app/api/v1/hooks/500001"
        result = rr._replace_reference_in_url(
            source_dependency_url=url,
            lookup_table=lut,
            reverse_lookup_table=rlut,
            object_type=Resource.Hook,
            target_objects_count=3,  # 3 parent targets, but 1 hook target => all use hook[0]
            target_index=1,
            use_dummy_references=True,
        )
        assert result == "https://tgt.rossum.app/api/v1/hooks/100010"

    def test_uses_remote_id_when_available(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        target = _make_target(999999)
        # Even though target.id = 999999, the actual remote url has different id
        target.data_from_remote = {
            "url": "https://tgt.rossum.app/api/v1/hooks/555555",
            "id": 555555,
        }
        lut = _make_lookup(500001, Resource.Hook, [target])
        rlut = _make_reverse_lookup(Resource.Hook, {})
        url = "https://src.rossum.app/api/v1/hooks/500001"
        result = rr._replace_reference_in_url(
            source_dependency_url=url,
            lookup_table=lut,
            reverse_lookup_table=rlut,
            object_type=Resource.Hook,
            target_objects_count=1,
            target_index=0,
            use_dummy_references=True,
        )
        assert result == "https://tgt.rossum.app/api/v1/hooks/555555"


class TestReplaceReferenceUrl:
    def test_replaces_in_place(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        lut = _make_lookup(500001, Resource.Hook, [_make_target(999999)])
        rlut = _make_reverse_lookup(Resource.Hook, {})
        obj = {"dependency": "https://src.rossum.app/api/v1/hooks/500001"}
        rr.replace_reference_url(
            object=obj,
            target_index=0,
            target_objects_count=1,
            dependency_name="dependency",
            lookup_table=lut,
            reverse_lookup_table=rlut,
            object_type=Resource.Hook,
            use_dummy_references=True,
        )
        assert obj["dependency"] == "https://tgt.rossum.app/api/v1/hooks/999999"

    def test_allow_empty_reference_pops_none(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        obj = {"dependency": None}
        rr.replace_reference_url(
            object=obj,
            target_index=0,
            target_objects_count=1,
            dependency_name="dependency",
            lookup_table={},
            reverse_lookup_table={},
            object_type=Resource.Hook,
            use_dummy_references=True,
            allow_empty_reference=True,
        )
        assert "dependency" not in obj

    def test_missing_mapping_raises(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        obj = {"dependency": "https://src.rossum.app/api/v1/hooks/500099"}
        with pytest.raises(Exception):
            rr.replace_reference_url(
                object=obj,
                target_index=0,
                target_objects_count=1,
                dependency_name="dependency",
                lookup_table={},
                reverse_lookup_table={},
                object_type=Resource.Hook,
                use_dummy_references=True,
            )


class TestReplaceListOfReferenceUrls:
    def test_replaces_all(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        lut = {
            500001: {Resource.Hook: [_make_target(100100)]},
            500002: {Resource.Hook: [_make_target(200200)]},
        }
        rlut = _make_reverse_lookup(Resource.Hook, {})
        obj = {
            "hooks": [
                "https://src.rossum.app/api/v1/hooks/500001",
                "https://src.rossum.app/api/v1/hooks/500002",
            ]
        }
        rr.replace_list_of_reference_urls(
            object=obj,
            target_index=0,
            target_objects_count=1,
            dependency_name="hooks",
            object_type=Resource.Hook,
            lookup_table=lut,
            reverse_lookup_table=rlut,
            use_dummy_references=True,
        )
        assert obj["hooks"] == [
            "https://tgt.rossum.app/api/v1/hooks/100100",
            "https://tgt.rossum.app/api/v1/hooks/200200",
        ]

    def test_skip_unmapped_by_default(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        lut = {500001: {Resource.Hook: [_make_target(100100)]}}
        rlut = _make_reverse_lookup(Resource.Hook, {})
        obj = {
            "hooks": [
                "https://src.rossum.app/api/v1/hooks/500001",
                "https://src.rossum.app/api/v1/hooks/700999",  # not mapped
            ]
        }
        rr.replace_list_of_reference_urls(
            object=obj,
            target_index=0,
            target_objects_count=1,
            dependency_name="hooks",
            object_type=Resource.Hook,
            lookup_table=lut,
            reverse_lookup_table=rlut,
            use_dummy_references=True,
        )
        assert obj["hooks"] == ["https://tgt.rossum.app/api/v1/hooks/100100"]

    def test_keep_unmapped_when_flag_set(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        lut = {500001: {Resource.Hook: [_make_target(100100)]}}
        rlut = _make_reverse_lookup(Resource.Hook, {})
        obj = {
            "hooks": [
                "https://src.rossum.app/api/v1/hooks/500001",
                "https://src.rossum.app/api/v1/hooks/700999",
            ]
        }
        rr.replace_list_of_reference_urls(
            object=obj,
            target_index=0,
            target_objects_count=1,
            dependency_name="hooks",
            object_type=Resource.Hook,
            lookup_table=lut,
            reverse_lookup_table=rlut,
            use_dummy_references=True,
            keep_dependencies_without_equivalent=True,
        )
        # The unmapped URL must still be in the list
        assert "https://src.rossum.app/api/v1/hooks/700999" in obj["hooks"]


class TestReverseTargetReferenceIntoSource:
    def test_replaces_target_ids_in_string(self):
        rlut = _make_reverse_lookup(Resource.Hook, {100: 1, 200: 2})
        value = "hook:100 and hook:200"
        result = ReferenceReplacer.reverse_target_reference_into_source(
            value=value,
            reference_type=Resource.Hook,
            reverse_lookup_table=rlut,
            source_base_url="https://src/api/v1",
            target_base_url="https://tgt/api/v1",
        )
        assert "1" in result
        assert "2" in result

    def test_replaces_base_url(self):
        rlut = _make_reverse_lookup(Resource.Hook, {100: 1})
        value = "https://tgt/api/v1/hooks/100"
        result = ReferenceReplacer.reverse_target_reference_into_source(
            value=value,
            reference_type=Resource.Hook,
            reverse_lookup_table=rlut,
            source_base_url="https://src/api/v1",
            target_base_url="https://tgt/api/v1",
        )
        assert result == "https://src/api/v1/hooks/1"

    def test_recurses_into_list(self):
        rlut = _make_reverse_lookup(Resource.Hook, {100: 1})
        values = ["a", "100", {"key": "100"}]
        result = ReferenceReplacer.reverse_target_reference_into_source(
            value=values,
            reference_type=Resource.Hook,
            reverse_lookup_table=rlut,
            source_base_url="https://src/api/v1",
            target_base_url="https://tgt/api/v1",
        )
        assert result[1] == "1"
        assert result[2] == {"key": "1"}

    def test_recurses_into_dict(self):
        rlut = _make_reverse_lookup(Resource.Hook, {100: 1})
        value = {"a": "100", "b": {"c": "100"}}
        result = ReferenceReplacer.reverse_target_reference_into_source(
            value=value,
            reference_type=Resource.Hook,
            reverse_lookup_table=rlut,
            source_base_url="https://src/api/v1",
            target_base_url="https://tgt/api/v1",
        )
        assert result == {"a": "1", "b": {"c": "1"}}


class TestReverseUnknownReferenceType:
    def test_wraps_value(self):
        assert ReferenceReplacer.reverse_unknown_reference_type(42) == "UNKNOWN_REFERENCE(42)"
        assert ReferenceReplacer.reverse_unknown_reference_type("abc") == "UNKNOWN_REFERENCE(abc)"


class TestReplaceUnstructuredAttributes:
    def test_replaces_id_in_settings(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        lut = _make_lookup(1, Resource.Hook, [_make_target(99)])
        target_object = {
            "name": "hook",
            "settings": {"some_hook_ref": 1},
        }
        rr.replace_references_in_unstructured_attributes(
            target_object_label="hook label",
            target_object=target_object,
            lookup_table=lut,
            target_object_index=0,
            num_targets=1,
        )
        assert target_object["settings"]["some_hook_ref"] == 99

    def test_skips_when_no_overlap(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        lut = _make_lookup(1, Resource.Hook, [_make_target(99)])
        target_object = {"settings": {"foo": "bar"}}
        rr.replace_references_in_unstructured_attributes(
            target_object_label="hook",
            target_object=target_object,
            lookup_table=lut,
            target_object_index=0,
            num_targets=1,
        )
        assert target_object["settings"]["foo"] == "bar"

    def test_actions_exact_match_preserves_uuids(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        lut = _make_lookup(1, Resource.Hook, [_make_target(99)])
        target_object = {
            "actions": [{"id": "some-uuid-1-abc"}],  # contains '1' but is not reference
        }
        rr.replace_references_in_unstructured_attributes(
            target_object_label="hook",
            target_object=target_object,
            lookup_table=lut,
            target_object_index=0,
            num_targets=1,
        )
        # Should NOT be modified because "actions.id" is in EXACT_MATCH_PATHS
        # and the value is not exactly "1"
        assert target_object["actions"][0]["id"] == "some-uuid-1-abc"

    def test_actions_exact_match_replaces_bare_id(self):
        rr = ReferenceReplacer(parent_object_reference=_make_parent(), type=Resource.Hook)
        lut = _make_lookup(1, Resource.Hook, [_make_target(99)])
        target_object = {"actions": [{"id": "1"}]}
        rr.replace_references_in_unstructured_attributes(
            target_object_label="hook",
            target_object=target_object,
            lookup_table=lut,
            target_object_index=0,
            num_targets=1,
        )
        assert target_object["actions"][0]["id"] == "99"
