from anyio import Path
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.upload.directory import ChangedObject
from deployment_manager.commands.upload.plan import (
    CREATE_TYPE_ORDER,
    DELETE_TYPE_ORDER,
    classify,
    determine_type_from_local_path,
    is_new_path,
    order_creates,
    order_deletes,
    validate,
)
from deployment_manager.utils.consts import GIT_CHARACTERS

ORG = Path("source")


def make_obj(op, path: str, data: dict | None = None) -> ChangedObject:
    return ChangedObject(operation=op, path=Path(path), data=data or {})


class TestDetermineTypeFromLocalPath:
    def test_workspace(self):
        assert (
            determine_type_from_local_path(Path("workspaces/AP_[]/workspace.json"))
            == Resource.Workspace
        )

    def test_queue_schema_inbox_under_placeholder_parent(self):
        assert determine_type_from_local_path(Path("workspaces/AP_[1]/queues/Inv_[]/queue.json")) == Resource.Queue
        assert determine_type_from_local_path(Path("workspaces/AP_[1]/queues/Inv_[]/schema.json")) == Resource.Schema
        assert determine_type_from_local_path(Path("workspaces/AP_[1]/queues/Inv_[]/inbox.json")) == Resource.Inbox

    def test_hook_rule_engine_field(self):
        assert determine_type_from_local_path(Path("hooks/Validator_[].json")) == Resource.Hook
        assert determine_type_from_local_path(Path("rules/Foo_[].json")) == Resource.Rule
        assert (
            determine_type_from_local_path(Path("engines/My_[1]/engine_fields/Field_[].json"))
            == Resource.EngineField
        )

    def test_unknown(self):
        assert determine_type_from_local_path(Path("misc/foo.json")) is None


class TestIsNewPath:
    def test_self_placeholder(self):
        assert is_new_path(Path("hooks/Foo_[].json"))

    def test_parent_placeholder(self):
        assert is_new_path(Path("workspaces/AP_[]/queues/Inv_[1]/queue.json"))

    def test_no_placeholder(self):
        assert not is_new_path(Path("workspaces/AP_[1]/queues/Inv_[2]/queue.json"))


class TestClassify:
    def test_placeholder_create(self):
        obj = make_obj(GIT_CHARACTERS.CREATED, "source/workspaces/AP_[]/workspace.json", {"name": "AP"})
        plan = classify([obj], ORG)
        assert plan.errors == []
        assert plan.creates == [obj]
        assert obj.is_new is True
        assert obj.placeholder_path == Path("workspaces/AP_[]/workspace.json")

    def test_placeholder_with_id_is_error(self):
        obj = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/workspaces/AP_[]/workspace.json",
            {"name": "AP", "id": 99, "url": "https://x/api/v1/workspaces/99"},
        )
        plan = classify([obj], ORG)
        assert plan.creates == []
        assert any("JSON still has an id/url" in e for e in plan.errors)

    def test_update_op_is_update(self):
        obj = make_obj(
            GIT_CHARACTERS.UPDATED,
            "source/workspaces/AP_[1]/workspace.json",
            {"id": 1, "url": "https://x/api/v1/workspaces/1"},
        )
        plan = classify([obj], ORG)
        assert plan.updates == [obj]

    def test_rename_collapse_delete_plus_create_same_id(self):
        """git mv: the new file keeps the original id+url, the old file is deleted."""
        deleted = make_obj(
            GIT_CHARACTERS.DELETED,
            "source/hooks/Old_[42].json",
            {"id": 42, "url": "https://x/api/v1/hooks/42"},
        )
        created = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/hooks/Renamed_[42].json",
            {"id": 42, "name": "Renamed", "url": "https://x/api/v1/hooks/42"},
        )
        plan = classify([deleted, created], ORG)
        assert plan.deletes == []
        assert plan.creates == []
        assert plan.updates == [created]
        assert created.operation == GIT_CHARACTERS.UPDATED

    def test_unmatched_delete_is_delete(self):
        deleted = make_obj(
            GIT_CHARACTERS.DELETED,
            "source/hooks/Old_[42].json",
            {"id": 42, "url": "https://x/api/v1/hooks/42"},
        )
        plan = classify([deleted], ORG)
        assert plan.deletes == [deleted]
        assert plan.errors == []

    def test_inbox_under_existing_queue_is_create(self):
        """Inbox can be added to an existing queue: no `_[]` anywhere, no id, but
        the parent queue folder has an id. Should classify as CREATE."""
        obj = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/workspaces/WS_[1]/queues/Q_[2]/inbox.json",
            {"name": "Inbox"},
        )
        plan = classify([obj], ORG)
        assert plan.errors == []
        assert plan.creates == [obj]
        assert obj.is_new is True

    def test_schema_without_placeholder_or_id_is_error(self):
        """schema.json under an existing queue with no id stays an error — adding
        a fresh schema to an existing queue requires PATCHing the queue's schema
        field, which the push pipeline doesn't do."""
        obj = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/workspaces/WS_[1]/queues/Q_[2]/schema.json",
            {"name": "schema", "content": []},
        )
        plan = classify([obj], ORG)
        assert plan.creates == []
        assert any("no '_[]' placeholder" in e for e in plan.errors)

    def test_create_without_placeholder_or_id_is_error(self):
        obj = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/hooks/Foo.json",
            {"name": "Foo"},
        )
        plan = classify([obj], ORG)
        assert plan.creates == []
        assert any("no '_[]' placeholder" in e for e in plan.errors)

    def test_rename_via_create_branch_sets_is_rename(self):
        """Rename collapse via the CREATE branch (id+url, no _[]) sets is_rename=True."""
        deleted = make_obj(
            GIT_CHARACTERS.DELETED,
            "source/hooks/Old_[42].json",
            {"id": 42, "url": "https://x/api/v1/hooks/42"},
        )
        created = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/hooks/Renamed_[42].json",
            {"id": 42, "name": "Renamed", "url": "https://x/api/v1/hooks/42"},
        )
        plan = classify([deleted, created], ORG)
        assert plan.updates == [created]
        assert created.is_rename is True

    def test_rename_via_update_branch_sets_is_rename(self):
        """When `mark_unstaged_objects_as_updated` flipped ?? to M, classify still
        pairs against the matching D and sets is_rename."""
        deleted = make_obj(
            GIT_CHARACTERS.DELETED,
            "source/hooks/Old_[42].json",
            {"id": 42, "url": "https://x/api/v1/hooks/42"},
        )
        updated = make_obj(
            GIT_CHARACTERS.UPDATED,
            "source/hooks/Renamed_[42].json",
            {"id": 42, "name": "Renamed", "url": "https://x/api/v1/hooks/42"},
        )
        plan = classify([deleted, updated], ORG)
        assert plan.updates == [updated]
        assert updated.is_rename is True

    def test_normal_update_does_not_set_is_rename(self):
        """An UPDATE with no matching D should NOT have is_rename set."""
        obj = make_obj(
            GIT_CHARACTERS.UPDATED,
            "source/workspaces/AP_[1]/workspace.json",
            {"id": 1, "url": "https://x/api/v1/workspaces/1"},
        )
        plan = classify([obj], ORG)
        assert plan.updates == [obj]
        assert obj.is_rename is False


