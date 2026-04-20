import pytest
from anyio import Path

from deployment_manager.commands.upload.dependencies import (
    is_change_existing,
    merge_formula_changes,
    merge_hook_changes,
)
from deployment_manager.common.read_write import read_object_from_json, write_object_to_json, write_str
from deployment_manager.utils.consts import GIT_CHARACTERS, settings


class TestIsChangeExisting:
    def test_same_op_and_path_returns_true(self):
        changes = [(GIT_CHARACTERS.UPDATED, Path("a.json"))]
        assert is_change_existing((GIT_CHARACTERS.UPDATED, Path("a.json")), changes) is True

    def test_different_op_same_path(self):
        changes = [(GIT_CHARACTERS.UPDATED, Path("a.json"))]
        assert is_change_existing((GIT_CHARACTERS.DELETED, Path("a.json")), changes) is False

    def test_different_path(self):
        changes = [(GIT_CHARACTERS.UPDATED, Path("a.json"))]
        assert is_change_existing((GIT_CHARACTERS.UPDATED, Path("b.json")), changes) is False

    def test_empty_list(self):
        assert is_change_existing((GIT_CHARACTERS.UPDATED, Path("a.json")), []) is False


@pytest.mark.asyncio
class TestMergeHookChanges:
    async def test_updated_py_file_merges_into_json(self, tmp_path):
        org_path = tmp_path
        hook_dir = tmp_path / "org" / "hooks"
        await hook_dir.mkdir(parents=True)
        hook_json_path = hook_dir / "h1.json"
        hook_py_path = hook_dir / "h1.py"

        # Write the initial JSON object and a new Python file
        await write_object_to_json(
            hook_json_path,
            {"config": {"code": "old_code", "runtime": "python3.8"}, "extension_source": "custom"},
        )
        await write_str(hook_py_path, "new_code_here")

        changes = [(GIT_CHARACTERS.UPDATED, hook_py_path)]
        result = await merge_hook_changes(changes, org_path)

        # The result should have a single UPDATED for the JSON file
        assert len(result) == 1
        assert result[0][0] == GIT_CHARACTERS.UPDATED
        assert "h1.json" in str(result[0][1])

        # The JSON file itself should now contain the new code
        updated = await read_object_from_json(hook_json_path)
        assert updated["config"]["code"] == "new_code_here"

    async def test_unrelated_change_is_passed_through(self, tmp_path):
        other_path = tmp_path / "workspace.json"
        change = (GIT_CHARACTERS.UPDATED, other_path)
        result = await merge_hook_changes([change], tmp_path)
        assert change in result


@pytest.mark.asyncio
class TestMergeFormulaChanges:
    async def test_formula_update_merges_into_schema(self, tmp_path):
        formula_dir = settings.FORMULA_DIR_NAME
        queue_dir = tmp_path / "ws_[1]" / "queues" / "q_[5]"
        formula_path = queue_dir / formula_dir / "target_field.py"
        schema_path = queue_dir / "schema.json"

        await (queue_dir / formula_dir).mkdir(parents=True)

        # Write schema with that formula field
        await write_object_to_json(
            schema_path,
            {
                "content": [
                    {
                        "category": "section",
                        "children": [
                            {"id": "target_field", "category": "datapoint", "formula": "old"},
                        ],
                    }
                ]
            },
        )
        # Write new formula code
        await write_str(formula_path, "new_formula_code")

        changes = [(GIT_CHARACTERS.UPDATED, formula_path)]
        result = await merge_formula_changes(changes)

        # Should produce a single UPDATED schema.json change
        assert len(result) == 1
        assert result[0][0] == GIT_CHARACTERS.UPDATED
        assert "schema.json" in str(result[0][1])

        # Schema file now has updated formula code
        updated = await read_object_from_json(schema_path)
        datapoint = updated["content"][0]["children"][0]
        assert datapoint["formula"] == "new_formula_code"

    async def test_unrelated_change_passthrough(self, tmp_path):
        p = tmp_path / "something.json"
        change = (GIT_CHARACTERS.UPDATED, p)
        result = await merge_formula_changes([change])
        assert change in result
