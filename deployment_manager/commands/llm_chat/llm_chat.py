from anyio import Path
import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from deployment_manager.commands.document.llm_helper import LLMHelper
from deployment_manager.commands.llm_chat.helpers import ConversationSolver
from deployment_manager.utils.consts import (
    settings,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    get_url_and_credentials,
)
from deployment_manager.common.read_write import read_prd_project_config
from deployment_manager.utils.functions import coro


# TODO: tools
# TODO: differentiate objects for the LLM (annotations vs hooks, etc.)
# Fetch annotation
# Look up something in master data
# Fetch object (how to determine type?)
# Fetch hook logs by annotation_id or hook_id


async def query_llm(solver: ConversationSolver, input: str):
    return await solver.call(input)


@click.command(
    name=settings.LLM_CHAT_COMMAND_NAME,
    help="""Create documentation""",
)
@coro
async def llm_chat_wrapper(project_path: Path = None):
    if not project_path:
        project_path = Path("./")

    LLMHelper().validate_credentials()

    history = InMemoryHistory()
    session = PromptSession(history=history)

    # TODO: Integrate with a prd project
    prd_config = await read_prd_project_config(project_path=project_path)
    creds = await get_url_and_credentials(
        project_path=project_path, org_name="dev-org", yaml_data=prd_config
    )
    # api_url = await get_api_url_from_user()
    # token = await get_token_from_user()

    solver = ConversationSolver(creds=creds, project_path=project_path, dir_name='dev-org', subdir_name='s2k')
    await solver.initialize()

    while True:
        try:
            user_input = await session.prompt_async("You> ", multiline=False)

            if user_input.strip().lower() == "exit":
                print("Goodbye!")
                break

            # Call your LLM (async)
            response = await query_llm(solver, user_input)
            print(f"AI> {response}")

        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
