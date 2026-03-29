# arc42 Documentation - Quisy TTS API

Welcome to the documentation for the Quisy TTS API. This documentation follows the arc42 standard.

## 01. Introduction and Goals
- **Objective:** Production-ready Text-to-Speech API.
- **Key Quality Goals:** Modularity, Testability, Resilience.

## 02. System Scope and Context
- The API interacts with LLM engines (Qwen) and audio processing tools (Sox).
- Voice metadata (voices DB) is authoritative for speaker languages; the API requires callers to provide the target language for synthesis.

## 03. Building Block View
 - **API Layer:** FastAPI routes, dependency injection. All generation endpoints require an explicit `language` parameter; SSML may carry language implicitly via speaker IDs but each voice must have a language set in the DB.
 - **Services:** Core business logic (TTSService orchestration, voice integrity, text splitting, SFX).
 - **Core:** Interfaces and shared exceptions (engine and cache interfaces).
 - **Infrastructure:** Adapters for external engines/audio (Qwen backend, Sox audio processing, File cache).
