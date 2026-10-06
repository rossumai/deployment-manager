"""Tests for the simpler logic in deploy_object subclasses (paths, yaml lookup,
auto-detect dependencies, etc.). Complements test_deploy_object_types.py."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from anyio import Path
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import DeployObject
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.email_template_deploy_object import (
    EmailTemplateDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.engine_deploy_object import (
    EngineDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.engine_field_deploy_object import (
    EngineFieldDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.inbox_deploy_object import (
    InboxDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.queue_deploy_object import (
    QueueDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.rule_deploy_object import (
    RuleDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.schema_deploy_object import (
    SchemaDeployObject,
)

# Trigger model rebuild for forward refs
from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (  # noqa: F401
    DeployOrchestrator,
)


class TestEmailTemplateNonCreatableDetection:
    def test_initialize_marks_non_creatable_for_rejection_default(self, monkeypatch):
        et = EmailTemplateDeployObject(id=1, name="t", data={"type": "rejection_default", "queue": ""})

        # The base class's initialize_deploy_object does a lot of setup we don't want here.
        # Patch it to a no-op that still sets the attributes the subclass mutates.
        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
            DeployObject,
        )

        async def fake_init(self, deploy_file):
            self.deploy_file = deploy_file
            self.ignored_attributes = []

        monkeypatch.setattr(DeployObject, "initialize_deploy_object", fake_init)

        import asyncio

        asyncio.run(et.initialize_deploy_object(deploy_file=SimpleNamespace()))
        assert et.non_creatable is True
        # Subclass extends ignored_attributes
        assert "organization" in et.ignored_attributes
        assert "triggers" in et.ignored_attributes

    def test_initialize_does_not_mark_creatable_template(self, monkeypatch):
        et = EmailTemplateDeployObject(id=1, name="t", data={"type": "custom"})

        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
            DeployObject,
        )

        async def fake_init(self, deploy_file):
            self.deploy_file = deploy_file
            self.ignored_attributes = []

        monkeypatch.setattr(DeployObject, "initialize_deploy_object", fake_init)

        import asyncio

        asyncio.run(et.initialize_deploy_object(deploy_file=SimpleNamespace()))
        assert et.non_creatable is False


@pytest.mark.asyncio
class TestEmailTemplateNonCreatableSkips:
    async def test_deploy_target_objects_skipped_when_non_creatable(self):
        et = EmailTemplateDeployObject(id=1, name="t")
        et.non_creatable = True
        # Should return without invoking parent — verify by injecting a sentinel attribute
        # The parent would touch self.targets; we simply check it returns silently.
        await et.deploy_target_objects("first_deploy_data")  # no error, no-op

    async def test_visualize_changes_skipped_when_non_creatable(self):
        et = EmailTemplateDeployObject(id=1, name="t")
        et.non_creatable = True
        await et.visualize_changes()  # no error, no-op


class TestEngineDeployObjectPath:
    def test_path_uses_base_path_when_set(self):
        engine = EngineDeployObject(id=1, name="eng", base_path="some/dir")
        assert str(engine.path).endswith("some/dir/engine.json")

    def test_path_falls_back_to_source_dir(self):
        engine = EngineDeployObject(id=42, name="my-engine")
        engine.deploy_file = SimpleNamespace(source_dir_path=Path("src"))
        # No base_path — uses source_dir_path / "engines" / "{name}_[id]" / "engine.json"
        assert str(engine.path).endswith("src/engines/my-engine_[42]/engine.json")


class TestEngineFieldDeployObject:
    def test_get_object_in_yaml_returns_none_without_parent(self):
        field = EngineFieldDeployObject(id=1, name="f")
        assert field.get_object_in_yaml() is None

    def test_get_object_in_yaml_finds_matching_field(self):
        field = EngineFieldDeployObject(id=42, name="f")
        engine = MagicMock()
        engine.yaml_reference = {"engine_fields": [{"id": 1}, {"id": 42, "name": "match"}]}
        field.parent_engine = engine
        result = field.get_object_in_yaml()
        assert result == {"id": 42, "name": "match"}

    def test_get_object_in_yaml_returns_none_when_not_found(self):
        field = EngineFieldDeployObject(id=99, name="f")
        engine = MagicMock()
        engine.yaml_reference = {"engine_fields": [{"id": 1}, {"id": 2}]}
        field.parent_engine = engine
        assert field.get_object_in_yaml() is None

    def test_path_with_parent_engine(self):
        field = EngineFieldDeployObject(id=10, name="my-field")
        engine = MagicMock()
        engine.path = Path("src/engines/eng_[1]/engine.json")
        field.parent_engine = engine
        assert str(field.path).endswith("src/engines/eng_[1]/engine_fields/my-field_[10].json")

    def test_path_without_parent_engine(self):
        field = EngineFieldDeployObject(id=10, name="my-field")
        field.deploy_file = SimpleNamespace(source_dir_path=Path("src"))
        assert str(field.path).endswith("src/engine_fields/my-field_[10].json")

    def test_update_targets_assigns_remote_id(self):
        field = EngineFieldDeployObject(id=1, name="f")
        from deployment_manager.commands.deploy.subcommands.run.models import Target

        target = Target(id=None)
        target.data_from_remote = {"id": 999}
        target.index = 0
        field.targets = [target]
        # No yaml_reference → does not blow up
        field.yaml_reference = None
        field.update_targets()
        assert target.id == 999

    def test_update_targets_writes_back_to_yaml(self):
        field = EngineFieldDeployObject(id=1, name="f")
        from deployment_manager.commands.deploy.subcommands.run.models import Target

        target = Target(id=None)
        target.data_from_remote = {"id": 7}
        target.attribute_override = {"name": "new"}
        target.index = 0
        field.targets = [target]
        field.yaml_reference = {"targets": [{"id": None, "attribute_override": {}}]}
        field.update_targets()
        assert field.yaml_reference["targets"][0]["id"] == 7
        assert field.yaml_reference["targets"][0]["attribute_override"] == {"name": "new"}

    def test_update_targets_skips_when_no_remote_data(self):
        field = EngineFieldDeployObject(id=1, name="f")
        from deployment_manager.commands.deploy.subcommands.run.models import Target

        target = Target(id="dummy")
        # No data_from_remote → skipped
        target.data_from_remote = None
        field.targets = [target]
        field.yaml_reference = None
        field.update_targets()
        # No id reassignment happened
        assert target.id == "dummy"


class TestInboxDeployObjectPath:
    def test_path_is_sibling_of_parent_queue(self):
        parent = MagicMock()
        parent.path = Path("src/workspaces/W_[1]/queues/Q_[2]/queue.json")
        inbox = InboxDeployObject(id=1, name="ignored")
        inbox.parent_queue = parent
        assert str(inbox.path).endswith("src/workspaces/W_[1]/queues/Q_[2]/inbox.json")

    def test_get_object_in_yaml_pulls_from_parent_queue(self):
        parent = MagicMock()
        parent.yaml_reference = {"inbox": {"id": 5, "name": "inb"}}
        inbox = InboxDeployObject(id=5, name="ignored")
        inbox.parent_queue = parent
        assert inbox.get_object_in_yaml() == {"id": 5, "name": "inb"}

    def test_get_object_in_yaml_returns_empty_when_inbox_not_in_parent(self):
        parent = MagicMock()
        parent.yaml_reference = {}
        inbox = InboxDeployObject(id=5, name="ignored")
        inbox.parent_queue = parent
        assert inbox.get_object_in_yaml() == {}


@pytest.mark.asyncio
class TestInboxInitializeTargetObjectData:
    async def test_inherits_parent_queue_name_when_no_override(self):
        from deployment_manager.commands.deploy.subcommands.run.models import Target

        parent = MagicMock()
        parent_target = Target(id=None)
        parent_target.attribute_override = {}
        parent.targets = [parent_target]

        inbox = InboxDeployObject(id=1, name="my-q-name")
        inbox.parent_queue = parent

        target = Target(id=None)
        target.attribute_override = {}
        target.index = 0
        data = {"name": "old", "email": "x@y.com"}
        await inbox.initialize_target_object_data(data, target)

        # Inbox name now matches parent queue name; email stripped
        assert data["name"] == "my-q-name"
        assert "email" not in data

    async def test_uses_parent_target_name_override_when_provided(self):
        from deployment_manager.commands.deploy.subcommands.run.models import Target

        parent = MagicMock()
        parent_target = Target(id=None)
        parent_target.attribute_override = {"name": "PROD-queue"}
        parent.targets = [parent_target]

        inbox = InboxDeployObject(id=1, name="src-q")
        inbox.parent_queue = parent

        target = Target(id=None)
        target.attribute_override = {}
        target.index = 0
        data = {"name": "old"}
        await inbox.initialize_target_object_data(data, target)

        assert target.attribute_override["name"] == "PROD-queue"

    async def test_keeps_explicit_inbox_name_override(self):
        from deployment_manager.commands.deploy.subcommands.run.models import Target

        parent = MagicMock()
        parent.targets = [Target(id=None)]
        inbox = InboxDeployObject(id=1, name="src-q")
        inbox.parent_queue = parent

        target = Target(id=None)
        target.attribute_override = {"name": "explicit-inbox-name"}
        target.index = 0
        data = {"name": "x"}
        await inbox.initialize_target_object_data(data, target)
        # User-provided override is preserved
        assert target.attribute_override["name"] == "explicit-inbox-name"


@pytest.mark.asyncio
class TestRuleAutoLoadActionDependencies:
    async def test_extracts_label_ids_from_actions(self, monkeypatch):
        # Fake fetch_one and a deploy_file with empty labels/email_templates lists
        rule = RuleDeployObject(
            id=1,
            name="r",
            data={
                "actions": [
                    {
                        "type": "add_label",
                        "payload": {"labels": ["https://api/v1/labels/100", "https://api/v1/labels/200"]},
                    },
                    {
                        "type": "remove_label",
                        # not a label-loading action type, won't trigger fetch
                        "payload": {"labels": ["https://api/v1/labels/300"]},
                    },
                ],
            },
        )
        rule.deploy_file = SimpleNamespace(
            labels=[],
            email_templates=[],
            queues=[],
            source_client=MagicMock(),
            deploy_state=SimpleNamespace(labels={}, email_templates={}),
            local_deploy=False,
        )
        rule.deploy_file.source_client._http_client = MagicMock()
        rule.deploy_file.source_client._http_client.fetch_one = AsyncMock(
            side_effect=lambda resource, id_: {"id": id_, "name": f"label-{id_}"}
        )

        # Patch LabelDeployObject.initialize_deploy_object to avoid heavy work
        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.label_deploy_object import (
            LabelDeployObject,
        )

        async def fake_init(self, deploy_file):
            self.deploy_file = deploy_file
            self.ignored_attributes = []

        monkeypatch.setattr(LabelDeployObject, "initialize_deploy_object", fake_init)

        await rule.auto_load_action_dependencies()
        loaded_ids = {label.id for label in rule.deploy_file.labels}
        assert loaded_ids == {100, 200}

    async def test_extracts_email_template_id_from_send_email(self, monkeypatch):
        rule = RuleDeployObject(
            id=1,
            name="r",
            data={
                "actions": [
                    {
                        "type": "send_email",
                        "payload": {"email_template": "https://api/v1/email_templates/77"},
                    },
                ],
            },
        )
        rule.deploy_file = SimpleNamespace(
            labels=[],
            email_templates=[],
            queues=[],
            source_client=MagicMock(),
            deploy_state=SimpleNamespace(labels={}, email_templates={}),
            local_deploy=False,
        )
        rule.deploy_file.source_client._http_client = MagicMock()
        rule.deploy_file.source_client._http_client.fetch_one = AsyncMock(
            return_value={"id": 77, "name": "send-email-template", "queue": None}
        )

        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.email_template_deploy_object import (
            EmailTemplateDeployObject,
        )

        async def fake_init(self, deploy_file):
            self.deploy_file = deploy_file
            self.ignored_attributes = []

        monkeypatch.setattr(EmailTemplateDeployObject, "initialize_deploy_object", fake_init)

        await rule.auto_load_action_dependencies()
        assert len(rule.deploy_file.email_templates) == 1
        assert rule.deploy_file.email_templates[0].id == 77

    async def test_dedupes_label_ids_across_actions(self, monkeypatch):
        # Two actions both reference label 100 → only one fetch
        rule = RuleDeployObject(
            id=1,
            name="r",
            data={
                "actions": [
                    {"type": "add_label", "payload": {"labels": ["https://api/v1/labels/100"]}},
                    {"type": "add_remove_label", "payload": {"labels": ["https://api/v1/labels/100"]}},
                ],
            },
        )
        rule.deploy_file = SimpleNamespace(
            labels=[],
            email_templates=[],
            queues=[],
            source_client=MagicMock(),
            deploy_state=SimpleNamespace(labels={}, email_templates={}),
            local_deploy=False,
        )
        rule.deploy_file.source_client._http_client = MagicMock()
        fetch_mock = AsyncMock(return_value={"id": 100, "name": "L"})
        rule.deploy_file.source_client._http_client.fetch_one = fetch_mock

        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.label_deploy_object import (
            LabelDeployObject,
        )

        async def fake_init(self, deploy_file):
            self.deploy_file = deploy_file
            self.ignored_attributes = []

        monkeypatch.setattr(LabelDeployObject, "initialize_deploy_object", fake_init)

        await rule.auto_load_action_dependencies()
        assert len(rule.deploy_file.labels) == 1
        assert fetch_mock.await_count == 1

    async def test_local_deploy_loads_dependencies_from_local_files(self, monkeypatch, tmp_path):
        """With --ld dependencies are read from the locally pulled files, never from the source org."""
        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.email_template_deploy_object import (
            EmailTemplateDeployObject,
        )
        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.label_deploy_object import (
            LabelDeployObject,
        )

        # Recreate the pull layout: labels/<name>_[id].json and
        # workspaces/<ws>/queues/<queue>/email_templates/<name>_[id].json
        # (the conftest tmp_path fixture is an anyio.Path, so file ops are awaited)
        labels_dir = tmp_path / "labels"
        await labels_dir.mkdir(parents=True)
        await (labels_dir / "MyLabel_[100].json").write_text(json.dumps({"id": 100, "name": "MyLabel"}))

        et_dir = tmp_path / "workspaces" / "WS_[1]" / "queues" / "Q_[2]" / "email_templates"
        await et_dir.mkdir(parents=True)
        await (et_dir / "Welcome_[77].json").write_text(
            json.dumps({"id": 77, "name": "Welcome", "queue": "https://api/v1/queues/2"})
        )

        rule = RuleDeployObject(
            id=1,
            name="r",
            data={
                "actions": [
                    {"type": "add_label", "payload": {"labels": ["https://api/v1/labels/100"]}},
                    {"type": "send_email", "payload": {"email_template": "https://api/v1/email_templates/77"}},
                ],
            },
        )
        fetch_mock = AsyncMock()
        source_client = MagicMock()
        source_client._http_client = MagicMock()
        source_client._http_client.fetch_one = fetch_mock
        rule.deploy_file = SimpleNamespace(
            labels=[],
            email_templates=[],
            queues=[],
            source_client=source_client,
            source_dir_path=tmp_path,
            auto_mappings={},
            deploy_state=SimpleNamespace(labels={}, email_templates={}),
            local_deploy=True,
        )

        async def fake_init(self, deploy_file):
            self.deploy_file = deploy_file
            self.ignored_attributes = []

        monkeypatch.setattr(LabelDeployObject, "initialize_deploy_object", fake_init)
        monkeypatch.setattr(EmailTemplateDeployObject, "initialize_deploy_object", fake_init)

        await rule.auto_load_action_dependencies()

        # Loaded from local files; the source org was never queried
        fetch_mock.assert_not_awaited()
        assert {label.id for label in rule.deploy_file.labels} == {100}
        assert {et.id for et in rule.deploy_file.email_templates} == {77}


@pytest.mark.asyncio
class TestSubObjectComparison:
    """Schemas and engine fields are not in the orchestrator's object list, so parents must compare them."""

    @pytest.fixture
    def compared(self, monkeypatch):
        compared = []
        # Flags each object should raise when compared, keyed by (type, id)
        outcomes = {}

        async def fake_compare(self):
            compared.append((self.type, self.id))
            for flag in outcomes.get((self.type, self.id), []):
                setattr(self, flag, True)

        monkeypatch.setattr(DeployObject, "compare_target_objects", fake_compare)
        return SimpleNamespace(calls=compared, outcomes=outcomes)

    def make_queue(self):
        schema = SchemaDeployObject(id=2, name="s")
        inbox = InboxDeployObject(id=3, name="i")
        return QueueDeployObject.model_construct(
            id=1, name="q", base_path="", schema_deploy_object=schema, inbox_deploy_object=inbox
        )

    async def test_queue_compares_schema_but_not_inbox(self, compared):
        queue = self.make_queue()
        await queue.compare_target_objects()
        assert compared.calls == [(Resource.Queue, 1), (Resource.Schema, 2)]

    async def test_queue_absorbs_schema_rebase_and_conflict(self, compared):
        compared.outcomes[(Resource.Schema, 2)] = ["rebase_detected", "conflict_detected"]
        queue = self.make_queue()
        await queue.compare_target_objects()
        assert queue.rebase_detected and queue.conflict_detected

    async def test_queue_flags_untouched_without_schema_drift(self, compared):
        queue = self.make_queue()
        await queue.compare_target_objects()
        assert not queue.rebase_detected and not queue.conflict_detected

    async def test_engine_compares_all_engine_fields(self, compared):
        engine = EngineDeployObject(id=1, name="e")
        engine.engine_field_deploy_objects = [
            EngineFieldDeployObject(id=10, name="a"),
            EngineFieldDeployObject(id=11, name="b"),
        ]
        await engine.compare_target_objects()
        assert compared.calls == [(Resource.Engine, 1), (Resource.EngineField, 10), (Resource.EngineField, 11)]

    async def test_engine_absorbs_engine_field_rebase(self, compared):
        compared.outcomes[(Resource.EngineField, 11)] = ["rebase_detected"]
        engine = EngineDeployObject(id=1, name="e")
        engine.engine_field_deploy_objects = [
            EngineFieldDeployObject(id=10, name="a"),
            EngineFieldDeployObject(id=11, name="b"),
        ]
        await engine.compare_target_objects()
        assert engine.rebase_detected and not engine.conflict_detected


