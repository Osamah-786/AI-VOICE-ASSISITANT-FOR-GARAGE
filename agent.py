from __future__ import annotations

from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)

from livekit.plugins import groq, silero
from dotenv import load_dotenv

from api import AssistantFnc
from prompts import INSTRUCTIONS, WELCOME_MESSAGE

load_dotenv()


async def entrypoint(context: JobContext):
    await context.connect(
        auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL
    )

    await context.wait_for_participant()

    assistantfnc = AssistantFnc()

    session = AgentSession(
        llm=groq.LLM(
            model="llama-3.3-70b-versatile",
            temperature=0.8,
        ),
        vad=silero.VAD.load(),
    )

    agent = Agent(
        instructions=INSTRUCTIONS,
        tools=assistantfnc,
    )

    await session.start(
        room=context.room,
        agent=agent,
    )

    await session.generate_reply(
        instructions=WELCOME_MESSAGE
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint
        )
    )