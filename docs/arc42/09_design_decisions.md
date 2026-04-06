# 09. Design Decisions

*   **Hexagonal Architecture:** Chosen to ensure core business logic remains independent of the FastAPI framework and SQLite persistence layer.
*   **Repository Pattern:** Adopted for `VoiceRepository` to encapsulate data access, allowing for easier testing and future database migrations.
*   **Orchestrator Pattern:** Implemented in `src/services/orchestrator/` to manage the complex, multi-step process of TTS generation (SSML -> Model -> Audio).
*   **AudioConverter Interface:** Decouples audio format transformation logic, enabling flexibility for adding new formats without modifying existing service code.