@pytest.mark.asyncio
class TestPlanChangesOnly:
    def make_field(self, monkeypatch, remote: dict, plan: dict, exists_on_remote: bool, changes_only: bool):
        from deployment_manager.commands.deploy.subcommands.run.models import Target

        field = EngineFieldDeployObject(id=1, name="f")
        target = Target(id=2)
        target.exists_on_remote = exists_on_remote
        target.visualized_plan_data = plan
        field.targets = [target]
        field.deploy_file = SimpleNamespace(changes_only=changes_only, unchanged_plan_objects_count=0)
        monkeypatch.setattr(EngineFieldDeployObject, "get_remote_object", AsyncMock(return_value=dict(remote)))
        printed = []
        monkeypatch.setattr(
            "deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object.pprint",
            printed.append,
        )
        return field, printed

    async def test_unchanged_object_hidden(self, monkeypatch):
        data = {"id": 2, "name": "f", "label": "x"}
        field, printed = self.make_field(monkeypatch, data, dict(data), exists_on_remote=True, changes_only=True)
        await field.visualize_changes()
        assert printed == []
        assert field.deploy_file.unchanged_plan_objects_count == 1

    async def test_changed_object_shown(self, monkeypatch):
        remote = {"id": 2, "name": "f", "label": "x"}
        plan = {"id": 2, "name": "f", "label": "y"}
        field, printed = self.make_field(monkeypatch, remote, plan, exists_on_remote=True, changes_only=True)
        await field.visualize_changes()
        assert len(printed) == 1
        assert field.deploy_file.unchanged_plan_objects_count == 0

    async def test_created_object_always_shown(self, monkeypatch):
        field, printed = self.make_field(
            monkeypatch, {}, {"id": 2, "name": "f"}, exists_on_remote=False, changes_only=True
        )
        await field.visualize_changes()
        assert len(printed) == 1

    async def test_unchanged_object_shown_without_flag(self, monkeypatch):
        data = {"id": 2, "name": "f", "label": "x"}
        field, printed = self.make_field(monkeypatch, data, dict(data), exists_on_remote=True, changes_only=False)
        await field.visualize_changes()
        assert len(printed) == 1


