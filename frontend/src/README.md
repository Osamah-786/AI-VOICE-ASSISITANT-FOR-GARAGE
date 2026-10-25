# Frontend source

This folder contains the React application entry point, conversation UI, and styles.

## Folder tree

```text
frontend/src/
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
    Main[main.jsx] --> App[App.jsx]
    Main --> Global[index.css]
    App --> ComponentStyles[App.css]
    App --> Backend[GET /api/token]
    App --> LK[LiveKit React components]
    LK -->|audio, typed input, transcriptions| App
    Assets[assets/] -. optional imports .-> App
```

- `main.jsx` mounts the app into the `#root` element from `frontend/index.html`.
- `App.jsx` owns token fetching, unique room/participant IDs, LiveKit connection, audio playback, typed chat, transcript rendering, and disconnect cleanup.
- `App.css` styles the page-level application and conversation components.
- `index.css` defines global document and typography styles.
- `assets/` holds image files. The current application does not import these starter assets.

## Runtime flow

```mermaid
flowchart LR
    Start[Start button] --> Token[Fetch token from Flask]
    Token --> Join[Mount LiveKitRoom with audio]
    Join --> Input{Customer input}
    Input -->|Microphone| Agent[LiveKit agent]
    Input -->|Typed text on lk.chat| Agent
    Agent --> Output[Audio reply and lk.transcription]
    Output --> UI[Render status and chronological messages]
    UI --> Stop[End or disconnect]
    Stop --> Reset[Unmount session and clear in-memory transcript]
```

The backend manages credentials and agent dispatch. This source folder handles the browser interaction and real-time UI only.
