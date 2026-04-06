# 10. Quality Requirements

*   **Latency:** Critical target of < 200ms time-to-first-byte (TTFB) for streaming.
*   **Maintainability:** Enforced by strict typing, `ruff` linting/formatting, and `mypy` static analysis.
*   **Testability:** High priority on unit tests for core services and repositories; integration tests for API endpoints.
*   **Availability:** Graceful handling of GPU unavailability via `DEVICE=cpu` mode for non-production environments.
