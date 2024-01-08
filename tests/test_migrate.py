import pytest

from rossum_api import ElisAPIClient

# repull new project for each test
# always destroy all new created objects and reset mapping

# TEST: (initial release) empty right hand side of mapping, release
# check that after pulling, you have all target files 

# TEST: ignore some file, release
# check that it was not released

# TEST: (second release) do an initial release, then try releasing again
# check that nothing changed

# TEST: (second release) do an initial release, change some source file, try releasing again
# check that the change was released to target object

# TEST: private hook migration

# TEST: hook dependency graph migration successful

# TEST: create/use MDH extension with attribute override defined, release that
# check that the queue ids were changed accordingly

# TEST: change mapping org target to empty, release
# check that release failed because of no target


@pytest.mark.asyncio
async def test_migrate_files(client: ElisAPIClient):
    organizations = [org async for org in client.list_all_organizations()]

    print(organizations)
