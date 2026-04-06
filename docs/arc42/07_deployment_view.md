# 07. Deployment View

*   **Local Development:** Run via `uv run start-dev`. Uses `sqlite` in `data/app_data/`.
*   **Docker Container:**
    *   Base image: `python:3.12-slim` + CUDA dependencies.
    *   Exposed Port: 8045.
    *   Volume mounts: `/app/models`, `/app/output`.
*   **Scalability:** Horizontal scaling is constrained by GPU resources; recommended deployment is GPU-accelerated container instances.
