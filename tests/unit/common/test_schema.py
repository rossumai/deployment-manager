from deployment_manager.common.schema import find_schema_id


class TestFindSchemaId:
    def test_empty(self):
        assert find_schema_id([], "x") is None

    def test_top_level_list(self):
        schema = [{"id": "a", "category": "datapoint"}, {"id": "b"}]
        assert find_schema_id(schema, "a") == {"id": "a", "category": "datapoint"}

    def test_not_found(self):
        schema = [{"id": "a"}]
        assert find_schema_id(schema, "missing") is None

    def test_nested_in_children_dict(self):
        schema = {"children": {"id": "x", "category": "datapoint"}}
        assert find_schema_id(schema, "x") == {"id": "x", "category": "datapoint"}

    def test_nested_in_children_list(self):
        schema = {
            "id": "section",
            "children": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
        }
        assert find_schema_id(schema, "b") == {"id": "b"}

    def test_deeply_nested(self):
        schema = [
            {
                "id": "s1",
                "children": [
                    {
                        "id": "g1",
                        "children": [{"id": "target_field", "formula": "1+1"}],
                    }
                ],
            }
        ]
        found = find_schema_id(schema, "target_field")
        assert found == {"id": "target_field", "formula": "1+1"}
