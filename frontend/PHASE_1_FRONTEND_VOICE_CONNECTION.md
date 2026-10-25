# Phase 1 — Frontend Voice Connection

## Goal

Connect the browser UI to the Python token API and the LiveKit production agent for a real-time, audio-only conversation.

## Request and media flow

1. The user opens the Vite frontend and selects **Start conversation**.
2. The frontend requests a participant token from Flask at `/api/token`, using a unique `garage-room-<uuid>` room name for each conversation.
3. Flask loads the LiveKit URL and API credentials from the project-root environment files, ensures the room exists, and dispatches `garage-phone-agent`.
4. Flask returns a participant JWT and LiveKit server URL to the browser.
5. The browser joins the room using LiveKit's React components and publishes microphone audio.
6. The production agent handles the conversation; LiveKit delivers the agent's audio back to the browser.
7. The UI shows connection/agent status and lets the user end the session.

The browser never receives the LiveKit API secret. Flask handles token creation and dispatch; LiveKit carries the audio media.

## Implemented frontend behavior

- Connects using the returned token and URL.
- Enables microphone audio and plays remote agent audio.
- Shows connecting, waiting, listening, thinking, and speaking states.
- Reports token API, LiveKit connection, and microphone errors.
- Provides an end-conversation action.
- Reads the Flask origin from `VITE_TOKEN_API_URL`; when unset, it uses `http://127.0.0.1:5000`.

## Backend requirements

- Flask API available at the configured token API URL.
- Correct `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` configured on the backend.
- Agent name must remain `garage-phone-agent` and dispatch must target the intended deployment (currently production).
- Keep the local legacy `python backend/agent.py dev` worker stopped when testing the production deployment; it can claim production jobs and, in this setup, its inference requests timed out.

## How to run locally

Start Flask in one terminal:

```powershell
.\venv\Scripts\python.exe backend\server.py
```

Start Vite in another terminal:

```powershell
Set-Location frontend
npm run dev
```

Open the Vite URL (usually `http://localhost:5173/`) and start a conversation. Do not open the Flask root URL as a website; Flask serves the API, so `/` returns 404.

## Completion criteria

- The browser receives a valid token for its unique `garage-room-<uuid>` session room.
- The browser joins the intended LiveKit project and the production agent joins the room.
- Microphone audio reaches the agent and the agent's audio is audible in the browser.
- Connection errors and disconnects are visible and recoverable.

## Current boundary

This phase provides audio connection and session UI. Typed chat and transcript display were added afterward and are documented in `PRE_PHASE_3_TEXT_CHAT_AND_TRANSCRIPTS.md`. Agent video/avatar, customer camera input, and a structured vehicle-profile panel remain unimplemented.
