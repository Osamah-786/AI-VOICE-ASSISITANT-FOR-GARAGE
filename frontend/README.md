# Frontend

The frontend is a React and JavaScript single-page application built with Vite. It connects to the Flask token API, joins LiveKit, publishes microphone audio, sends typed messages, and displays spoken transcriptions and agent state.

## Folder tree

```text
frontend/
├── README.md
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
├── BACKEND_INTEGRATION_PHASES.md
├── PHASE_1_FRONTEND_VOICE_CONNECTION.md
├── PHASE_2_VEHICLE_PROFILES.md
├── PRE_PHASE_3_TEXT_CHAT_AND_TRANSCRIPTS.md
├── public/
│   ├── README.md
│   ├── favicon.svg
│   └── icons.svg
└── src/
    ├── README.md
    ├── App.jsx
    ├── App.css
    ├── index.css
    ├── main.jsx
    └── assets/
        ├── README.md
        ├── hero.png
        ├── react.svg
        └── vite.svg
```

## How the files connect

```mermaid
flowchart TD
    HTML[index.html] --> Main[src/main.jsx]
    Main --> App[src/App.jsx]
    App --> Styles[App.css and index.css]
    App -->|GET /api/token| Flask[Backend token API]
    App -->|LiveKitRoom: audio, lk.chat, lk.transcription| LK[LiveKit room]
    LK --> Agent[Garage AI agent]
    Public[public/favicon.svg and icons.svg] -. static files .-> HTML
    Assets[src/assets: hero, React, Vite images] -. available assets; currently not imported .-> App
    Package[package.json and package-lock.json] --> Vite[vite.config.js and Vite commands]
    Docs[Phase and integration markdown] -. implementation notes .-> App
```

- `index.html` supplies the page root and loads `src/main.jsx`.
- `main.jsx` mounts `App.jsx` inside React Strict Mode and loads global CSS.
- `App.jsx` controls connection lifecycle, conversation status, typed messages, transcriptions, and LiveKit audio.
- `App.css` styles the assistant and conversation UI; `index.css` provides global styles.
- Vite serves `public/` files directly and bundles imported source files under `src/`.
- The phase documents record integration and feature requirements. [FUTURE_GOALS.md](../FUTURE_GOALS.md) is the current list of not-yet-implemented work.

## Frontend conversation diagram

```mermaid
sequenceDiagram
    actor Customer
    participant App as App.jsx
    participant Flask as Flask token API
    participant LK as LiveKit room
    participant Agent as Garage AI

    Customer->>App: Start conversation
    App->>App: Create unique room and participant IDs
    App->>Flask: Request token
    Flask-->>App: JWT and LiveKit URL
    App->>LK: Join with microphone audio
    Customer->>LK: Speak or send typed message on lk.chat
    LK->>Agent: Deliver input
    Agent-->>LK: Reply audio and lk.transcription text
    LK-->>App: Audio track and transcript streams
    App-->>Customer: Play speech and display conversation
    Customer->>App: End or reconnect
    App->>LK: Disconnect and clear current session UI
```

Typed and spoken turns share the active LiveKit session. The frontend does not connect to SQLite and does not contain LiveKit API secrets.

## Run and verify

```powershell
npm ci
npm run dev
```

Set `VITE_TOKEN_API_URL` only when the Flask API is not at its local default (`http://127.0.0.1:5000`). Do not put LiveKit API keys or secrets in Vite environment variables.

Useful checks:

```powershell
npm run lint
npm run build
```
