# Frontend ↔ Backend Integration Roadmap

This document describes a phased plan for connecting the Garage AI frontend to its Python backend and, optionally, adding video support. The current codebase has a Flask token endpoint and a LiveKit voice agent. The frontend should use Flask only for connection credentials and session setup; LiveKit carries real-time audio/video directly between the browser and room participants.

## Current implementation status

- Phases 1 and 2 are implemented: `/api/token` dispatches `garage-phone-agent` for validated unique `garage-room-<uuid>` sessions, and the agent uses the vehicle tools in `backend/api.py`.
- The frontend exists in `frontend/src/App.jsx`; it connects audio, sends typed messages, displays voice transcriptions, and handles disconnects.
- The local SQLite vehicle lookup/create flow is connected to the agent. Shared durable storage and production hardening remain future work.
- This roadmap describes the implemented phases and the remaining video/avatar and deployment options. See the root `FUTURE_GOALS.md` for the current outstanding work list.

## Phase 1 — Connect the browser to the voice backend (implemented)

**Goal:** Make the existing audio conversation connect reliably from the frontend.

The current implementation uses a unique `garage-room-<uuid>` for each conversation, validates it at the Flask token endpoint, and dispatches the named agent before returning the participant JWT. Remaining production tasks such as strict CORS origins and deployment configuration are listed in Phase 4.

### Backend work

1. Keep `/api/token` as the only frontend-facing credential endpoint. The LiveKit API secret must stay on the server and must never be bundled into Vite environment variables.
2. Generate a unique `garage-room-<uuid>` for each conversation and pass it explicitly to `/api/token`; this isolates reconnects and concurrent sessions.
3. Return a small, stable response shape such as `{ token, url, room }` and return useful HTTP errors for missing configuration or dispatch failure.
4. Configure CORS for the local frontend origin during development and the deployed site origin in production.
5. Load root `.env` settings consistently when the API is run directly or via `start.ps1`.

### Frontend work

1. Add a small connection helper that calls the Flask endpoint and validates the response before joining LiveKit.
2. Connect using `LiveKitRoom` with the returned token and URL; publish microphone audio and keep video disabled for this audio-only phase.
3. Render room connection state, agent availability, microphone permission errors, transcript events, and a disconnect action.
4. Read the backend URL from a public frontend setting (for example `VITE_TOKEN_API_URL`) instead of hard-coding `127.0.0.1`; the value is a URL, not a secret.

### Acceptance checks

- Clicking **Start Conversation** obtains a token and joins the intended room.
- The backend dispatches one voice agent and the browser receives its audio.
- Permission denial, API errors, and disconnects return the UI to a recoverable state.

## Phase 2 — Make the conversation use vehicle data (implemented)

**Goal:** Let the running agent retrieve and create vehicle profiles through the SQLite-backed function tools.

`AssistantFnc` is attached to the LiveKit agent, and the browser displays the corresponding typed and spoken conversation. A separate structured vehicle-details panel is not implemented.

### Backend work

1. Attach `AssistantFnc` from `backend/api.py` to the `Agent`/session using the function-tool API supported by the installed LiveKit Agents version.
2. Make VIN lookup, profile creation, and current vehicle details callable by the LLM; validate VIN and required car fields before database writes.
3. Handle duplicate VINs and database failures as actionable tool results instead of uncaught exceptions.
4. Update the system prompt to make the agent collect missing fields explicitly and confirm vehicle details before continuing.
5. Decide where SQLite data lives and how it is backed up for the deployment environment.

### Frontend work

1. Continue using LiveKit transcription events to display user and agent turns; do not have the browser call the SQLite code directly.
2. Show clear progress and error states while the assistant is identifying a vehicle.
3. If the product needs structured vehicle details on screen, send a deliberate data event from the backend or expose a separately authenticated API; avoid inferring structured data from transcript text.

### Acceptance checks

- An existing VIN returns the matching profile through the voice conversation.
- An unknown VIN can be handled through the agreed profile creation flow.
- Duplicate or invalid records produce a spoken, user-friendly response and do not break the session.

## Phase 3 — Add video, choosing the feature first

LiveKit's video guide describes two different directions. Choose one (or both) before implementation because the backend and UI work differs.

### Option A: Show a generated agent avatar

1. Select an avatar provider, install its backend plugin, and configure provider credentials on the server.
2. In `backend/agent.py`, create and start an avatar session attached to the existing `AgentSession` in the same LiveKit room.
3. In the React voice component, use `useVoiceAssistant()` to read `videoTrack` alongside `audioTrack` and render the track when available.
4. Keep the existing voice UI as the fallback while the avatar worker connects or when no video track exists.
5. If using lower-level participant lookup instead of the hook, distinguish the avatar worker using its agent participant kind and `lk.publish_on_behalf` attribute; do not treat every remote participant as the voice agent.

### Option B: Let a customer share camera video for vehicle inspection

1. Add a user-controlled camera preview and consent/enable action in the frontend.
2. Publish the camera track to the same LiveKit room and add explicit stop-camera controls and permission/error handling.
3. Update the Python agent to receive video. For sampled images in the current STT→LLM→TTS design, subscribe to the user's video track, sample frames, and attach a suitable frame to the user's chat turn using `ImageContent`.
4. Resize/limit frame rate and only send frames when useful; video frames consume model input and can increase latency and cost.
5. If true continuous live video understanding is required, switch to a supported realtime model and enable the corresponding video input configuration. The current Gemini Flash pipeline should not be assumed to support live video input.

### Acceptance checks

- Avatar option: the browser renders the avatar video track and continues to play synchronized agent audio.
- Camera option: the browser publishes only after user action, the agent can describe a relevant sampled frame, and camera sharing stops cleanly on disconnect.
- For either option, audio-only conversation remains usable if video is unavailable.

## Phase 4 — Prepare for deployment and operations

**Goal:** Replace local development assumptions with an operational integration.

1. Configure frontend API origin per environment and serve the site over HTTPS (required for browser microphone/camera access outside localhost).
2. Restrict CORS, validate requested room and participant identity, rate-limit token issuance, and avoid exposing secrets in logs or client responses.
3. Move persistent vehicle data to an appropriate managed database if the service needs multi-instance deployment or durable production records.
4. Add structured logging and monitoring for token issuance, dispatch, room connection, agent errors, and optional video availability.
5. Verify LiveKit quotas, provider credentials, consent/privacy behavior, and expected video bandwidth/cost before release.

## Recommended next steps

1. Verify reconnect and vehicle-profile behavior against the LiveKit Cloud production agent.
2. Choose an avatar, customer camera input, or both; then implement the matching Phase 3 path.
3. Complete Phase 4 before public deployment.

## Documentation references

- [LiveKit Agents: Video and frontend integration](https://docs.livekit.io/agents/multimodality/vision/video/#frontend-integration)
- [LiveKit React components](https://docs.livekit.io/reference/components/react/)
