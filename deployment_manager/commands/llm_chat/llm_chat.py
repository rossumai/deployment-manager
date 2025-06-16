from anyio import Path
import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from deployment_manager.commands.document.llm_helper import LLMHelper
from deployment_manager.commands.llm_chat.helpers import ConversationSolver
from deployment_manager.utils.consts import (
    display_error,
    settings,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    get_url_and_credentials,
)
from deployment_manager.common.read_write import read_prd_project_config
from deployment_manager.utils.functions import coro


# TODO: tools
# TODO: differentiate objects for the LLM (annotations vs hooks, etc.)
# Look up something in master data
# Fetch object (how to determine type?)
# Fetch hook logs by annotation_id or hook_id


async def query_llm(solver: ConversationSolver, input: str):
    return await solver.call(input)


@click.command(
    name=settings.LLM_CHAT_COMMAND_NAME,
    help="""Chat with Rossum-knowledgeable AI""",
)
@click.argument(
    "destination",
    nargs=1,
    type=str,
)
@coro
async def llm_chat_wrapper(destination: str, project_path: Path = None):
    if not project_path:
        project_path = Path("./")

    try:
        dir_name, subdir_name = destination.split("/")
    except Exception as e:
        display_error(f"Invalid destination '{destination}'")
        return

    LLMHelper().validate_credentials()

    history = InMemoryHistory()
    session = PromptSession(history=history)

    # TODO: Integrate with a prd project
    prd_config = await read_prd_project_config(project_path=project_path)

    creds = await get_url_and_credentials(
        project_path=project_path, org_name=dir_name, yaml_data=prd_config
    )

    solver = ConversationSolver(
        creds=creds,
        project_path=project_path,
        dir_name=dir_name,
        subdir_name=subdir_name,
    )
    await solver.initialize()

    print("Welcome to the Rossum Assistant! Type 'exit' to quit.")
    while True:
        try:
            user_input = await session.prompt_async("You> ", multiline=False)

            if user_input.strip().lower() == "exit":
                print("Goodbye!")
                break

            print(
                "AI> ", end="", flush=True
            )  # Start printing AI response on the same line
            # Consume the streamed response
            async for chunk in solver.stream_call(user_input):
                print(
                    chunk, end="", flush=True
                )  # Print each chunk immediately without a newline
            print()  # Print a final newline after the AI response is complete

        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
