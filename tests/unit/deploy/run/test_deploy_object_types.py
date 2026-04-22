"""Tests for the individual deploy_objects types: classification flags, skipping,
non-creatable email templates, etc."""

import pytest

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.email_template_deploy_object import (
    NON_CREATABLE_EMAIL_TEMPLATE_TYPES,
    EmailTemplateDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.engine_deploy_object import (
    EngineDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.label_deploy_object import (
    LabelDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.rule_deploy_object import (
    RuleDeployObject,
)


# Trigger model rebuilds for forward refs
from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (  # noqa: F401
    DeployOrchestrator,
)
from deployment_manager.utils.consts import CustomResource
from rossum_api.domain_logic.resources import Resource


class TestNonCreatableEmailTemplates:
    def test_rejection_default_is_non_creatable(self):
        assert "rejection_default" in NON_CREATABLE_EMAIL_TEMPLATE_TYPES

    def test_no_processable_attachments_is_non_creatable(self):
        assert "email_with_no_processable_attachments" in NON_CREATABLE_EMAIL_TEMPLATE_TYPES


class TestEmailTemplateDeployObject:
    def test_default_non_creatable_flag(self):
        et = EmailTemplateDeployObject(id=1, name="t")
        assert et.non_creatable is False

    def test_type_is_email_template(self):
        et = EmailTemplateDeployObject(id=1, name="t")
        assert et.type == Resource.EmailTemplate


class TestLabelDeployObject:
    def test_type_is_custom_label(self):
        label = LabelDeployObject(id=1, name="label-1")
        assert label.type == CustomResource.Label


class TestEngineDeployObject:
    def test_default_fields(self):
        engine = EngineDeployObject(id=1, name="engine-a")
        assert engine.type == Resource.Engine
        assert engine.engine_field_deploy_objects == []
        assert engine.base_path == ""


class TestRuleDeployObject:
    def test_defaults(self):
        rule = RuleDeployObject(id=1, name="r1")
        assert rule.type == Resource.Rule
        assert rule.skipped is False
        assert rule.second_deploy_references_overridden is False


class TestRuleAutoMappingsLookup:
    """`get_target_ids_from_auto_mappings` checks auto_mappings file → deploy_state fallback."""

    def test_returns_from_auto_mappings_when_present(self):
        rule = RuleDeployObject(id=1, name="r")
        # Build a mock deploy_file with auto_mappings
        from types import SimpleNamespace

        rule.deploy_file = SimpleNamespace(
            auto_mappings={"labels": {42: 99}},
            deploy_state=SimpleNamespace(labels={}),
        )
        result = rule.get_target_ids_from_auto_mappings(CustomResource.Label, 42)
        assert result == [99]

    def test_returns_empty_when_no_mapping(self):
        rule = RuleDeployObject(id=1, name="r")
        from types import SimpleNamespace

        rule.deploy_file = SimpleNamespace(
            auto_mappings={},
            deploy_state=SimpleNamespace(labels={}),
        )
        result = rule.get_target_ids_from_auto_mappings(CustomResource.Label, 42)
        assert result == []


@pytest.mark.asyncio
class TestRuleSkipSchemaBased:
    async def test_skipped_when_schema_attribute_present(self):
        """A rule with schema attribute is deprecated and skipped during deploy."""
        from types import SimpleNamespace
        from unittest.mock import MagicMock

        rule = RuleDeployObject(
            id=1,
            name="r",
            data={"schema": "https://api/v1/schemas/1"},
        )
        rule.deploy_file = SimpleNamespace(
            is_same_org=True,
            no_rebase=False,
            auto_mappings={},
            deploy_state=SimpleNamespace(labels={}, email_templates={}),
            source_client=MagicMock(),
            yaml=SimpleNamespace(data={}),
        )
        # Patch the parent initialize_deploy_object to avoid full setup
        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import DeployObject

        original = DeployObject.initialize_deploy_object

        async def fake_init(self, deploy_file):
            self.deploy_file = deploy_file
            self.yaml_reference = {}
            self.ignored_attributes = []
            self.sort_list_attributes = []

        DeployObject.initialize_deploy_object = fake_init
        try:
            await rule.initialize_deploy_object(rule.deploy_file)
        finally:
            DeployObject.initialize_deploy_object = original

        assert rule.skipped is True