@pytest.mark.asyncio
class TestReloadLocalData:
    """After a conflict is resolved on disk, the reload must re-read the file instead of keeping cached data."""

    async def test_reinitialize_picks_up_file_resolved_on_disk(self, tmp_path, monkeypatch):
        await (Path(tmp_path) / "engine.json").write_text(json.dumps({"id": 1, "name": "e", "description": "resolved"}))
        engine = EngineDeployObject(id=1, name="e", base_path=str(tmp_path), data={"id": 1, "description": "stale"})
        engine.deploy_file = SimpleNamespace(is_same_org=True, no_rebase=False)
        monkeypatch.setattr(EngineDeployObject, "get_object_in_yaml", lambda self: None)

        await engine.reload_local_data()
        await engine.initialize_deploy_object(deploy_file=engine.deploy_file)

        assert engine.data["description"] == "resolved"

    async def test_keeps_data_without_local_file(self, tmp_path):
        engine = EngineDeployObject(id=1, name="e", base_path=str(tmp_path), data={"id": 1})
        await engine.reload_local_data()
        assert engine.data == {"id": 1}

    async def test_queue_reloads_schema(self, monkeypatch):
        reloaded = []

        async def fake_reload(self):
            reloaded.append((self.type, self.id))

        monkeypatch.setattr(DeployObject, "reload_local_data", fake_reload)
        queue = QueueDeployObject.model_construct(
            id=1,
            name="q",
            base_path="",
            schema_deploy_object=SchemaDeployObject(id=2, name="s"),
            inbox_deploy_object=InboxDeployObject(id=3, name="i"),
        )
        await queue.reload_local_data()
        assert reloaded == [(Resource.Queue, 1), (Resource.Schema, 2)]

    async def test_engine_reloads_engine_fields(self, monkeypatch):
        reloaded = []

        async def fake_reload(self):
            reloaded.append((self.type, self.id))

        monkeypatch.setattr(DeployObject, "reload_local_data", fake_reload)
        engine = EngineDeployObject(id=1, name="e")
        engine.engine_field_deploy_objects = [EngineFieldDeployObject(id=10, name="a")]
        await engine.reload_local_data()
        assert reloaded == [(Resource.Engine, 1), (Resource.EngineField, 10)]
