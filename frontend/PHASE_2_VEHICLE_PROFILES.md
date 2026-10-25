# Phase 2 — Vehicle Profiles and VIN Tools

## Goal

Let the voice agent identify a customer's vehicle using a VIN, retrieve an existing profile, or create a profile after the customer confirms the details.

## Conversation and data flow

1. The agent welcomes the customer and asks for the 17-character VIN.
2. When a VIN is provided, the agent calls `lookup_car`.
3. If the VIN exists, the tool returns its make, model, and year for the agent to confirm with the customer.
4. If no profile exists, the agent asks whether the customer wants to create one.
5. With consent, the agent collects make, model, and year, reads the details back, and waits for confirmation.
6. After confirmation, the agent calls `create_car`; the backend validates the data and writes it to SQLite.
7. The agent confirms success only when the database tool reports that the profile was saved.

Vehicle data remains on the backend. The frontend joins the LiveKit room and presents the voice conversation; it does not access SQLite directly.

## Implemented backend pieces

- `backend/api.py` defines three LiveKit function tools: `lookup_car`, `get_car_details`, and `create_car`.
- `backend/agent.py` creates one `AssistantFnc` instance per agent session and passes its tools to the LiveKit `Agent`.
- `backend/prompts.py` instructs the agent to confirm details, avoid inventing vehicle information, and not claim a save unless the tool succeeds.
- `backend/db_driver.py` persists VIN, make, model, and year in `backend/auto_db.sqlite`.
- Tool operations run database calls off the event loop, validate standard VIN format and year range, and return friendly duplicate/database error results.

## Testing the vehicle flow

Use the frontend with the active production agent deployment, then:

1. Provide a valid 17-character VIN that is not already in the database.
2. Agree to create a profile when asked.
3. Provide make, model, and year; confirm when the agent reads them back.
4. Start another conversation and give the same VIN. The agent should find the saved profile and confirm the returned details.
5. Try the same VIN with a second create request. The existing record should be reported instead of causing the session to fail.

Because vehicle records are stored in SQLite on the machine running the backend/agent, the production deployment must be configured to use durable shared storage if records need to survive redeployments or be available across multiple agent instances. The current local SQLite file is suitable for development, not a multi-instance production database.

## Completion criteria

- A stored VIN lookup returns the matching profile.
- A missing VIN can be created only after the customer confirms all required details.
- Invalid VINs and years are rejected with a clear spoken explanation.
- Duplicate VINs and database errors do not crash the conversation.
- The UI remains connected and receives the agent's spoken response throughout the tool flow.

## Current boundary

The tools support vehicle profile lookup and creation only. They do not book appointments, provide vehicle-history data, diagnose faults, or expose structured vehicle data as a frontend panel.
