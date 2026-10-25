# Kilo configuration folder

This folder contains a tool-specific ignore file. It is not part of the Garage AI runtime.

## Folder tree

```text
.kilo/
├── README.md
└── .gitignore
```

## How the files connect

```mermaid
flowchart LR
    Ignore[.gitignore] --> Tool[Local Kilo tooling]
    Tool -. does not affect .-> App[Garage AI backend or frontend]
```

`.gitignore` lists local Kilo-generated package and manager files that should not be tracked. The application does not import or read this directory.

## Tooling flow

```mermaid
flowchart TD
    LocalTool[Developer runs local tool] --> Generated[Tool may create local files]
    Generated --> IgnoreRules[.gitignore filters selected files]
    IgnoreRules --> Git[Git status and commits]
```

This folder has no connection to Flask, React, LiveKit, or vehicle data.
