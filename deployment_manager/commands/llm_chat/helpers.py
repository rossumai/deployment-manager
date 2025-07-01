import dataclasses
from anyio import Path
from langchain_aws import AmazonKnowledgeBasesRetriever, ChatBedrockConverse
from langchain_core.tools import tool
import json
from typing import AsyncGenerator
from langchain_core.messages import (
    AIMessage,
    ToolMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)

# from langchain_core.messages.utils import count_tokens_approximately # Will replace with LLM's counter
import httpx
from deployment_manager.commands.deploy.subcommands.run.upload_helpers import (
    Credentials,
)
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
from langchain_core.messages.utils import count_tokens_approximately
from langchain.memory import ConversationSummaryBufferMemory

# No longer strictly needed for direct message passing but good for prompt templates
# from langchain_core.prompts import MessagesPlaceholder


def find_by_schema_id(content: list, schema_id: str) -> list:
    """Recursively finds all nodes in a nested JSON structure that match a given schema_id."""
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
        "# Objective: Answer questions with the help of the provided tools."
        "# Key instructions and tips:"
        "- If the question or subproblem is specific to a Rossum queue/project, you should always check your understanding against documentation before answering."
        "- If the question or subproblem is generic about Rossum, you should always check your understanding against the knoelwedge base before answering."
        "- The knowledge base includes the whole Rossum API reference."
        "- If you don't have a specific tool, you can try search the API reference and then make use the generic Rossum API request tool."
        "- Rossum objects are nested in the following way: workspace has queues, queue has a schema, etc. If you need to find something about a queue, the information might therefore be on a different but related object."
        "- Your context window is limited and you should not call the API to list many objects at once (e.g., all /hooks?queue_id=333). If you can, request objects one by one (e.g., look at queue.hooks and then ask about each in turn)."
        "- If the user references some name of field (e.g., 'PO Number'), you should first look into the schema of the queue to understand what the schema_id is because that is what Rossum uses internally."
    )

    region = "us-west-2"
    knowledge_base_id = "49SUNSDQCQ"
    profile_name = "rossum-dev"
    endpoint_url = "https://bedrock-runtime.us-west-2.amazonaws.com/"

    show_debug = False

    total_input_tokens = 0
    total_output_tokens = 0

    # Define a buffer safety margin for individual messages/tool outputs
    # This prevents a single message from consuming the entire memory limit.
    MAX_INDIVIDUAL_MESSAGE_FRACTION = 0.8

    @property
    def documentation_base_path(self):
        return (
            self.project_path
            / self.dir_name
            / self.subdir_name
            / settings.DOCUMENTATION_FOLDER_NAME
        )

    @property
    def data_storage_api_url(self):
        COMMON_SUFFIX = "/svc/data-storage/api/v1"
        if "us.api.rossum.ai" in self.client._http_client.base_url:
            return "https://us.app.rossum.ai" + COMMON_SUFFIX
        elif "api.elis.rossum.ai" in self.client._http_client.base_url:
            return "https://elis.rossum.ai" + COMMON_SUFFIX
        else:
            return (
                self.client._http_client.base_url.replace("/api/v1", "") + COMMON_SUFFIX
            )

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
            endpoint_url=self.endpoint_url,
            region_name=self.region,
            credentials_profile_name=self.profile_name,
        )

        self.summary_llm = ChatBedrockConverse(
            model="us.anthropic.claude-3-haiku-20240307-v1:0",  # Use a cheaper/faster model for summarization if preferred
            endpoint_url=self.llm.endpoint_url,
            region_name=self.llm.region_name,
            credentials_profile_name=self.llm.credentials_profile_name,
        )

        self.bedrock_kb_retriever = AmazonKnowledgeBasesRetriever(
            knowledge_base_id=self.knowledge_base_id,
            region_name=self.region,
            credentials_profile_name=self.profile_name,
            retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 4}},
        )

        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=100_0000,
            memory_key="chat_history",
            return_messages=True,
        )
        self.memory.chat_memory.add_message(
            SystemMessage(content=self.system_prompt_content)
        )

        self.tools = self.setup_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def _get_messages_tokens(self, messages: list[BaseMessage]) -> int:
        """Returns the total token count for a list of BaseMessages."""
        return count_tokens_approximately(messages)

    async def initialize(self):
        self.object_jsons = await self.gather_object_json()

    async def gather_object_json(self):
        all_file_paths = await find_all_object_paths(
            self.project_path / self.dir_name / self.subdir_name
        )

        object_jsons = {}
        for path in all_file_paths:
            file_content = await Path(path).read_text()
            object = json.loads(file_content)
            object_jsons.update({extract_id_from_url(object["url"]): object})
        return object_jsons

    def setup_tools(self):
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
                        url=self.data_storage_api_url + "/data/aggregate",
                        headers={
                            "Authorization": f"Bearer {self.client._http_client.token}"
                        },
                        json={"collectionName": collection_name, "pipeline": pipeline},
                    )
                    req.raise_for_status()
                    return req.json()
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
        async def get_queue_documentation(queue_id: int):
            """
            Returns documentation of a specific Rossum queue as text.
            Should be the starting point for almost every question since it gives general overview of the queue including extensions.

            Args:
                queue_id: ID of the queue

            """
            async for queue_path in (self.documentation_base_path / "queues").iterdir():
                if (
                    queue_path.stem
                    == f"{queue_id}_{settings.DOCUMENTATION_INTERNAL_SUFFIX}"
                ):
                    return await queue_path.read_text()
            return "no such queue documented"

        @tool
        async def get_extension_documentation(extension_id: int):
            """
            Returns documentation of a specific Rossum extension (hook) as text.
            Should be the starting point for almost every question since it gives general overview of the queue including extensions.

            Args:
                extension_id: ID of the extension

            """
            async for hook_path in (self.documentation_base_path / "hooks").iterdir():
                if hook_path.stem == f"{extension_id}":
                    return await hook_path.read_text()
            return "no such extension documented"

        @tool
        async def get_extension_logs(
            extension_id: int,
            request_id: str = None,
            annotation_id: int = None,
            log_level: str = None,
            queue_id: int = None,
            search: str = None,
        ):
            """
            Returns logs of a specific Rossum extension (hook).

            Args:
                extension_id: ID of the extension
                request_id: [Optional] filter out only logs for this correlation ID
                annotation_id: [Optional] comma-separated string of annotation IDs to which the logs should be related to
                log_level: [Optional] comma-separated string of log levels (INFO, WARNING, ERROR)
                queue_id [Optional] comma-separated string of queue IDs to which the logs should be related to
                search [Optional] full-text filter across log entry fields

            """
            try:
                return await self.client.request_json(
                    method="GET",
                    url="hooks/logs",
                    params={
                        "hook": extension_id,
                        "request_id": request_id,
                        "annotation": annotation_id,
                        "queue": queue_id,
                        "log_level": log_level,
                        "search": search,
                    },
                )
            except Exception as e:
                display_error(f"Error while getting logs: {e}")
                return None

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
            get_queue_documentation,
            get_extension_documentation,
            get_extension_logs,
            get_local_object_json,
            get_remote_hook_json,
            search_knowledge_base,
            make_data_storage_request,
        ]

    async def stream_call(self, user_input: str) -> AsyncGenerator[str, None]:
        # --- Pre-check user input token length ---
        user_input_message = HumanMessage(content=user_input)
        user_input_tokens = self._get_messages_tokens([user_input_message])
        max_allowed_for_single_message = int(
            self.memory.max_token_limit * self.MAX_INDIVIDUAL_MESSAGE_FRACTION
        )

        if user_input_tokens > max_allowed_for_single_message:
            # If the user input is too large, attempt to summarize it
            self._debug_print(
                f"DEBUG: User input too long ({user_input_tokens} tokens). Summarizing..."
            )
            yield f"--- Your input was too long ({user_input_tokens} tokens) and has been summarized to fit the conversation memory. ---\n\n"
            try:
                # Use a separate LLM call to summarize the user's input
                summary_prompt = f"Summarize the following text concisely to fit within {max_allowed_for_single_message} tokens, retaining all key information:\n\n{user_input}"
                summary_result = await self.summary_llm.ainvoke(
                    [HumanMessage(content=summary_prompt)]
                )

                user_input_message = HumanMessage(content=summary_result.content)
                current_input_tokens = self._get_messages_tokens([user_input_message])
                self.total_input_tokens += current_input_tokens
                self._debug_print(
                    f"DEBUG: User input summarized to {current_input_tokens} tokens."
                )
            except Exception as e:
                self._debug_print(
                    f"DEBUG: Failed to summarize user input: {e}. Using truncated input instead."
                )
                # Fallback to simple truncation if summarization fails
                user_input_message = HumanMessage(
                    content=user_input[: max_allowed_for_single_message * 4] + "..."
                )  # Rough character estimate for tokens
                yield f"--- Failed to summarize your input. It has been truncated to fit the conversation memory. ---\n\n"

        self.memory.chat_memory.add_message(
            user_input_message
        )  # Add the original or processed user message

        while True:
            messages_for_llm = self.memory.load_memory_variables({})[
                self.memory.memory_key
            ]

            # Calculate input tokens for the current turn, which is the entire message history from memory
            current_input_tokens = self._get_messages_tokens(messages_for_llm)
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
                first_chunk = await anext(llm_stream)
                full_ai_message_chunk = first_chunk
            except StopAsyncIteration:
                self._debug_print("DEBUG: LLM returned no content or tool calls.")
                self.memory.chat_memory.add_ai_message("")
                break

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

            async for chunk in llm_stream:
                full_ai_message_chunk += chunk

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

            final_ai_message_for_history = AIMessage(
                content=full_ai_message_chunk.content,
                tool_calls=full_ai_message_chunk.tool_calls,
            )
            self.memory.chat_memory.add_message(final_ai_message_for_history)

            ai_response_tokens = self._get_messages_tokens(
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

            if not final_ai_message_for_history.tool_calls:
                self._debug_print(
                    "DEBUG: No tool calls in final AI message. Breaking loop."
                )
                break

            self._debug_print("DEBUG: Executing tool calls...")
            for tool_call in final_ai_message_for_history.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args")
                tool_id = tool_call.get("id")

                if not tool_name or tool_args is None or not tool_id:
                    self._debug_print(
                        f"DEBUG: Malformed tool call found: {tool_call}. Skipping."
                    )
                    yield f"--- Tool Error: Malformed tool call received: {tool_call} ---\n\n"
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

                        # --- Post-check tool output token length ---
                        tool_output_tokens = self._get_messages_tokens(
                            [ToolMessage(content=tool_output_str, tool_call_id=tool_id)]
                        )
                        if tool_output_tokens > max_allowed_for_single_message:
                            self._debug_print(
                                f"DEBUG: Tool output too long ({tool_output_tokens} tokens). Summarizing..."
                            )
                            yield f"--- Tool output was too long ({tool_output_tokens} tokens) and has been summarized to fit the conversation memory. ---\n\n"
                            try:
                                # Use a separate LLM call to summarize the tool's output
                                summary_prompt = f"Summarize the following tool output concisely to fit within {max_allowed_for_single_message} tokens, retaining all key information:\n\n{tool_output_str}"
                                summary_result = await self.summary_llm.ainvoke(
                                    [HumanMessage(content=summary_prompt)]
                                )
                                tool_output_str = summary_result.content
                                tool_message = ToolMessage(
                                    content=tool_output_str,
                                    tool_call_id=tool_id,
                                )

                                current_input_tokens = self._get_messages_tokens(
                                    [tool_message]
                                )

                                self._debug_print(
                                    f"DEBUG: Tool output summarized to {current_input_tokens} tokens."
                                )
                            except Exception as e:
                                self._debug_print(
                                    f"DEBUG: Failed to summarize tool output: {e}. Using truncated output instead."
                                )
                                tool_output_str = (
                                    tool_output_str[
                                        : max_allowed_for_single_message * 4
                                    ]
                                    + "..."
                                )  # Rough char estimate
                                yield f"--- Failed to summarize tool output. It has been truncated to fit the conversation memory. ---\n\n"

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
                    self.memory.chat_memory.add_ai_message(error_msg)
                    break
