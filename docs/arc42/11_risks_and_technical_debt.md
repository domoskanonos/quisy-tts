# 11. Risks and Technical Debt

*   **GPU Dependency:** High reliance on CUDA for acceptable performance. Fallback to CPU is slow.
*   **Database Migrations:** Manual migration in `VoiceRepository` is fragile as the codebase grows. Future: transition to an automated migration framework (e.g., `alembic`).
*   **Dependency Management:** Strict dependencies on `qwen-tts` may limit upgrades.
*   **Documentation:** Maintaining Arc42 documentation along with code changes requires discipline.
