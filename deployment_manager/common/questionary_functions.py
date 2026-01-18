import sys
from typing import Any

from questionary import Question


# Question.ask_async() implementation without catching KeyboardInterrupt exception and returning None instead
async def ask_async_with_interruption(question: Question) -> Any:
    sys.stdout.flush()
    value = await question.unsafe_ask_async()
    return value
