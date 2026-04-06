# 05. Building Block View

This section provides an overview of the system's architecture, following Hexagonal Architecture principles to ensure modularity and separation of concerns.

## Level 1: White Box

The system is organized into the following key packages:

*   **API Layer (`src/api`):** Handles incoming HTTP/WebSocket requests, parameter validation, and routing.
*   **Schemas (`src/schemas`):** Defines data contracts (request/response models).
*   **Services (`src/services`):** The orchestration layer containing business logic.
    *   **Orchestrator (`src/services/orchestrator`):** Centralizes TTS generation flow (streaming, SSML processing).
*   **Domain (`src/domain`):** Core business logic and domain entities (e.g., Voice models).
*   **Repositories (`src/repositories`):** Abstracts data access layers (e.g., SQLite interaction).
*   **Infrastructure (`src/infrastructure`):** Infrastructure adapters (e.g., audio conversion, caching, cleanup).
*   **Engine (`src/engine`):** Infrastructure adapters implementing the actual TTS synthesis logic.
*   **Core (`src/core`):** Interfaces (ports) and domain-specific exceptions.

## Diagram (PlantUML)

```kroki-plantuml
@startuml
[FastAPI Routes] as API <<API Layer>>
[Data Contracts] as Schemas <<Schemas>>
[Services] as Services <<Services>>
[Orchestration] as Orchestrator <<Orchestrator>>
[Domain Logic] as Domain <<Domain>>
[Repositories] as Repos <<Repositories>>
[Infrastructure] as Infra <<Infrastructure>>
[TTS Engines] as Engine <<Engine>>
[Core Interfaces] as Core <<Core>>

API --> Schemas : uses
API --> Orchestrator : calls
Orchestrator --> Services : uses
Services --> Domain : manages
Domain --> Repos : persists
Services --> Infra : uses
Services --> Engine : invokes
Engine --> Core : implements
@enduml
```
