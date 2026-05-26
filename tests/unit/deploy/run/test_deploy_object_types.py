"""Tests for the individual deploy_objects types: classification flags, skipping,
non-creatable email templates, etc."""

import pytest
from rossum_api.domain_logic.resources import Resource

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

    def test_base_path_defaults_to_none(self):
        et = EmailTemplateDeployObject(id=1, name="t")
        assert et.base_path is None

    def test_path_uses_base_path_when_set(self):
        # Standalone email template (selected in deploy file) reads from its queue's
        # email_templates/ dir, reconstructed from base_path + name + id.
        et = EmailTemplateDeployObject(
            id=42,
            name="Welcome",
            base_path="src/primary/workspaces/W_[5]/queues/Q_[1]/email_templates",
        )
        assert str(et.path) == "src/primary/workspaces/W_[5]/queues/Q_[1]/email_templates/Welcome_[42].json"


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


class TestRuleExistingTargetIds:
    """`get_existing_target_ids` reads previously-deployed target IDs from the deploy state
    (so repeat deploys UPDATE the existing target rather than creating a duplicate)."""

    def test_returns_target_id_from_deploy_state(self):
        from types import SimpleNamespace

        rule = RuleDeployObject(id=1, name="r")
        rule.deploy_file = SimpleNamespace(
            deploy_state=SimpleNamespace(labels={42: SimpleNamespace(deployments={99: object()})}),
        )
        result = rule.get_existing_target_ids(CustomResource.Label, 42)
        assert result == [99]

    def test_returns_all_target_ids_for_multi_target(self):
        # Unlike the old .auto single-target mapping, the deploy state preserves every target.
        from types import SimpleNamespace

        rule = RuleDeployObject(id=1, name="r")
        rule.deploy_file = SimpleNamespace(
            deploy_state=SimpleNamespace(
                email_templates={7: SimpleNamespace(deployments={11: object(), 22: object()})}
            ),
        )
        result = rule.get_existing_target_ids(Resource.EmailTemplate, 7)
        assert sorted(result) == [11, 22]

    def test_returns_empty_when_not_previously_deployed(self):
        from types import SimpleNamespace

        rule = RuleDeployObject(id=1, name="r")
        rule.deploy_file = SimpleNamespace(deploy_state=SimpleNamespace(labels={}))
        result = rule.get_existing_target_ids(CustomResource.Label, 42)
        assert result == []

    def test_backwards_compat_resolves_target_from_v2_13_1_deploy_state(self):
        """Backwards compat: a label/email template deployed under v2.13.1 (which wrote the
        .auto/ mappings file AND the deploy state) must still resolve to its existing target
        after the .auto/ mechanism was dropped, so upgraded users don't get duplicates.

        Deserializes a deploy-state in the exact on-disk shape v2.13.1 wrote (string keys,
        int-coerced by the model) through the real DeployState model - the same thing
        load_deploy_state does after reading the file - and checks get_existing_target_ids
        (now the only resolver) finds the prior target.
        """
        import json
        from types import SimpleNamespace

        from deployment_manager.commands.deploy.subcommands.run.merge.state import DeployState

        # source label 4402 -> target 14993, source email template 500 -> targets 11 & 22,
        # exactly as save_deploy_state persisted them in v2.13.1.
        state_json = (
            '{"labels": {"4402": {"deployments": {"14993": {"last_applied": '
            '{"forward": {"name": "Export Completed"}}}}}}, '
            '"email_templates": {"500": {"deployments": '
            '{"11": {"last_applied": {}}, "22": {"last_applied": {}}}}}}'
        )
        deploy_state = DeployState(**json.loads(state_json))

        rule = RuleDeployObject(id=1, name="r")
        rule.deploy_file = SimpleNamespace(deploy_state=deploy_state)

        assert rule.get_existing_target_ids(CustomResource.Label, 4402) == [14993]
        assert sorted(rule.get_existing_target_ids(Resource.EmailTemplate, 500)) == [11, 22]
        # A source never deployed before still resolves to empty -> creates new (no false reuse)
        assert rule.get_existing_target_ids(CustomResource.Label, 9999) == []


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


@pytest.mark.asyncio
class TestRuleAutoLoadDedup:
    """A label/email template selected standalone must not be re-loaded (and re-fetched)
    by a rule that also references it — the standalone object already in the orchestrator wins."""

    async def test_standalone_label_not_reloaded_by_rule(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock

        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.label_deploy_object import (
            LabelDeployObject,
        )

        standalone = LabelDeployObject(id=42, name="Existing", data={"id": 42, "name": "Existing"})
        rule = RuleDeployObject(
            id=1,
            name="r",
            data={"actions": [{"type": "add_label", "payload": {"labels": ["https://api/v1/labels/42"]}}]},
        )
        fetch_one = AsyncMock()
        rule.deploy_file = SimpleNamespace(
            labels=[standalone],
            email_templates=[],
            queues=[],
            deploy_state=SimpleNamespace(labels={}, email_templates={}),
            source_client=SimpleNamespace(_http_client=SimpleNamespace(fetch_one=fetch_one)),
        )

        await rule.auto_load_action_dependencies()

        # Label already present (standalone) → rule must not fetch or duplicate it
        fetch_one.assert_not_called()
        assert len(rule.deploy_file.labels) == 1
        assert rule.deploy_file.labels[0] is standalone
