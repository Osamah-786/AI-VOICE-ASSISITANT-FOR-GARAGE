# Frontend source assets

This folder contains image assets that can be imported by the React source code.

## Folder tree

```text
frontend/src/assets/
├── README.md
├── hero.png
├── react.svg
└── vite.svg
```

## How the files connect

```mermaid
flowchart LR
    Images[hero.png, react.svg, vite.svg] -. may be imported by .-> Components[frontend/src/App.jsx or other components]
    Components --> Bundler[Vite asset bundler]
    Bundler --> Output[Hashed production assets]
```

The current application does not import these images. They are retained starter/example assets and can be removed once confirmed unnecessary, or imported when a feature needs them.

## Asset flow

```mermaid
flowchart TD
    Source[Source image] --> Import[JavaScript or CSS import]
    Import --> Vite[Vite build]
    Vite --> Browser[Browser loads optimized output]
```

No backend or LiveKit service reads this folder. Only assets explicitly referenced by frontend code become part of the bundled experience.
