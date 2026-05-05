from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.merge.detect_reference import (
    FIELD_TO_RESOURCE,
    ROSSUM_URL_RE,
    ReferenceDetectionStatus,
    detect_reference_with_type,
)


class TestDetectReferenceByFieldName:
    def test_queues_field(self):
        status, resource = detect_reference_with_type([1, 2], field_name="queues")
        assert status == ReferenceDetectionStatus.DEFINITELY_REFERENCE
        assert resource == Resource.Queue

    def test_schema_field(self):
        status, resource = detect_reference_with_type(1, field_name="schema")
        assert status == ReferenceDetectionStatus.DEFINITELY_REFERENCE
        assert resource == Resource.Schema

    def test_hook_template_field(self):
        status, resource = detect_reference_with_type(5, field_name="hook_template")
        assert status == ReferenceDetectionStatus.DEFINITELY_REFERENCE
        # hook_templates is a raw string, not a Resource enum value
        assert resource == "hook_templates"

    def test_all_known_fields_present(self):
        for field in (
            "queues",
            "run_after",
            "schema",
            "inbox",
            "webhooks",
            "workspace",
            "users",
            "token_owner",
            "hook_template",
            "organization",
        ):
            status, _ = detect_reference_with_type(1, field_name=field)
            assert status == ReferenceDetectionStatus.DEFINITELY_REFERENCE

    def test_unknown_field_falls_through(self):
        status, _ = detect_reference_with_type("hello world", field_name="random")
        assert status == ReferenceDetectionStatus.DEFINITELY_NOT


class TestRossumUrlRegex:
    def test_matches_api_url(self):
        m = ROSSUM_URL_RE.match("https://mysub.api.rossum.ai/api/v1/queues/42")
        assert m is not None
        assert m.group(1) == "queues"
        assert m.group(2) == "42"

    def test_matches_bare_api_rossum(self):
        m = ROSSUM_URL_RE.match("https://api.rossum.ai/v1/queues/42")
        assert m is not None

    def test_does_not_match_non_rossum(self):
        assert ROSSUM_URL_RE.match("https://example.com/api/v1/queues/1") is None


class TestDetectReferenceByUrl:
    def test_valid_rossum_queue_url(self):
        status, resource = detect_reference_with_type(
            "https://elis.api.rossum.ai/api/v1/queues/42"
        )
        assert status == ReferenceDetectionStatus.DEFINITELY_REFERENCE
        assert resource == Resource.Queue

    def test_unknown_resource_in_url(self):
        status, resource = detect_reference_with_type(
            "https://elis.api.rossum.ai/api/v1/some_weird/42"
        )
        assert status == ReferenceDetectionStatus.DEFINITELY_NOT
        assert resource is None


class TestDetectReferenceByHeuristic:
    def test_small_int_unknown(self):
        status, resource = detect_reference_with_type(123)
        assert status == ReferenceDetectionStatus.UNKNOWN

    def test_numeric_string_unknown(self):
        status, resource = detect_reference_with_type("123")
        assert status == ReferenceDetectionStatus.UNKNOWN

    def test_too_large_number(self):
        # Outside 1..999_999_999 range -> falls through to DEFINITELY_NOT
        status, resource = detect_reference_with_type(10_000_000_000)
        assert status == ReferenceDetectionStatus.DEFINITELY_NOT

    def test_zero_not_reference(self):
        status, resource = detect_reference_with_type(0)
        assert status == ReferenceDetectionStatus.DEFINITELY_NOT


class TestDetectReferenceNonRef:
    def test_list_is_not_ref(self):
        status, _ = detect_reference_with_type([1, 2])
        assert status == ReferenceDetectionStatus.DEFINITELY_NOT

    def test_dict_is_not_ref(self):
        status, _ = detect_reference_with_type({"a": 1})
        assert status == ReferenceDetectionStatus.DEFINITELY_NOT

    def test_bool_is_not_ref(self):
        status, _ = detect_reference_with_type(True)
        assert status == ReferenceDetectionStatus.DEFINITELY_NOT

    def test_none_is_not_ref(self):
        status, _ = detect_reference_with_type(None)
        assert status == ReferenceDetectionStatus.DEFINITELY_NOT


class TestFieldToResourceMapping:
    def test_mapping_has_expected_keys(self):
        for field in ("queues", "schema", "inbox", "workspace", "users", "organization"):
            assert field in FIELD_TO_RESOURCE
