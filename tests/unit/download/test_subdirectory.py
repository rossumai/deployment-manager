from deployment_manager.commands.download.subdirectory import (
    Subdirectory,
    create_subdir_configuration,
)


class TestSubdirectory:
    def test_default_values(self):
        sd = Subdirectory(name="test")
        assert sd.name == "test"
        assert sd.regex is None
        assert sd.include is False

    def test_fields_from_init(self):
        sd = Subdirectory(name="prod", regex="PROD", include=True, object_ids=[1, 2])
        assert sd.regex == "PROD"
        assert sd.include is True
        assert sd.object_ids == {1, 2}


class TestCreateSubdirConfiguration:
    def test_empty_input(self):
        assert create_subdir_configuration({}) == {}

    def test_basic_mapping(self):
        result = create_subdir_configuration(
            {
                "prod": {"include": True, "object_ids": [1]},
                "dev": {"include": False, "object_ids": [2]},
            }
        )
        assert "prod" in result
        assert "dev" in result
        assert result["prod"].include is True
        assert result["dev"].include is False

    def test_none_value_handled(self):
        result = create_subdir_configuration({"prod": None})
        assert result["prod"].name == "prod"
        # When `value` is None, default Subdirectory fields are used
        assert result["prod"].include is False
