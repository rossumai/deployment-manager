from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    async def run(self, prompt: str) -> str:
        ...

    def validate(self) -> bool:
        return True
