from project_rossum_deploy.commands.deploy.subcommands.run.attribute_override import (
    override_attributes_v2,
)
from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
)
from project_rossum_deploy.commands.migrate.schemas import update_formula_fields_code
from project_rossum_deploy.utils.consts import display_error


from rossum_api.api_client import Resource


import asyncio
from copy import deepcopy


class SchemaRelease(ObjectRelease):
    type: Resource = Resource.Schema

    async def deploy(self):
        try:
            await update_formula_fields_code(self.path, self.data)

            release_requests = []
            for target in self.targets:
                schema_copy = deepcopy(self.data)
                schema_copy["queues"] = []
                override_attributes_v2(
                    object=schema_copy, attribute_overrides=target.attribute_override
                )

                request = self.upload(object=schema_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            # asyncio.gather returns results in the same order as they were put in
            for index, (result, target) in enumerate(zip(results, self.targets)):
                target.id = result.get("id", None)
                target.data = result
                self.yaml_reference["targets"][index]["id"] = target.id

        except Exception as e:
            display_error(f"Error while migrating schema {self.name} ({self.id}):", e)
