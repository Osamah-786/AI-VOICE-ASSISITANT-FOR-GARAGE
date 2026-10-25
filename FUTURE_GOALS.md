# Future goals and remaining work

This file distinguishes features already present from work that is still planned. It is a living implementation roadmap, not a promise that every item is in progress.

## Already implemented

- Browser-to-Flask token flow and LiveKit Cloud agent dispatch.
- Unique `garage-room-<UUID>` room per conversation to make reconnects and concurrent sessions independent.
- Voice conversation with microphone publishing, agent audio playback, connection/error states, and session cleanup.
- Typed message sending over LiveKit `lk.chat`.
- Customer/agent speech transcript display over `lk.transcription`, including current session chronology and in-memory reset on disconnect.
- LiveKit agent voice pipeline and conversational instructions.
- VIN lookup, validated vehicle profile creation, duplicate handling, and SQLite persistence.
- Mocked Flask token/dispatch tests; frontend lint/build scripts.

## Not implemented yet

### 1. Agent avatar and video experience

- Replace the decorative orb with an agent avatar that responds to listening, thinking, and speaking states.
- Decide whether the avatar is a local animated visual or a LiveKit-published video participant.
- If camera input is added, request permission only after explicit user action, show camera state clearly, and stop tracks when the session ends.
- For video understanding, implement the LiveKit Agents vision/video path and decide how frames are sampled and sent to the agent.

### 2. Durable vehicle storage

- Replace local SQLite with a managed/shared database before running multiple backend or agent instances.
- Define migrations, backups, retention, and environment-specific database configuration.
- Add integration tests for vehicle tool behavior against an isolated test database.

### 3. Production deployment and security

- Deploy the token API behind HTTPS using a production WSGI server.
- Restrict CORS to approved frontend origins and add abuse controls such as rate limiting and request monitoring.
- Validate the deployment and LiveKit project configuration without exposing API secrets to the browser.
- Define health checks, structured logs, alerting, and operational recovery for API, agent, and database failures.

### 4. Broader service workflows

- Appointment availability and booking.
- Service-department routing or human handoff.
- Repair history and other vehicle information from approved data sources.
- Diagnostic guidance only after its data source, limits, and customer messaging are defined.

The agent prompt currently avoids claiming that appointments are booked or vehicles are diagnosed because no such tools are connected.

### 5. Verification and product decisions

- Add frontend component or browser tests for connect, reconnect, text send, transcript updates, and disconnect cleanup.
- Add an opt-in LiveKit Cloud end-to-end smoke test for room creation, agent dispatch, audio, and transcriptions.
- Decide whether transcripts should ever be persisted. They currently live only in the active browser session.
- Review unused starter assets and stale phase documents after the current implementation is accepted.

## Suggested order

1. Confirm the browser reconnect path against the production LiveKit agent.
2. Select the avatar/video behavior and implement it as a separate feature.
3. Move vehicle data to durable shared storage before scaling beyond local development.
4. Add production deployment controls and end-to-end monitoring.
5. Add booking, routing, or diagnostic workflows only after the required service integrations are available.
