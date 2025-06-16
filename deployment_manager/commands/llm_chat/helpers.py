import dataclasses
from anyio import Path
from langchain_aws import AmazonKnowledgeBasesRetriever, ChatBedrockConverse
from langchain_core.tools import tool
import json
from typing import AsyncGenerator
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from langchain_core.messages.utils import count_tokens_approximately
import httpx
from deployment_manager.commands.deploy.subcommands.run.upload_helpers import (
    Credentials,
)
from langchain.memory import ConversationSummaryBufferMemory

from deployment_manager.commands.document.llm_helper import MODEL_ID
from deployment_manager.utils.consts import display_error
from deployment_manager.utils.functions import (
    extract_id_from_url,
    find_all_object_paths,
)
from rossum_api.elis_api_client import ElisAPIClient
from deployment_manager.utils.consts import (
    settings,
)


def find_by_schema_id(content: list, schema_id: str) -> list:
    accumulator = []
    for node in content:
        if node["schema_id"] == schema_id:
            accumulator.append(node)
        elif "children" in node:
            accumulator.extend(find_by_schema_id(node["children"], schema_id))

    return accumulator


class ConversationSolver:
    system_prompt_content = (
        "You are an assistant advising on problems with the Rossum platform."
        "Answer questions with the help of the provided tools."
        "You also have access to a knowledge base including the whole Rossum API reference."
        "If you don't have a specific tool, you can try search the API reference and then make use the generic Rossum API request tool."
        "Here are some Rossum-related things to always keep in mind:"
        "- The JSON objects are nested: workspace has queues, queue has a schema, etc. If you need to find something about a queue, the information might therefore be on a different but related object."
        "- If the user references some name of field (e.g., 'PO Number'), you should first look into the schema of the queue to understand what the schema_id is because that is what Rossum uses internally."
    )

    region = "us-west-2"
    knowledge_base_id = "49SUNSDQCQ"
    profile_name = "rossum-dev"

    show_debug = False

    total_input_tokens = 0
    total_output_tokens = 0

    def _debug_print(self, message: str):
        if self.show_debug:
            print(message)

    def __init__(
        self, creds: Credentials, project_path: Path, dir_name: str, subdir_name: str
    ):
        self.client = ElisAPIClient(token=creds.token, base_url=creds.url)

        self.project_path = project_path
        self.dir_name = dir_name
        self.subdir_name = subdir_name

        self.llm = ChatBedrockConverse(
            model=MODEL_ID,
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

        # This memory automatically summarizes older parts of the conversation to
        # keep the total token count within the specified limit.
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=20_000,  # Max tokens for the conversation buffer (adjust as needed)
            memory_key="chat_history",  # The key under which memory variables are stored
            return_messages=True,  # Ensure messages are returned as LangChain BaseMessage objects
        )
        # --- Add the initial system message to the memory's chat history ---
        # This ensures the system instructions are always part of the context.
        self.memory.chat_memory.add_message(
            SystemMessage(content=self.system_prompt_content)
        )

        self.tools = self.setup_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    async def initialize(self):
        use_case_doc_path = (
            self.project_path
            / self.dir_name
            / self.subdir_name
            / settings.DOCUMENTATION_FOLDER_NAME
            / "use_case.txt"
        )
        self.documentation = (await use_case_doc_path.read_text()).splitlines()

        self.object_jsons = await self.gather_object_json()

    async def gather_object_json(self):
        all_file_paths = await find_all_object_paths(
            self.project_path / self.dir_name / self.subdir_name
        )

        object_jsons = {}
        for path in all_file_paths:
            # Using anyio.Path.read_text for async file reading
            file_content = await Path(path).read_text()
            object = json.loads(file_content)
            object_jsons.update({extract_id_from_url(object["url"]): object})

        return object_jsons

    def setup_tools(self):
        # TODO: count tokens and return meaningful error to LLM if it went overboard (e.g., 50k)
        @tool
        async def make_rossum_api_request(method: str, url: str, body: dict = None):
            """Calls Rossum API with the passed in parameters.
            The API Bearer token will be automatically included.

            Args:
                method: HTTP verb to use (GET/POST/PUT/PATCH/...)
                url: the URL should start only after version (e.g., /v1/annotations/{id} -> annotations/{id})
                body: (optional) Python dict with data to be sent in the request body (it will be converted to JSON automatically)

            Returns:
                JSON object from the Rossum API or an error as a string
            """
            try:
                return await self.client.request_json(method=method, url=url, json=body)
            except Exception as e:
                display_error(f"Error while making request to Rossum API: {e}")
                return str(e)

        @tool
        async def make_data_storage_request(collection_name: str, pipeline: list[dict]):
            """Calls Data Storage API with a MongoDB aggregation pipeline.
            The API Bearer token will be automatically included.

            Args:
                collection_name: Name of MongoDB collection to query
                pipeline: the aggregation pipeline to be used

            Returns:
                JSON objects from MongoDB
            """
            try:
                async with httpx.AsyncClient() as client:
                    req = await client.post(
                        url="https://us.app.rossum.ai/svc/data-storage/api/v1/data/aggregate",
                        headers={
                            "Authorization": f"Bearer {self.client._http_client.token}"
                        },
                        json={"collectionName": collection_name, "pipeline": pipeline},
                    )
                    req.raise_for_status()
                    return req.json()
                return await self.client.request_json()
            except Exception as e:
                display_error(f"Error while making request to DataStorage API: {e}")
                return str(e)

        @tool
        async def get_local_object_json(id: int):
            """Returns JSON of a local hook/queue/workspace JSON with the specified Rossum ID

            Args:
                id: ID of the object
            """
            obj_path = self.object_jsons.get(id)
            return obj_path

        @tool
        async def get_remote_hook_json(id: int):
            """Returns JSON of a hook JSON with the specified Rossum ID

            Args:
                id: ID of the hook
            """
            try:
                hook = await self.client.request_json(method="GET", url=f"hooks/{id}")
                return hook
            except Exception as e:
                display_error(f"Error while getting hook: {e}")
                return None

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
                annotation = await self.client.request_json(
                    method="GET", url=f"annotations/{id}"
                )
                return annotation
            except Exception as e:
                display_error(f"Error while getting annotation: {e}")
                return None

        @tool
        async def get_document_content(schema_ids: list[str], annotation_id: int):
            """Returns specificed schema_ids (datapoints) of the document with the specified ID

            Args:
                schema_ids: list of schema_ids to return
                annotation_id: ID of the document
            """
            try:
                annotation_content = await self.client.request_json(
                    method="GET", url=f"annotations/{annotation_id}/content"
                )
                found_schema_ids = {}
                for schema_id in schema_ids:
                    found_schema_ids[schema_id] = find_by_schema_id(
                        annotation_content["content"], schema_id
                    )
                return found_schema_ids
            except Exception as e:
                display_error(f"Error while getting annotation content: {e}")
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
            make_rossum_api_request,
            get_document,
            get_document_content,
            get_use_case_documentation,
            get_local_object_json,
            get_remote_hook_json,
            search_knowledge_base,
            make_data_storage_request,
        ]

    async def stream_call(self, user_input: str) -> AsyncGenerator[str, None]:
        # Add the new human message to the memory's chat history.
        # The memory will automatically manage summarization based on max_token_limit.
        self.memory.chat_memory.add_user_message(user_input)

        while True:
            # Retrieve the current conversation messages from memory.
            # This list includes the initial system message, any summarized history,
            # and the most recent messages, all trimmed to the max_token_limit.
            messages_for_llm = self.memory.load_memory_variables({})[
                self.memory.memory_key
            ]

            # Calculate input tokens for the current turn, which is the entire message history
            current_input_tokens = count_tokens_approximately(messages_for_llm)
            self.total_input_tokens += current_input_tokens

            self._debug_print(
                f"DEBUG: Current turn input tokens: {current_input_tokens}"
            )
            self._debug_print(
                f"DEBUG: Total input tokens so far: {self.total_input_tokens}"
            )

            llm_stream = self.llm_with_tools.astream(messages_for_llm)

            self._debug_print("\n--- Starting LLM Astream ---")
            try:
                first_chunk = await anext(llm_stream)  # Use anext to get the first item
                full_ai_message_chunk = first_chunk  # Initialize with the first chunk
            except StopAsyncIteration:
                self._debug_print("DEBUG: LLM returned no content or tool calls.")
                # If LLM returns nothing, add an empty AI message to history to keep turns consistent
                self.memory.chat_memory.add_ai_message("")
                break

            # Yield content from the first chunk immediately
            if hasattr(first_chunk, "content") and first_chunk.content is not None:
                if isinstance(first_chunk.content, list):
                    for part in first_chunk.content:
                        if (
                            isinstance(part, dict)
                            and part.get("type") == "text"
                            and "text" in part
                        ):
                            yield part["text"]
                elif isinstance(first_chunk.content, str):
                    yield first_chunk.content

            # Process remaining chunks
            async for chunk in llm_stream:  # Iterate through the REST of the stream
                full_ai_message_chunk += chunk  # Accumulate using LangChain's __add__

                # Yield content from the current chunk for immediate display
                if hasattr(chunk, "content") and chunk.content is not None:
                    if isinstance(chunk.content, list):
                        for part in chunk.content:
                            if (
                                isinstance(part, dict)
                                and part.get("type") == "text"
                                and "text" in part
                            ):
                                yield part["text"]
                    elif isinstance(chunk.content, str):
                        yield chunk.content

            self._debug_print("--- LLM Astream Finished ---")

            # Add the complete message to history
            final_ai_message_for_history = AIMessage(
                content=full_ai_message_chunk.content,
                tool_calls=full_ai_message_chunk.tool_calls,
            )
            self.memory.chat_memory.add_message(final_ai_message_for_history)

            # Calculate output tokens for the AI's response (only the new message)
            ai_response_tokens = count_tokens_approximately(
                [final_ai_message_for_history]
            )
            self.total_output_tokens += ai_response_tokens
            self._debug_print(f"DEBUG: AI response output tokens: {ai_response_tokens}")
            self._debug_print(
                f"DEBUG: Total output tokens so far: {self.total_output_tokens}"
            )

            self._debug_print(
                f"DEBUG: Final AIMessage for history (full content): {final_ai_message_for_history.content}"
            )
            self._debug_print(
                f"DEBUG: Final AIMessage for history (tool_calls attribute): {final_ai_message_for_history.tool_calls}"
            )

            # If no tool calls were made in the *final* accumulated message, the LLM is done
            if not final_ai_message_for_history.tool_calls:
                self._debug_print(
                    "DEBUG: No tool calls in final AI message. Breaking loop."
                )
                break  # Exit the main while loop

            # Execute the tool calls
            self._debug_print("DEBUG: Executing tool calls...")
            for tool_call in final_ai_message_for_history.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args")
                tool_id = tool_call.get("id")

                # Basic validation for tool_call structure before attempting execution
                if not tool_name or tool_args is None or not tool_id:
                    self._debug_print(
                        f"DEBUG: Malformed tool call found: {tool_call}. Skipping."
                    )
                    yield f"--- Tool Error: Malformed tool call received: {tool_call} ---\n\n"
                    # Add an AI message to memory to inform the LLM about the malformed tool call
                    self.memory.chat_memory.add_ai_message(
                        f"Malformed tool call: {tool_call}"
                    )
                    continue

                self._debug_print(
                    f"DEBUG: Attempting to execute tool: name={tool_name}, args={tool_args}, id={tool_id}"
                )

                selected_tool = next(
                    (t for t in self.tools if t.name == tool_name), None
                )

                if selected_tool:
                    self._debug_print(f"DEBUG: Tool '{tool_name}' found.")
                    yield f"\n\n--- Calling tool: {tool_name} with args: {json.dumps(tool_args)} ---\n"
                    try:
                        tool_output = await selected_tool.ainvoke(tool_args)
                        tool_output_str = (
                            json.dumps(tool_output)
                            if isinstance(tool_output, (dict, list))
                            else str(tool_output)
                        )

                        tool_message = ToolMessage(
                            content=tool_output_str,
                            tool_call_id=tool_id,
                        )
                        self.memory.chat_memory.add_message(tool_message)

                        yield f"--- Tool output: {tool_output_str[:200]}{'...' if len(tool_output_str) > 200 else ''} ---\n\n"
                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {e}"
                        yield f"--- Tool Error: {error_msg} ---\n\n"
                        error_tool_message = ToolMessage(
                            content=error_msg, tool_call_id=tool_id
                        )
                        self.memory.chat_memory.add_message(error_tool_message)
                else:
                    error_msg = f"Tool '{tool_name}' not found. This might indicate the model hallucinated a tool or the tool definition is missing."
                    yield f"--- Tool Error: {error_msg} ---\n\n"
                    error_ai_message = AIMessage(content=error_msg)
                    self.memory.chat_memory.add_ai_message(error_ai_message)
                    break
