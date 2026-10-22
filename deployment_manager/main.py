import importlib.metadata
from pathlib import Path

import click

from deployment_manager.commands.deploy.deploy import deploy
from deployment_manager.commands.document.document import generate_documentation_wrapper
from deployment_manager.commands.download.download import download_project_wrapper
from deployment_manager.commands.hook.hook import hook
from deployment_manager.commands.initialize import init_project
from deployment_manager.commands.llm_chat.llm_chat import llm_chat_wrapper
from deployment_manager.commands.purge.purge import purge_object_types_wrapper
from deployment_manager.commands.update import update_application
from deployment_manager.commands.upload.upload import upload_project_wrapper
from deployment_manager.utils.output_logging import (
    AUTO_LOG_FILE,
    NO_LOG_FILE_OPTION,
    LogFileGroup,
    enable_output_logging,
    resolve_log_file_path,
)


@click.group(cls=LogFileGroup, context_settings={"max_content_width": 120})
@click.version_option(version=importlib.metadata.version("deployment-manager"))
@click.option(
    "--log-file",
    type=click.Path(dir_okay=False, path_type=Path),
    is_flag=False,
    flag_value=AUTO_LOG_FILE,
    default=AUTO_LOG_FILE,
    envvar="PRD_LOG_FILE",
    help="Append all output, including tracebacks, to this file. By default (or when passed without a value) "
    "output-<timestamp>.log is written into .prd_logs/, keeping the latest 20. Also settable via PRD_LOG_FILE.",
)
@click.option(
    NO_LOG_FILE_OPTION,
    is_flag=True,
    envvar="PRD_NO_LOG_FILE",
    help="Do not write the output to a log file. Also settable via PRD_NO_LOG_FILE=1.",
)
def main(log_file: Path, no_log_file: bool):
    if not no_log_file:
        enable_output_logging(resolve_log_file_path(log_file))


main.add_command(download_project_wrapper)
main.add_command(init_project)
main.add_command(deploy)
main.add_command(hook)
main.add_command(generate_documentation_wrapper)
main.add_command(llm_chat_wrapper)
main.add_command(purge_object_types_wrapper)
main.add_command(upload_project_wrapper)
main.add_command(update_application)

# For debugging purposes
if __name__ == "__main__":
    main()
