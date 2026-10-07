from livekit.agents import Agent


class AssistantFnc:
    """Functions/tools for the voice assistant."""

    async def ask_assistant(self, question: str) -> str:
        """
        Answer a question from the user.

        Args:
            question: The question to answer.
        """
        return question