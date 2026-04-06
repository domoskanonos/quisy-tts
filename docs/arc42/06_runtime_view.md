# 06. Runtime View

## Request Flow
1.  **Client:** Sends request (HTTP/WS).
2.  **API Layer:** Validates input.
3.  **Services (Orchestrator):** Processes SSML, calls Repository for voice, invokes TTS Engine.
4.  **Engine:** Performs inference on GPU.
5.  **Streaming:** Audio is streamed back to the Client via `async` generator.

## Database Interaction
1.  **Repository:** Performs atomic SQLite queries within `with self._get_conn() as conn:` context managers.
2.  **Migrations:** Handled manually via `_migrate()` in the repository during service initialization.
