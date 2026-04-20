"""Tests for utils/consts.py - pure module-level constants, enums, and small utilities."""

from deployment_manager.utils.consts import (
    API_SUFFIX_RE,
    ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD,
    ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD,
    GIT_CHARACTERS,
    MAPPING_SELECTED_ATTRIBUTE,
    MIGRATE_PLANNING_MODE_OBJECT_PLACEHOLDER,
    QUEUE_ENGINE_ATTRIBUTES,
    CustomResource,
    Settings,
    display_error,
    display_info,
    display_warning,
    settings,
)
from rossum_api.domain_logic.resources import Resource


class TestConstants:
    def test_attribute_override_keywords_distinct(self):
        assert (
            ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD
            != ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD
        )

    def test_prd_ref_keyword_value(self):
        """$prd_ref is the documented attribute-override keyword for target references.

        The constant is reserved in `consts.py` but not yet wired into
        AttributeOverrider — when used in a deploy file today, it's treated
        as a literal string override. This test locks the value so future
        integration doesn't silently change it.
        """
        assert ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD == "$prd_ref"

    def test_source_value_keyword_value(self):
        """$source_value references the original source value (documented feature, reserved constant)."""
        assert ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD == "$source_value"

    def test_mapping_selected_attribute(self):
        assert MAPPING_SELECTED_ATTRIBUTE == "selected"

    def test_migrate_placeholder(self):
        assert "ID" in MIGRATE_PLANNING_MODE_OBJECT_PLACEHOLDER

    def test_queue_engine_attrs(self):
        assert set(QUEUE_ENGINE_ATTRIBUTES) == {"dedicated_engine", "generic_engine"}


class TestApiSuffixRegex:
    def test_matches_standard_suffix(self):
        assert API_SUFFIX_RE.search("https://api.rossum.ai/api/v1") is not None

    def test_matches_v2(self):
        assert API_SUFFIX_RE.search("https://api.rossum.ai/api/v2") is not None

    def test_no_match_without_api_prefix(self):
        assert API_SUFFIX_RE.search("https://api.rossum.ai/v1") is None

    def test_no_match_trailing_slash(self):
        # regex is anchored at end ($); trailing slash fails
        assert API_SUFFIX_RE.search("https://api.rossum.ai/api/v1/") is None


class TestGitCharacters:
    def test_values(self):
        assert GIT_CHARACTERS.DELETED == "D"
        assert GIT_CHARACTERS.UPDATED == "M"
        assert GIT_CHARACTERS.CREATED == "??"
        assert GIT_CHARACTERS.CREATED_STAGED == "A"

    def test_is_string_enum(self):
        # Works as a string directly
        assert f"{GIT_CHARACTERS.DELETED}-code" == "D-code"


class TestCustomResource:
    def test_label_value(self):
        assert CustomResource.Label.value == "labels"

    def test_workflow_values(self):
        assert CustomResource.Workflow.value == "workflows"
        assert CustomResource.WorkflowStep.value == "workflow_steps"


class TestSettingsDefaults:
    def test_command_names_distinct(self):
        names = {
            Settings.UPDATE_COMMAND_NAME,
            Settings.INITIALIZE_COMMAND_NAME,
            Settings.DOWNLOAD_COMMAND_NAME,
            Settings.UPLOAD_COMMAND_NAME,
            Settings.PURGE_COMMAND_NAME,
            Settings.DEPLOY_COMMAND_NAME,
            Settings.DOCUMENT_COMMAND_NAME,
            Settings.LLM_CHAT_COMMAND_NAME,
            Settings.HOOK_COMMAND_NAME,
        }
        # No two commands collide
        assert len(names) == 9

    def test_deploy_keys_distinct(self):
        deploy_keys = {
            Settings.DEPLOY_KEY_WORKSPACES,
            Settings.DEPLOY_KEY_QUEUES,
            Settings.DEPLOY_KEY_SCHEMA,
            Settings.DEPLOY_KEY_RULES,
            Settings.DEPLOY_KEY_INBOX,
            Settings.DEPLOY_KEY_HOOKS,
            Settings.DEPLOY_KEY_LABELS,
            Settings.DEPLOY_KEY_EMAIL_TEMPLATES,
            Settings.DEPLOY_KEY_ENGINES,
        }
        assert len(deploy_keys) == 9

    def test_non_pulled_keys_queue_includes_counts(self):
        assert "counts" in Settings.NON_PULLED_KEYS_PER_OBJECT[Resource.Queue]

    def test_non_diffed_for_hook_includes_guide(self):
        assert "guide" in Settings.DEPLOY_NON_DIFFED_KEYS[Resource.Hook]

    def test_cross_org_non_diffed_includes_engines(self):
        cross = Settings.DEPLOY_CROSS_ORG_NON_DIFFED_KEYS[Resource.Queue]
        assert "workflows" in cross
        assert "dedicated_engine" in cross

    def test_deploy_ignored_dirs(self):
        for expected in (".git", "deploy_files", "deploy_secrets"):
            assert expected in Settings.DEPLOY_IGNORED_DIRS


class TestSettingsSingleton:
    def test_initialized(self):
        # settings is the module-level singleton; should always be non-None once imported
        assert settings is not None

    def test_has_concurrency(self):
        assert settings.CONCURRENCY >= 1


class TestDisplayHelpers:
    def test_display_error_runs(self, capsys):
        display_error("err message")

    def test_display_warning_runs(self, capsys):
        display_warning("warn")

    def test_display_info_runs(self, capsys):
        display_info("info")


class TestSettingsApiUrl:
    def test_source_url_strips_trailing_slash(self, monkeypatch):
        original = settings.SOURCE_API_BASE
        try:
            settings.SOURCE_API_BASE = "https://api.rossum.ai/api/v1/"
            assert settings.SOURCE_API_URL == "https://api.rossum.ai/api/v1"
        finally:
            settings.SOURCE_API_BASE = original

    def test_target_url_strips_trailing_slash(self):
        original = settings.TARGET_API_BASE
        try:
            settings.TARGET_API_BASE = "https://tgt.rossum.ai/api/v1/"
            assert settings.TARGET_API_URL == "https://tgt.rossum.ai/api/v1"
        finally:
            settings.TARGET_API_BASE = original
