import dataclasses
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.reference_replacer import (
    ReferenceReplacer,
)
from deployment_manager.commands.deploy.subcommands.run.models import (
    LookupTable,
    ReverseLookupTable,
)
from deployment_manager.utils.consts import display_error
from deployment_manager.utils.functions import extract_id_from_url
from rossum_api.domain_logic.resources import Resource


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
                predecessor_of_predecessor_urls = (
                    await self.find_missing_hook_run_after(
                        predecessor_url=source_dependency_url,
                        reverse_lookup_table=reverse_lookup_table,
                        lookup_table=lookup_table,
                        target_objects_count=target_objects_count,
                        target_index=target_index,
                        use_dummy_references=use_dummy_references,
                    )
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
        try:
            predecessor_id = extract_id_from_url(predecessor_url)
            predecessor = await self.parent_object_reference.deploy_file.source_client.retrieve_hook(
                predecessor_id
            )
            return await self.replace_hook_run_after_list(
                object=dataclasses.asdict(predecessor),
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
