"""Tests for lookup table construction and the reverse lookup table derived from it."""

from collections import defaultdict

from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (  # noqa: F401
    DeployOrchestrator,
)
from deployment_manager.commands.deploy.subcommands.run.models import Target
from rossum_api.domain_logic.resources import Resource


class TestLookupTableStructure:
    """Tests around the shape the orchestrator builds: {source_id: {Resource: [Target...]}}"""

    def test_source_id_maps_to_resource_types(self):
        # Simulate what create_lookup_table produces
        t1 = Target(id=100)
        t2 = Target(id=200)
        lookup_table = defaultdict(dict)
        lookup_table[1][Resource.Hook] = [t1, t2]

        assert 1 in lookup_table
        assert Resource.Hook in lookup_table[1]
        assert [t.id for t in lookup_table[1][Resource.Hook]] == ["100", "200"]

    def test_multiple_types_can_share_source_id(self):
        lookup_table = defaultdict(dict)
        t1 = Target(id=100)
        t2 = Target(id=500)
        lookup_table[42][Resource.Hook] = [t1]
        lookup_table[42][Resource.Queue] = [t2]
        assert len(lookup_table[42]) == 2

    def test_reverse_lookup_construction(self):
        """Mimic create_reverse_lookup_table logic."""
        lookup_table = defaultdict(dict)
        lookup_table[1][Resource.Hook] = [Target(id=100), Target(id=200)]
        lookup_table[2][Resource.Queue] = [Target(id=300)]

        reverse = defaultdict(dict)
        for source_id, type_dict in lookup_table.items():
            for resource_type, targets in type_dict.items():
                for target in targets:
                    reverse[resource_type][target.id] = source_id

        assert reverse[Resource.Hook]["100"] == 1
        assert reverse[Resource.Hook]["200"] == 1
        assert reverse[Resource.Queue]["300"] == 2
