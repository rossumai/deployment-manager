from __future__ import annotations

import subprocess

from deployment_manager.ai_agent.llm.base import LLMClient


class GeminiSubprocessLLMClient(LLMClient):
    def __init__(self, command: str = "gemini", use_stdin: bool = True):
        self._command = command
        self._use_stdin = use_stdin

    async def run(self, prompt: str) -> str:
        if "\x00" in prompt:
            prompt = prompt.replace("\x00", "")
        try:
            if self._use_stdin:
                result = subprocess.run(
                    [self._command, "-p", "-"],
                    input=prompt,
                    check=False,
                    capture_output=True,
                    text=True,
                )
            else:
                result = subprocess.run(
                    [self._command, "-p", prompt],
                    check=False,
                    capture_output=True,
                    text=True,
                )
        except FileNotFoundError:
            return f"Gemini command not found: {self._command}"
        output = (result.stdout or "").strip()
        if not output:
            output = (result.stderr or "").strip()
        return output
