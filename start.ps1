param(
    [switch]$RunLocalAgent
)

# Start the Flask token server and frontend. LiveKit Cloud runs the production agent.
$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot 'venv\Scripts\python.exe'

Start-Process -FilePath $python -WorkingDirectory $projectRoot -ArgumentList 'backend/server.py'

if ($RunLocalAgent) {
    Start-Process -FilePath $python -WorkingDirectory $projectRoot -ArgumentList 'backend/agent.py dev'
}

Set-Location (Join-Path $projectRoot 'frontend')
npm run dev
