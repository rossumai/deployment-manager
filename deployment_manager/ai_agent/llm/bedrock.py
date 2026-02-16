from __future__ import annotations

from deployment_manager.ai_agent.llm.base import LLMClient
from deployment_manager.commands.document.llm_helper import LLMHelper


class BedrockLLMClient(LLMClient):
    def __init__(self, model_id: str | None = None):
        self._helper = LLMHelper(model_id=model_id)

    async def run(self, prompt: str) -> str:
        response = await self._helper.run(prompt)
        if response and response.text:
            return response.text
        return ""

    def validate(self) -> bool:
        return self._helper.validate_credentials()
