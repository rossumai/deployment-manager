from __future__ import annotations

from deployment_manager.ai_agent.config import AgentConfig
from deployment_manager.ai_agent.llm.base import LLMClient
from deployment_manager.ai_agent.llm.bedrock import BedrockLLMClient
from deployment_manager.ai_agent.llm.gemini import GeminiSubprocessLLMClient


def create_llm_client(config: AgentConfig) -> LLMClient:
    provider = config.provider.lower()
    if provider == "bedrock":
        return BedrockLLMClient(model_id=config.model_id)
    if provider == "gemini":
        return GeminiSubprocessLLMClient(
            command=config.command,
            use_stdin=config.use_stdin,
        )
    return BedrockLLMClient(model_id=config.model_id)
