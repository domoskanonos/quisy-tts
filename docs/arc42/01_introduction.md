# arc42 Documentation - Quisy TTS API

Welcome to the documentation for the Quisy TTS API. This documentation follows the arc42 standard.

## 01. Introduction and Goals
- **Objective:** Production-ready Text-to-Speech API.
- **Key Quality Goals:** Modularity, Testability, Resilience.

## 02. System Scope and Context
- The API interacts with LLM engines (Qwen) and audio processing tools (Sox).

## 03. Building Block View
- **API Layer:** FastAPI routes, dependency injection.
- **Services:** Core business logic.
- **Core:** Interfaces and shared exceptions.
- **Infrastructure:** Adapters for external engines/audio.
