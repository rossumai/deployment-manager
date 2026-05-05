"""JMESPath-heavy attribute_override scenarios flagged in the refine-deployment skill:
array indices, $-quoted keys, deeply nested paths.
"""

import pytest
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.attribute_override import (
    AttributeOverrideException,
    AttributeOverrider,
    parse_parent_and_key,
    perform_search,
)


class TestArrayIndexOverrides:
    def test_single_array_index(self):
        overrider = AttributeOverrider(type=Resource.Hook)
        obj = {"settings": {"items": [{"v": "a"}, {"v": "b"}]}}
        overrider.override_attribute_v2(obj, "settings.items[0].v", "replaced")
        assert obj["settings"]["items"][0]["v"] == "replaced"
        assert obj["settings"]["items"][1]["v"] == "b"

    def test_multiple_array_indices(self):
        overrider = AttributeOverrider(type=Resource.Hook)
        obj = {
            "settings": {
                "configurations": [
                    {"source": {"dataset": "dev_a", "queries": [{"name": "q1"}]}},
                    {"source": {"dataset": "dev_b", "queries": [{"name": "q2"}]}},
                ]
            }
        }
        overrider.override_attribute_v2(obj, "settings.configurations[0].source.dataset", "prod_a")
        overrider.override_attribute_v2(obj, "settings.configurations[1].source.dataset", "prod_b")
        assert obj["settings"]["configurations"][0]["source"]["dataset"] == "prod_a"
        assert obj["settings"]["configurations"][1]["source"]["dataset"] == "prod_b"

    def test_deeply_nested_array_chain(self):
        overrider = AttributeOverrider(type=Resource.Hook)
        obj = {
            "settings": {
                "configurations": [
                    {
                        "source": {
                            "queries": [
                                {
                                    "pipeline": [
                                        {"name": "stage0"},
                                        {"name": "stage1"},
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }
        overrider.override_attribute_v2(
            obj,
            "settings.configurations[0].source.queries[0].pipeline[1].name",
            "updated_stage",
        )
        assert obj["settings"]["configurations"][0]["source"]["queries"][0]["pipeline"][1]["name"] == "updated_stage"


class TestDollarQuotedKeys:
    """$-prefixed keys (MongoDB operators) must be quoted: `settings."$unionWith".coll`."""

    def test_quoted_dollar_key(self):
        overrider = AttributeOverrider(type=Resource.Hook)
        obj = {"settings": {"$unionWith": {"coll": "dev_collection"}}}
        overrider.override_attribute_v2(obj, 'settings."$unionWith".coll', "prod_collection")
        assert obj["settings"]["$unionWith"]["coll"] == "prod_collection"

    def test_nested_dollar_key_with_array(self):
        overrider = AttributeOverrider(type=Resource.Hook)
        obj = {
            "settings": {
                "pipeline": [
                    {"$match": {"status": "draft"}},
                    {"$lookup": {"from": "dev_data"}},
                ]
            }
        }
        overrider.override_attribute_v2(obj, 'settings.pipeline[1]."$lookup".from', "prod_data")
        assert obj["settings"]["pipeline"][1]["$lookup"]["from"] == "prod_data"


class TestKeysWithSpecialChars:
    def test_hyphen_key_not_supported_directly(self):
        """Hyphen keys in a parent path aren't handled by parse_parent_and_key.
        Workaround: target the hyphen-key as the single top-level query string."""
        overrider = AttributeOverrider(type=Resource.Hook)
        # The full quoted path is treated as JMESPath by perform_search
        obj = {"my-key": "old"}
        overrider.override_attribute_v2(obj, '"my-key"', "new")
        # parse_parent_and_key treats this as parent=None, key='"my-key"'
        # The quoted key becomes the dict key (with quotes), so the original stays.
        # This documents current behavior: quoted top-level keys are NOT supported.
        assert obj["my-key"] == "old"

    def test_key_with_dots_quoted_raises(self):
        """Dots inside quoted keys break `parse_parent_and_key` — it splits on the last dot."""
        import jmespath.exceptions

        overrider = AttributeOverrider(type=Resource.Hook)
        obj = {"settings": {"some.key": "old"}}
        with pytest.raises(jmespath.exceptions.LexerError):
            overrider.override_attribute_v2(obj, 'settings."some.key"', "new")


class TestParentKeyParsing:
    def test_bracket_index_at_end(self):
        parent, key, _ = parse_parent_and_key("settings.items[0]")
        assert parent == "settings"
        # This is how JMESPath sees it — the whole thing is the key after last dot
        assert key == "items[0]"

    def test_quoted_dollar_key_parent(self):
        parent, key, _ = parse_parent_and_key('settings."$unionWith".coll')
        # Last '.' is between "$unionWith" and coll
        assert key == "coll"

    def test_bracket_wildcard(self):
        parent, key, _ = parse_parent_and_key("settings.configurations[*].queue_ids")
        assert parent == "settings.configurations[*]"
        assert key == "queue_ids"


class TestPerformSearchWithArrays:
    def test_index_extraction(self):
        obj = {"items": [{"x": 1}, {"x": 2}]}
        result = perform_search("items[0]", obj)
        assert result == [{"x": 1}]

    def test_wildcard_search(self):
        obj = {"items": [{"x": 1}, {"x": 2}]}
        result = perform_search("items[*]", obj)
        assert result == [{"x": 1}, {"x": 2}]

    def test_missing_array_element_raises(self):
        obj = {"items": [{"x": 1}]}
        with pytest.raises(AttributeOverrideException):
            perform_search("items[5]", obj)


class TestRegexWithWordBoundaries:
    """refine-deployment skill uses patterns like `\\bDEV\\b/#/PROD` to avoid partial matches."""

    def test_word_boundary_avoids_partial(self):
        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.attribute_override import (
            AttributeOverrider,
        )

        overrider = AttributeOverrider(type=Resource.Workspace)
        obj = {"name": "DEVELOPMENT Queue for DEV"}
        # \bDEV\b should not match inside "DEVELOPMENT"
        overrider.override_attribute_v2(obj, "name", "\\bDEV\\b/#/PROD")
        # Only the standalone 'DEV' should be replaced
        assert obj["name"] == "DEVELOPMENT Queue for PROD"

    def test_anchor_start_pattern(self):
        from deployment_manager.commands.deploy.subcommands.run.deploy_objects.attribute_override import (
            AttributeOverrider,
        )

        overrider = AttributeOverrider(type=Resource.Hook)
        obj = {"name": "DEV_suppliers"}
        overrider.override_attribute_v2(obj, "name", "^DEV_/#/PROD_")
        assert obj["name"] == "PROD_suppliers"
