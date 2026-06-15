import dataclasses

from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.reference_replacer import ReferenceReplacer
from deployment_manager.commands.deploy.subcommands.run.models import LookupTable, ReverseLookupTable
from deployment_manager.common.read_write import read_object_from_json
from deployment_manager.utils.consts import display_error, display_warning
from deployment_manager.utils.functions import extract_id_from_url, find_local_object_path_by_id


class HookReferenceReplacer(ReferenceReplacer):
    def __init__(self, parent_object_reference):
        super().__init__(parent_object_reference, Resource.Hook)

    async def replace_hook_run_after_list(
        self,
        object: dict,
        target_index: int,
        target_objects_count: int,
        lookup_table: LookupTable,
        reverse_lookup_table: ReverseLookupTable,
        use_dummy_references: bool,
    ):
        dependency_name = "run_after"
        object_type = Resource.Hook
        # The list is either copied and URLs are replaced, or they are simply added
        new_urls = []
        for source_dependency_url in object.get(dependency_name, []):
            new_url = self._replace_reference_in_url(
                source_dependency_url=source_dependency_url,
                reverse_lookup_table=reverse_lookup_table,
                lookup_table=lookup_table,
                object_type=object_type,
                target_objects_count=target_objects_count,
                target_index=target_index,
                use_dummy_references=use_dummy_references,
            )

            # Unlike for a single reference, a list item can be missing
            # In situations where this could be a problem, there are special warnings (e.g., forgotten hooks for queues)
            if not new_url:
                # Middle hook between A->B->C might not have been deployed so link A->C
                predecessor_of_predecessor_urls = await self.find_missing_hook_run_after(
                    predecessor_url=source_dependency_url,
                    reverse_lookup_table=reverse_lookup_table,
                    lookup_table=lookup_table,
                    target_objects_count=target_objects_count,
                    target_index=target_index,
                    use_dummy_references=use_dummy_references,
                )
                new_urls.extend(predecessor_of_predecessor_urls)
            else:
                new_urls.append(new_url)

        return new_urls

    async def find_missing_hook_run_after(
        self,
        predecessor_url: str,
        lookup_table: LookupTable,
        reverse_lookup_table: ReverseLookupTable,
        target_objects_count: int,
        target_index: int,
        use_dummy_references: bool = True,
    ):
        # The predecessor hook was ignored, it has no targets equivalent
        # Take the predecessor's source and find its predecessor (if none, stop)
        # Find the predecessors' target and put that into run_after for this hook
        # If there is no target, repeat from line one
        deploy_file = self.parent_object_reference.deploy_file
        predecessor_id = extract_id_from_url(predecessor_url)

        try:
            if deploy_file.local_deploy:
                # Local deploy: resolve the predecessor from the locally pulled hooks, not the source org.
                predecessor_data = await self._load_local_hook(predecessor_id)
                if not predecessor_data:
                    display_warning(
                        f'Could not find predecessor hook with ID "{predecessor_id}" locally. '
                        "The run_after reference may not be replaced correctly."
                    )
                    return []
            else:
                predecessor = await deploy_file.source_client.retrieve_hook(predecessor_id)
                predecessor_data = dataclasses.asdict(predecessor)

            return await self.replace_hook_run_after_list(
                object=predecessor_data,
                reverse_lookup_table=reverse_lookup_table,
                lookup_table=lookup_table,
                target_objects_count=target_objects_count,
                target_index=target_index,
                use_dummy_references=use_dummy_references,
            )

        except Exception as e:
            display_error(
                f' Error while finding predecessor hook with ID "{predecessor_id}" in Rossum.',
                e,
            )
            return []

    async def _load_local_hook(self, hook_id: int) -> dict | None:
        """Read a locally pulled hook by id from ``<source_dir>/hooks/`` (used by local deploy --ld)."""
        hooks_dir = self.parent_object_reference.deploy_file.source_dir_path / Resource.Hook.value
        path = await find_local_object_path_by_id(hooks_dir, hook_id)
        if not path:
            return None
        return await read_object_from_json(path, False)
