# Frontend public files

Vite copies files in `public/` to the site output without bundling or renaming them.

## Folder tree

```text
frontend/public/
├── README.md
├── favicon.svg
└── icons.svg
```

## How the files connect

```mermaid
flowchart LR
    Favicon[favicon.svg] -->|referenced by| HTML[frontend/index.html]
    Icons[icons.svg] -->|available at site root| Browser[Browser static-file request]
```

`favicon.svg` is referenced by `index.html`. `icons.svg` is available as a static resource; it is not currently imported by the React application.

## Static-file flow

```mermaid
sequenceDiagram
    participant Browser
    participant Vite as Vite dev server or built site
    Browser->>Vite: Request /favicon.svg or /icons.svg
    Vite-->>Browser: Return public asset unchanged
```

These files are presentation assets. They do not participate in token creation, LiveKit media, or agent processing.
