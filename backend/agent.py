from __future__ import annotations

from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)

from livekit.plugins import silero
import config  # Loads project-root .env files.
from api import AssistantFnc
from prompts import INSTRUCTIONS, WELCOME_MESSAGE


async def entrypoint(context: JobContext):
    await context.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    await context.wait_for_participant()

    session = AgentSession(
        stt="deepgram/nova-3",
        llm="google/gemini-3-flash-preview",
        tts="fishaudio/s2.1-pro:fa4c9eb3dccc4806b382b40d61c6b10a",
        vad=silero.VAD.load(),
    )

    vehicle_tools = AssistantFnc()
    agent = Agent(
        instructions=INSTRUCTIONS,
        tools=[
            vehicle_tools.lookup_car,
            vehicle_tools.get_car_details,
            vehicle_tools.create_car,
        ],
    )

    await session.start(room=context.room, agent=agent)
    await session.generate_reply(instructions=WELCOME_MESSAGE)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="garage-phone-agent",
        )
    )
