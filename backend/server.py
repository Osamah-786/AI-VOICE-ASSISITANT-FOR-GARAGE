from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import re
import time
from threading import Lock

import aiohttp

from livekit.api import AccessToken, LiveKitAPI, VideoGrants
from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest
from livekit.protocol.room import CreateRoomRequest, ListRoomsRequest

import config  # Loads project-root .env files.

app = Flask(__name__)
CORS(app)

AGENT_NAME = "garage-phone-agent"
_ROOM_NAME_RE = re.compile(r"^garage-room-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
_PARTICIPANT_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_dispatch_lock = Lock()


def _is_livekit_error(exc: Exception, code: str) -> bool:
    return getattr(exc, "code", None) == code


def _is_transient_error(exc: Exception) -> bool:
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, aiohttp.ClientError, OSError)):
        return True
    return getattr(exc, "status", None) in (408, 429, 500, 502, 503, 504)


def _prepare_agent_dispatch(room_name: str, livekit_url: str, api_key: str, api_secret: str) -> None:
    for attempt in range(2):
        try:
            asyncio.run(_ensure_agent_dispatch(room_name, livekit_url, api_key, api_secret))
            return
        except Exception as exc:
            if attempt == 0 and _is_transient_error(exc):
                time.sleep(0.2)
                continue
            raise


async def _ensure_agent_dispatch(room_name: str, livekit_url: str, api_key: str, api_secret: str) -> None:
    """Ensure the session room and an active agent job exist before issuing a token."""
    livekit_api = LiveKitAPI(url=livekit_url, api_key=api_key, api_secret=api_secret)
    try:
        rooms = await livekit_api.room.list_rooms(ListRoomsRequest(names=[room_name]))
        if not rooms.rooms:
            try:
                await livekit_api.room.create_room(CreateRoomRequest(name=room_name))
            except Exception as exc:
                # Another server process may have created this unique session room first.
                if not _is_livekit_error(exc, "already_exists"):
                    raise

        try:
            dispatches = await livekit_api.agent_dispatch.list_dispatch(room_name)
        except Exception as exc:
            # The room may have been auto-closed between list_rooms and list_dispatch.
            # Creating a dispatch also creates the room if needed.
            if not _is_livekit_error(exc, "not_found"):
                raise
            dispatches = []

        active_dispatch = any(
            dispatch.agent_name == AGENT_NAME
            and (
                not dispatch.state.jobs
                or any(job.state.status in (0, 1) for job in dispatch.state.jobs)  # pending or running
            )
            for dispatch in dispatches
        )
        if active_dispatch:
            return

        await livekit_api.agent_dispatch.create_dispatch(
            CreateAgentDispatchRequest(agent_name=AGENT_NAME, room=room_name)
        )
    finally:
        await livekit_api.aclose()


@app.route("/api/token", methods=["GET"])
def get_token():
    room_name = request.args.get("room", "")
    participant_name = request.args.get("participant", "")

    if not _ROOM_NAME_RE.fullmatch(room_name):
        return jsonify({"error": "A valid session room name is required."}), 400
    if not _PARTICIPANT_RE.fullmatch(participant_name):
        return jsonify({"error": "A valid participant identity is required."}), 400

    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")
    if not api_key or not api_secret or not livekit_url:
        app.logger.error("LiveKit configuration is incomplete")
        return jsonify({"error": "LiveKit service is not configured."}), 503

    try:
        # Flask's dev server runs one process; this lock prevents duplicate jobs for
        # concurrent token requests targeting the same session in that process.
        with _dispatch_lock:
            _prepare_agent_dispatch(room_name, livekit_url, api_key, api_secret)
    except Exception as exc:
        app.logger.error("LiveKit agent dispatch failed for room %s: %s", room_name, exc)
        return jsonify({"error": "Unable to prepare the voice agent. Please retry."}), 502

    try:
        token = (
            AccessToken(api_key, api_secret)
            .with_identity(participant_name)
            .with_name(participant_name)
            .with_grants(VideoGrants(room_join=True, room=room_name))
            .to_jwt()
        )
    except Exception:
        app.logger.exception("Failed to create LiveKit participant token")
        return jsonify({"error": "Unable to create a LiveKit connection token."}), 500

    return jsonify({"token": token, "url": livekit_url, "room": room_name})


if __name__ == "__main__":
    # Local-only development server. Use a production WSGI server for deployment.
    app.run(host="127.0.0.1", port=5000, debug=False)