class TestValidate:
    def test_required_field_missing(self):
        obj = make_obj(GIT_CHARACTERS.CREATED, "source/workspaces/AP_[]/workspace.json", {})
        plan = classify([obj], ORG)
        validate(plan)
        assert any("missing required field" in e for e in plan.errors)

    def test_new_queue_requires_sibling_schema(self):
        queue = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/workspaces/AP_[1]/queues/Inv_[]/queue.json",
            {"name": "Inv"},
        )
        plan = classify([queue], ORG)
        validate(plan)
        assert any("sibling schema.json" in e for e in plan.errors)

    def test_new_queue_with_sibling_schema_in_plan(self):
        queue = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/workspaces/AP_[1]/queues/Inv_[]/queue.json",
            {"name": "Inv"},
        )
        schema = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/workspaces/AP_[1]/queues/Inv_[]/schema.json",
            {"name": "Inv schema", "content": []},
        )
        plan = classify([queue, schema], ORG)
        validate(plan)
        sibling_errors = [e for e in plan.errors if "sibling schema.json" in e]
        assert sibling_errors == []


class TestOrder:
    def test_creates_workspace_before_queue_before_inbox(self):
        inbox = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/workspaces/AP_[]/queues/Inv_[]/inbox.json",
            {"name": "Inbox"},
        )
        queue = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/workspaces/AP_[]/queues/Inv_[]/queue.json",
            {"name": "Inv"},
        )
        schema = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/workspaces/AP_[]/queues/Inv_[]/schema.json",
            {"name": "schema", "content": []},
        )
        workspace = make_obj(
            GIT_CHARACTERS.CREATED,
            "source/workspaces/AP_[]/workspace.json",
            {"name": "AP"},
        )
        plan = classify([inbox, queue, schema, workspace], ORG)
        validate(plan)
        types = [op.type for op in order_creates(plan)]
        assert types.index(Resource.Workspace) < types.index(Resource.Queue)
        assert types.index(Resource.Schema) < types.index(Resource.Queue)
        assert types.index(Resource.Queue) < types.index(Resource.Inbox)

    def test_deletes_children_before_parents(self):
        workspace = make_obj(
            GIT_CHARACTERS.DELETED,
            "source/workspaces/AP_[1]/workspace.json",
            {"id": 1, "url": "https://x/api/v1/workspaces/1"},
        )
        queue = make_obj(
            GIT_CHARACTERS.DELETED,
            "source/workspaces/AP_[1]/queues/Inv_[2]/queue.json",
            {"id": 2, "url": "https://x/api/v1/queues/2"},
        )
        plan = classify([workspace, queue], ORG)
        types = [op.type for op in order_deletes(plan)]
        assert types.index(Resource.Queue) < types.index(Resource.Workspace)

    def test_create_and_delete_orders_are_reverses(self):
        assert CREATE_TYPE_ORDER == list(reversed(DELETE_TYPE_ORDER))
