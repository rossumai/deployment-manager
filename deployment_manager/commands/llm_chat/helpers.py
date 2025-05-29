import asyncio
import dataclasses
from functools import partial
import aiofiles
from anyio import Path
import anyio
from langchain_aws import AmazonKnowledgeBasesRetriever, ChatBedrockConverse
from langchain_core.tools import tool, Tool
import json

from deployment_manager.commands.deploy.subcommands.run.upload_helpers import (
    Credentials,
)
from deployment_manager.utils.consts import display_error
from deployment_manager.utils.functions import (
    extract_id_from_url,
    find_all_object_paths,
)
from rossum_api.elis_api_client import ElisAPIClient
from deployment_manager.utils.consts import (
    settings,
)


class ConversationSolver:
    messages = [
        (
            "system",
            "You are an assistant advising on problems with the Rossum platform. Answer questions with the help of the provided tools.",
        )
    ]

    region = "us-west-2"
    knowledge_base_id = "49SUNSDQCQ"
    profile_name = "rossum-dev"

    def __init__(
        self, creds: Credentials, project_path: Path, dir_name: str, subdir_name: str
    ):
        self.client = ElisAPIClient(token=creds.token, base_url=creds.url)

        self.project_path = project_path
        self.dir_name = dir_name
        self.subdir_name = subdir_name

        self.llm = ChatBedrockConverse(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            endpoint_url="https://bedrock-runtime.us-west-2.amazonaws.com/",
            region_name=self.region,
            credentials_profile_name=self.profile_name,
        )

        self.bedrock_kb_retriever = AmazonKnowledgeBasesRetriever(
            knowledge_base_id=self.knowledge_base_id,
            region_name=self.region,
            credentials_profile_name=self.profile_name,
            retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 4}},
        )

        self.tools = self.setup_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    async def initialize(self):
        async with aiofiles.open(
            f"{self.dir_name}/{self.subdir_name}/{settings.DOCUMENTATION_FOLDER_NAME}/use_case.txt"
        ) as rf:
            self.documentation = await rf.readlines()

        self.object_json_paths = await self.gather_object_json()

    async def gather_object_json(self):
        all_file_paths = await find_all_object_paths(
            self.project_path / self.dir_name / self.subdir_name
        )

        # TODO: more efficient approach
        object_jsons = {}
        for path in all_file_paths:
            with open(path) as rf:
                object = json.load(rf)
                object_jsons.update({extract_id_from_url(object["url"]): object})

        return object_jsons

    def setup_tools(self):
        # Define tools as instance methods that can access self
        @tool
        async def get_object_json(id: int):
            """Returns JSON of the hook/queue/workspace with the specified Rossum ID

            Args:
                id: ID of the object
            """
            path = self.object_json_paths.get(id)
            return path
            # print(path, id)
            # if not path:
            #     return None
            # async with aiofiles.open(path, "r") as rf:
            #     return json.loads(await rf.read())

        # TODO: parameterize path to subdir
        @tool
        def get_use_case_documentation():
            """
            Returns documentation of a specific Rossum use case/project as text.
            Should be the starting point for almost every question since it gives general overview of the project.
            """
            return self.documentation

        @tool
        async def get_document(id: int):
            """Returns JSON of the document (annotation) with the specified ID

            Args:
                id: ID of the document
            """
            try:
                annotation = await self.client.retrieve_annotation(
                    id, sideloads=["content"]
                )
                return dataclasses.asdict(annotation)
            except Exception as e:
                display_error(f"Error while getting annotation: {e}")
                return None

        @tool
        async def search_knowledge_base(query: str):
            """
            Searches the Knowledge Base for relevant information.
            Use this tool when you need general (not project-specific) information about Rossum and its configuration.

            Args:
                query: The question or query to search the knowledge base with.
            """
            try:
                docs = await self.bedrock_kb_retriever.ainvoke(query)
                parsed_docs = "\n\n".join([doc.page_content for doc in docs])
                return parsed_docs
            except Exception as e:
                display_error(f"Error while searching knowledge base: {e}")
                return None

        return [
            get_document,
            get_use_case_documentation,
            get_object_json,
            search_knowledge_base,
        ]

    async def call(self, user_input: str):
        self.messages.append(("human", user_input))

        while True:
            print("LLM call")
            ai_msg = await self.llm_with_tools.ainvoke(self.messages)
            self.messages.append(ai_msg)

            if not ai_msg.tool_calls:
                # LLM is done with tools, ready to talk to user
                return ai_msg.content

            # Otherwise, loop over tools and let the LLM continue
            for tool_call in ai_msg.tool_calls:
                selected_tool = next(
                    t for t in self.tools if t.name == tool_call["name"]
                )
                tool_msg = await selected_tool.ainvoke(tool_call)
                self.messages.append(tool_msg)
