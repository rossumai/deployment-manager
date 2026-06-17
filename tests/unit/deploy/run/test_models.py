import uuid

import pytest

# Importing the orchestrator triggers Target.model_rebuild() at module load
from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (  # noqa: F401
    DeployOrchestrator,
)
from deployment_manager.commands.deploy.subcommands.run.models import (
    Target,
    convert_int_id_to_class,
)


class TestTarget:
    def test_default_id_is_uuid(self):
        t = Target()
        # Should be a valid UUID string
        uuid.UUID(t.id)
        assert t.exists_on_remote is False

    def test_real_int_id_sets_exists_on_remote(self):
        t = Target(id=42)
        # Converted to str
        assert t.id == "42"
        assert t.exists_on_remote is True

    def test_real_numeric_string_sets_exists_on_remote(self):
        t = Target(id="100")
        assert t.exists_on_remote is True

    def test_none_id_defaults_to_uuid(self):
        t = Target(id=None)
        uuid.UUID(t.id)
        assert t.exists_on_remote is False

    def test_create_dummy_id_from_parent(self):
        class FakeParent:
            name = "myws"
            id = 99

        t = Target()
        t.parent_object = FakeParent()
        t.index = 0
        t.create_dummy_id_from_parent()
        assert "NEW COPY" in t.id
        assert "myws" in t.id
        assert "99" in t.id

    def test_update_after_first_create(self):
        t = Target()
        t.data_from_remote = {"id": 555}
        t.update_after_first_create()
        assert t.id == 555
        assert t.exists_on_remote is True

    def test_attribute_override_default_empty(self):
        t = Target()
        assert t.attribute_override == {}

    def test_is_real_id_numeric_string(self):
        assert Target._is_real_id("123") is True

    def test_is_real_id_uuid(self):
        assert Target._is_real_id("abc-123-def") is False

    def test_is_real_id_none(self):
        assert Target._is_real_id(None) is False


class TestConvertIntIdToClass:
    def test_int_converts_to_target_with_none_id(self):
        result = convert_int_id_to_class(Target, 42)
        assert isinstance(result, Target)
        # An int passed alone (non-dict, non-model) becomes Target(id=None) i.e. new UUID
        uuid.UUID(result.id)

    def test_dict_passes_through(self):
        result = convert_int_id_to_class(Target, {"id": 5})
        # Not converted; dict is returned as-is so pydantic can handle it
        assert isinstance(result, dict)

    def test_model_passes_through(self):
        t = Target(id=42)
        assert convert_int_id_to_class(Target, t) is t


class TestDisplayLabel:
    def test_display_label_uses_pre_reference_data(self):
        t = Target(id=42)
        t.pre_reference_replace_data = {"name": "myobj", "id": 42}
        label = t.display_label
        assert "myobj" in label
        assert "42" in label


class TestExceptions:
    @pytest.mark.parametrize(
        "cls_name",
        [
            "SubObjectException",
            "PathNotFoundException",
            "TimestampMismatchException",
            "NonExistentObjectException",
            "DeployException",
        ],
    )
    def test_exceptions_inherit_from_exception(self, cls_name):
        from deployment_manager.commands.deploy.subcommands.run import models

        cls = getattr(models, cls_name)
        assert issubclass(cls, Exception)
        # Make sure they can be raised
        with pytest.raises(cls):
            raise cls("bar")
