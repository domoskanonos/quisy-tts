# CHANGELOG


## v0.27.0 (2026-04-05)

### Chores

- Update quisy-tts version to 0.26.0
  ([`e142600`](https://github.com/domoskanonos/quisy-tts/commit/e142600f581c0b1f99e5bfad71b4e8cd68994d5e))

### Features

- Update language identifiers to full names and remove default voices
  ([`e96046d`](https://github.com/domoskanonos/quisy-tts/commit/e96046d786e717749e567e5e7fb6cd44529cac14))


## v0.26.0 (2026-04-04)

### Bug Fixes

- Refactor code structure for improved readability and maintainability
  ([`1e209b1`](https://github.com/domoskanonos/quisy-tts/commit/1e209b1df298b0e2ad20d4550f3e8b4caf082562))

### Features

- Add mkdocs-plantuml dependency and installation step in pipeline
  ([`4038bdb`](https://github.com/domoskanonos/quisy-tts/commit/4038bdba0da893b5ebf0fef86ce109f33afed526))

### Refactoring

- Remove unused imports and clean up test file
  ([`c6e98ff`](https://github.com/domoskanonos/quisy-tts/commit/c6e98ff0ab0279fcf8ebde56bcc06f8f541bff1b))


## v0.25.0 (2026-04-03)

### Bug Fixes

- Revert model version to 0.6 and enhance SSML generation documentation
  ([`88ecc49`](https://github.com/domoskanonos/quisy-tts/commit/88ecc49aa559d43216ce19fc82e41ea96a5bdb8a))

### Features

- Add Definition of Done and Team structure documentation
  ([`7f85836`](https://github.com/domoskanonos/quisy-tts/commit/7f85836e154ed4d15e6fd009cafbacff3a17241a))

- Created .dod.md to outline the Definition of Done for project tasks, including code quality,
  testing, documentation, workflow, and security standards. - Established team roles and
  communication guidelines in .team.md.

feat: Implement Voice model and API testing

- Added Voice model in src/domain/voice/models.py with methods for instantiation from database rows
  and filename generation. - Created tests for the Voice model in tests/domain/test_voice_models.py.

test: Enhance API endpoint testing for audio generation

- Developed tests for the audio generation endpoint in tests/api/test_generate_route.py, including
  success and failure scenarios.

test: Implement cleanup service tests

- Added tests for the FileCleanupService in tests/services/test_cleanup_service.py to verify old
  file removal functionality.

test: Add tests for TTS service and default voices

- Created tests for TTSService initialization and audio generation in
  tests/services/test_tts_service.py. - Added a test for the count of default voices in
  tests/services/test_default_voices.py.

test: Implement schema tests for TTSParams

- Added tests for TTSParams functionality in tests/schemas/test_internal.py to ensure parameter
  copying and language resolution.

- Ensure reference audio exists before voice generation in generate_voice function
  ([`f51b8d7`](https://github.com/domoskanonos/quisy-tts/commit/f51b8d7789c2365ea644eb50c0fdc600b1430eb1))

- Update SSML endpoint to accept body content and improve audio generation logic; bump version to
  0.24.0
  ([`4c39561`](https://github.com/domoskanonos/quisy-tts/commit/4c3956193e24619ee55afcc5569d073bc96e405e))

### Refactoring

- Remove SoundEffectService and related functionality; update SSML processing logic
  ([`6641f32`](https://github.com/domoskanonos/quisy-tts/commit/6641f32a955540146a8af62b40ad5ee099f85f60))

- Update MCP server initialization and enhance docstrings for voice-related functions
  ([`26edf95`](https://github.com/domoskanonos/quisy-tts/commit/26edf957e106110e3268313c38fa2061b3002676))


## v0.24.0 (2026-04-01)

### Features

- Enforce Sox requirement for audio processing
  ([`18c37ee`](https://github.com/domoskanonos/quisy-tts/commit/18c37ee19df38bcefdb00736868bf5fe745ba2ac))

### Refactoring

- Replace SoxAudioProcessor with AudioProcessor for audio handling and remove Sox dependencies
  ([`5ff9cc0`](https://github.com/domoskanonos/quisy-tts/commit/5ff9cc02a6b7193c7b46d22eb8b40221b95125a8))


## v0.23.1 (2026-03-31)


## v0.23.0 (2026-03-31)

### Bug Fixes

- Aktualisiere CUDA-Version auf 12.4.1 für Builder und Runtime
  ([`f4a2a6a`](https://github.com/domoskanonos/quisy-tts/commit/f4a2a6aa47369a8a3e4b68068752592a4f004f4f))


## v0.22.1 (2026-03-31)

### Bug Fixes

- Füge 'instruct' Feld zu GenerateRequest hinzu, um Voice-Cloning zu ermöglichen
  ([`3370ce8`](https://github.com/domoskanonos/quisy-tts/commit/3370ce8ab7ae29384ae8d552a5f838bfc0c2c811))

### Features

- Aktualisiere Versionsnummer auf 0.22.0
  ([`2f9f093`](https://github.com/domoskanonos/quisy-tts/commit/2f9f09381dc05fc69f24b11c07f23a1fc34e1e9f))


## v0.22.0 (2026-03-31)

### Bug Fixes

- Entferne nicht benötigte 'attn_implementation' aus den Modell-Lade-Argumenten
  ([`1d1a67c`](https://github.com/domoskanonos/quisy-tts/commit/1d1a67cb6dd8291f155186a9d2abca161b482022))

### Features

- Aktualisiere Standard-Stimmen-ID auf 'german_audiobook_male_narrator_01' und erhöhe die Temperatur
  auf 0.9; passe Beispiele in den Anforderungs-Schemas an; aktualisiere Versionsnummer auf 0.21.0.
  ([`4f2aff0`](https://github.com/domoskanonos/quisy-tts/commit/4f2aff06e870447e032a2934444fcf927603966e))


## v0.21.0 (2026-03-30)


## v0.20.1 (2026-03-30)

### Bug Fixes

- Remove --no-optional flag from uv sync command in pipeline
  ([`3efd196`](https://github.com/domoskanonos/quisy-tts/commit/3efd196d3fd130e7b8a0104e9b1feb70a62700ee))

- Update Dockerfile to include TORCH_CUDA_ARCH_LIST and modify uv sync command in pipeline
  ([`4a45fc5`](https://github.com/domoskanonos/quisy-tts/commit/4a45fc597939146817da8a4bd32902ecd4113eee))

### Chores

- Update model version to 1.7 and bump package version to 0.20.0
  ([`10c8aa2`](https://github.com/domoskanonos/quisy-tts/commit/10c8aa2c17dd9dd9092f4077520bec8dc0b86b3f))

### Features

- Modified
  ([`1ec0cb3`](https://github.com/domoskanonos/quisy-tts/commit/1ec0cb360329810cbbcd23f6496b114e6eba3bba))

### Refactoring

- Reduce default max chunk size from 500 to 200 for improved text splitting
  ([`503a2fd`](https://github.com/domoskanonos/quisy-tts/commit/503a2fd86a0fa2838ea413b92b8dbd4941814633))


## v0.20.0 (2026-03-30)

### Refactoring

- Increase default max chunk size for text splitting and enhance logging in audio generation
  ([`b63765b`](https://github.com/domoskanonos/quisy-tts/commit/b63765b474b61eded5b933e3103ee38d57c105f9))

- Remove unused imports and update package version to 0.19.0
  ([`0f97a0a`](https://github.com/domoskanonos/quisy-tts/commit/0f97a0ae016f7e3751e673ecde1fb8fdbbf1880e))


## v0.19.0 (2026-03-30)

### Features

- Add model version configuration and update version to 0.18.0
  ([`af387c2`](https://github.com/domoskanonos/quisy-tts/commit/af387c2a22e0151c1859f5c6797eb021d84b73fe))

### Refactoring

- Clean up SSMLProcessor and enhance speaker handling logic
  ([`1d18bde`](https://github.com/domoskanonos/quisy-tts/commit/1d18bded1c57e772f068c1e59aa0f48b5d8d3fb4))

- Enhance audio generation logic and add language validation in QwenTextToSpeech
  ([`cb62caf`](https://github.com/domoskanonos/quisy-tts/commit/cb62caf5f3c53f53f4ee07811f66ca955a7c1473))

- Implement audio concatenation functionality and enhance error handling in generator
  ([`9d8e1fe`](https://github.com/domoskanonos/quisy-tts/commit/9d8e1fe36ae4a76a348b60f04b1d07b0dd88a6c7))

- Remove hardcoded model download list and implement dynamic model retrieval
  ([`f32a250`](https://github.com/domoskanonos/quisy-tts/commit/f32a2508d1440a878497750a6c56f4b702f60d00))

- Streamline QwenTextToSpeech class and improve model loading logic
  ([`0c48163`](https://github.com/domoskanonos/quisy-tts/commit/0c4816355e31794117feb305bd9d9a109fe175e2))

- Update model handling and remove deprecated configurations
  ([`2dc7939`](https://github.com/domoskanonos/quisy-tts/commit/2dc7939ce763b5d4f003579ff542dc1df27ddf41))

- Update model version in QwenTextToSpeech and enhance error handling during model loading
  ([`30299a8`](https://github.com/domoskanonos/quisy-tts/commit/30299a8c8660342ed3c667ba54ce77f714e836ca))


## v0.18.0 (2026-03-30)

### Features

- Add extra build dependencies for flash attention
  ([`061b370`](https://github.com/domoskanonos/quisy-tts/commit/061b370a8a98bc0d21c155c31a23fc2de878daaa))


## v0.17.1 (2026-03-30)

### Bug Fixes

- Ensure model is moved to GPU only if loaded and handle audio output correctly
  ([`32e860d`](https://github.com/domoskanonos/quisy-tts/commit/32e860da37e26522d5e50722cf9820f158e33f6a))

### Chores

- Clean up code structure and remove unused code blocks
  ([`db183ce`](https://github.com/domoskanonos/quisy-tts/commit/db183ceb52b1eec4723753eea4ff7748cd549c8d))

- Generate reference audio on-demand only (remove startup background task)
  ([`d450d51`](https://github.com/domoskanonos/quisy-tts/commit/d450d51c94b8643b24b9a59793da0aea80cda220))

### Features

- Add flash attention
  ([`c35dbd3`](https://github.com/domoskanonos/quisy-tts/commit/c35dbd3445a46fbb696d52ae66d234274c04efbe))

### Refactoring

- Clean up imports and remove unused test file
  ([`6828b2f`](https://github.com/domoskanonos/quisy-tts/commit/6828b2f27385bcd11f5a1f6fcfc96cc8cc3554e6))


## v0.17.0 (2026-03-27)


## v0.16.0 (2026-03-27)

### Features

- Pre-install spaCy and download language models for improved NLP support
  ([`ccc0c54`](https://github.com/domoskanonos/quisy-tts/commit/ccc0c544ddae169c0d14db68ebf2bbee5de0babb))

- Pre-install spaCy language models for improved NLP capabilities
  ([`88f5165`](https://github.com/domoskanonos/quisy-tts/commit/88f5165278964a92240acc8f8692fd023cbf9737))

- Update project configuration and dependencies for improved structure and functionality
  ([`6f138f0`](https://github.com/domoskanonos/quisy-tts/commit/6f138f02d98321c997764cd88f25a4bfdfa80eb7))

### Refactoring

- Remove unused import in test_tts_cancellation.py
  ([`d8a0d55`](https://github.com/domoskanonos/quisy-tts/commit/d8a0d55b1103f27b0cb4e48318efc085f1231520))


## v0.15.0 (2026-03-27)

### Bug Fixes

- Add type annotations for FastAPI and APIRouter instances for clarity
  ([`a34e2a1`](https://github.com/domoskanonos/quisy-tts/commit/a34e2a188ed996ce153dcfb8d38509f3c3126231))

- Disable reportUntypedFunctionDecorator for better type checking configuration
  ([`df3fa70`](https://github.com/domoskanonos/quisy-tts/commit/df3fa70e5abb81c4e581e563c906a4ee602c0e3f))

- Ruff format and mypy issues in tests
  ([`675985a`](https://github.com/domoskanonos/quisy-tts/commit/675985a909a181fdd3f16ab57391972e63433258))

- Update directory paths in ProjectSettings to use BASE_DATA_DIR for better organization
  ([`2cd5690`](https://github.com/domoskanonos/quisy-tts/commit/2cd5690f9e94089b9c122265158b47c5a9540d80))

- **api**: Respect force flag for ensure-audio endpoint when audio exists
  ([`cc0118e`](https://github.com/domoskanonos/quisy-tts/commit/cc0118e78877bfa8523d607cbd5d5d12ce86af57))

- **frontend**: Auto-save edits before generating and add cache-busting on playback; subscribe to
  status events
  ([`f1a1df1`](https://github.com/domoskanonos/quisy-tts/commit/f1a1df196cc89b0e424c52188f2ea1c41cd820a6))

- **frontend**: Import primeicons and scope icon font for player buttons
  ([`34ebe1c`](https://github.com/domoskanonos/quisy-tts/commit/34ebe1cfc01a3046fc30ffdbf1cbe7aae6549207))

- **frontend**: Make generateAndPlay public for template usage
  ([`bea4d02`](https://github.com/domoskanonos/quisy-tts/commit/bea4d0217e0f60f31bf6d16bf69a372a2c6b15cc))

- **frontend**: Remove system_prompt usage and add DOM lib + typed error handler
  ([`d76590c`](https://github.com/domoskanonos/quisy-tts/commit/d76590cb8090a3e5039f8b05aaa72334e8ff4aa1))

- **frontend**: Respect force flag and always trigger regeneration when requested
  ([`ce30513`](https://github.com/domoskanonos/quisy-tts/commit/ce30513c14214e722ad3b3bec8feb8030d723a04))

### Chores

- Add .env for local test runs
  ([`918581a`](https://github.com/domoskanonos/quisy-tts/commit/918581a5f644b65a0fcc544817a05d8566948ea8))

- Ignore local app SQLite DB (app/quisy-tts.db)
  ([`89debd1`](https://github.com/domoskanonos/quisy-tts/commit/89debd11973f9f5562b860c1d1e358a49d5b8337))

- Run ruff format and fix mypy test issues; add tests for tts cancellation and set_audio
  ([`111e999`](https://github.com/domoskanonos/quisy-tts/commit/111e999193f9e64490d358fd9dc7c8c7a8759ad7))

- Update `quisy-tts` version in lockfile and add local frontend API proxy configuration.
  ([`4485d07`](https://github.com/domoskanonos/quisy-tts/commit/4485d079de6adbbcc8d39dbce69d0dd2d6c102e7))

- **debug**: Log DB example_text and computed cache key during ref-gen
  ([`ec9fe4a`](https://github.com/domoskanonos/quisy-tts/commit/ec9fe4a4f9bad8ea55ddbc7a541bd7fea3bf2db4))

- **log**: Add informative cache & chunk generation logs
  ([`8026b1e`](https://github.com/domoskanonos/quisy-tts/commit/8026b1e143caf652b0e0fd31fea72811a643ef30))

### Features

- Add MCP server implementation with audio generation tools
  ([`9dec7d9`](https://github.com/domoskanonos/quisy-tts/commit/9dec7d938c49e8b5b7702c9de0db5ad33f006f9c))

- Implemented `generate_base_06b` and `generate_base_17b` for audio generation using voice cloning
  with 0.6B and 1.7B models respectively. - Added `generate_voice_design_17b` for generating audio
  based on natural language voice descriptions. - Created `generate_custom_voice_06b` and
  `generate_custom_voice_17b` for audio generation using specific speakers with 0.6B and 1.7B
  models. - Introduced `list_voices` function to list all available voices and their IDs for use in
  custom or base modes. - Integrated TTS and voice services for audio generation functionality.

- Enhance CI pipeline with Pyright checks, improve VoiceService DB handling, and update tests for
  circular imports
  ([`c66aaab`](https://github.com/domoskanonos/quisy-tts/commit/c66aaabfefb341df2e315d3b4c1e9712239a89a3))

- Implement initial Angular frontend application for Quisy TTS, including core UI components,
  styling, linting, and Playwright tests.
  ([`37ef1ae`](https://github.com/domoskanonos/quisy-tts/commit/37ef1ae954c0ecdef560b0dbfeeeb75877c76d82))

- Implement voice management system with CRUD API, default voices, and integrated frontend
  components.
  ([`b3700a3`](https://github.com/domoskanonos/quisy-tts/commit/b3700a34d3076fe11a243a5f775a68fc3709b7b8))

- Implement voice management with CRUD API, services, and frontend components, alongside TTS
  cancellation and refined audio file handling.
  ([`abdab22`](https://github.com/domoskanonos/quisy-tts/commit/abdab22265661ec5f35ca46ef99028338c36e83e))

- Msus so sein
  ([`be9efa7`](https://github.com/domoskanonos/quisy-tts/commit/be9efa7f94209aba3e6caaa2506a315b6757012f))

- Refactor type checking configurations, enhance error handling in voice creation, and improve
  module imports for better compatibility
  ([`3217bd5`](https://github.com/domoskanonos/quisy-tts/commit/3217bd572a50ca84fc835d05fe70ad7729e7f019))

- Remove unused imports in various scripts for cleaner code
  ([`efbda3e`](https://github.com/domoskanonos/quisy-tts/commit/efbda3e7be7489cac02b4370d9299f7fa93cd96e))

- Reorganize API route registration to prevent shadowing of static paths and add tests for reserved
  keywords handling
  ([`1178c89`](https://github.com/domoskanonos/quisy-tts/commit/1178c89fc8de88df982c0a7a50b7f4c51a6152d1))

- Replace grep-based search with a portable Python script and add VSCode workspace configuration
  ([`d94c5f9`](https://github.com/domoskanonos/quisy-tts/commit/d94c5f9ea2d04c01a3267737e27ce61359dbc273))

- Standardize API port to 8045, introduce Pydantic-based configuration, and enhance development with
  a frontend proxy and Uvicorn CLI.
  ([`77a7e17`](https://github.com/domoskanonos/quisy-tts/commit/77a7e17607f89c8ea8fd5dde410d3a54e636817a))

- Update .gitignore, refactor styles.scss to use Sass modules, and modify benchmark script for async
  execution
  ([`7c97ec6`](https://github.com/domoskanonos/quisy-tts/commit/7c97ec6ca6e019b8be3e550670604c84c03e9141))

- Update Pyright configuration, enhance DummyEngine for audio generation, and remove obsolete
  verify_modes test
  ([`dd2b756`](https://github.com/domoskanonos/quisy-tts/commit/dd2b75689cab02e126539c5dc1d148cd684d18d6))

- **cache**: Cleanup job to remove cache files older than X days; add script
  ([`58d4450`](https://github.com/domoskanonos/quisy-tts/commit/58d44503c0ae261652e2f468deb0bff115c7ab6f))

- **cache**: Stable SHA256 cache key including speaker and params
  ([`5b9a40d`](https://github.com/domoskanonos/quisy-tts/commit/5b9a40df0e5225ce366a658f00b22b956e31ae20))

- **demo**: Add demo script; log streaming chunk/cache events
  ([`480cd5d`](https://github.com/domoskanonos/quisy-tts/commit/480cd5dd05cbb777c5630319f365d1f832b05b3d))

- **frontend**: Add progress bar for reference-generation; server: set no-cache headers for audio
  responses
  ([`97d2856`](https://github.com/domoskanonos/quisy-tts/commit/97d2856a8fe6d716685c3851adff7b202ad5a4b7))

- **frontend**: Use Google Roboto (preconnect + stylesheet); a11y: add roles/aria to layout;
  reduced-motion support
  ([`3c8875d`](https://github.com/domoskanonos/quisy-tts/commit/3c8875dfb7ea166d145e5f4be287b7f57a618f93))

### Testing

- **playwright**: Use correct base URL /ui for dev server and tests
  ([`c2fbdcf`](https://github.com/domoskanonos/quisy-tts/commit/c2fbdcff0d5f1633c490ce293eb705b9cfba4f7c))

- **ui**: Add screenshots and axe scans; stabilize playwright server url to /ui
  ([`9e1c56e`](https://github.com/domoskanonos/quisy-tts/commit/9e1c56e075c70bb250a07d0ab12aea617e76e1e0))


## v0.14.0 (2026-03-24)

### Features

- Add pytest configuration to mock `qwen_tts` module and system dependencies like `torch.cuda` and
  `sox` for testing.
  ([`9fd4f77`](https://github.com/domoskanonos/quisy-tts/commit/9fd4f77eea79b4dbba5ee9d847af408d723d343b))

- Add Qwen3-TTS engine implementation, core interfaces for TTS, caching, and cleanup, and audio
  processing utilities.
  ([`ff51894`](https://github.com/domoskanonos/quisy-tts/commit/ff51894be2534d1ed3fdef3338017f680ff569ad))

- Implement Qwen3-TTS engine with asynchronous model loading and audio post-processing utilities.
  ([`3dafec2`](https://github.com/domoskanonos/quisy-tts/commit/3dafec23fc6d48cc5d1a029362349157de782cd0))

- Implement Qwen3-TTS engine with custom voice API routes, update project configuration, and add VS
  Code settings.
  ([`26e7e9d`](https://github.com/domoskanonos/quisy-tts/commit/26e7e9d38b471cae3b362868c6e43923cdb0dbb7))

- Implement TTS service with caching, text splitting, and Qwen engine integration, alongside new
  core interfaces and concurrency tests.
  ([`88541dd`](https://github.com/domoskanonos/quisy-tts/commit/88541dd397246a0d49323b835ea5dd54cb235efc))


## v0.13.0 (2026-03-24)

### Features

- Introduce a shared SCSS module for forwarding styles and enable backend host/port configuration
  via `.env` file.
  ([`c688536`](https://github.com/domoskanonos/quisy-tts/commit/c6885364c9ff39ae886ebbfcb2887e109f81971d))


## v0.12.0 (2026-03-24)


## v0.11.0 (2026-03-24)

### Bug Fixes

- **defaults**: Correct language tags for English default voices
  ([`4ceff78`](https://github.com/domoskanonos/quisy-tts/commit/4ceff785e2d86b89ec1798651c73aad7cef5dffc))

- **frontend**: Migrate deprecated Sass @import to @use for shared styles
  ([`027b72f`](https://github.com/domoskanonos/quisy-tts/commit/027b72f0c0c97a20e9e485a01148e4d3edb9ad3a))

- **voices**: Normalize languages on migration using resolve_language
  ([`6dd20a5`](https://github.com/domoskanonos/quisy-tts/commit/6dd20a508e77c858feaf2e02c05cdf4bf32abb65))

### Features

- Implement core TTS generation service with language-aware text splitting, caching, and Qwen engine
  integration.
  ([`121e3c3`](https://github.com/domoskanonos/quisy-tts/commit/121e3c3c7eae79d04de5adba261067e6a3aa8b30))

### Refactoring

- **sass**: Convert _shared.scss to Sass module with variables/mixins and CSS exports
  ([`26ef07a`](https://github.com/domoskanonos/quisy-tts/commit/26ef07a764b9026b3897f330c4e80e486fa5754b))

- **sass**: Enforce local inclusion of shared mixins in component styles (no global fallbacks)
  ([`4f64afa`](https://github.com/domoskanonos/quisy-tts/commit/4f64afa8db8e22a08e344b72df26b731d7a8c221))

- **sass**: Split shared variables and mixins into separate files and import from _shared
  ([`be8e443`](https://github.com/domoskanonos/quisy-tts/commit/be8e443828d525bbaa6b2089351d7846bb345cca))

### Testing

- **frontend**: Add component specs for Synthesis and Voices flows
  ([`bd3299a`](https://github.com/domoskanonos/quisy-tts/commit/bd3299aa324b169096db5dc6d408625233341e42))

- **frontend**: Extend VoiceGenerationService specs (generate & upload, ensure-by-id poll)
  ([`d20d61e`](https://github.com/domoskanonos/quisy-tts/commit/d20d61ebb4b380452b1b2ea5070a35348a924e6f))


## v0.10.0 (2026-03-24)

### Chores

- **frontend**: Small UX improvements — disable play only for other generating items, show toasts
  ([`1ce1795`](https://github.com/domoskanonos/quisy-tts/commit/1ce17958e1c4ee5bbcfa2d02682dbeaa9b65cc06))

### Features

- **frontend**: Add polling helper and fallback ensure-by-id; improve generation playback handling
  and toasts
  ([`de9b58e`](https://github.com/domoskanonos/quisy-tts/commit/de9b58ed95d7a116c0c5b73b152fa84bbc895fa0))

- **frontend**: Improve UX — toasts and unified background generation; play uploaded audio after
  generation
  ([`92e33ee`](https://github.com/domoskanonos/quisy-tts/commit/92e33ee2df2034a7948e81cf57113cdc68ffd102))

### Testing

- **frontend**: Add basic spec for VoiceGenerationService
  ([`479b114`](https://github.com/domoskanonos/quisy-tts/commit/479b1146c08cf3b003dcc246e3099417cae75e0e))


## v0.9.0 (2026-03-23)

### Features

- Add initial `quisy-tts.db` database file.
  ([`13ba438`](https://github.com/domoskanonos/quisy-tts/commit/13ba438ecce2288dcbe13924699a4c11436a98c2))

### Refactoring

- **frontend**: Unify voice generation logic via VoiceGenerationService and reuse in
  Synthesis/Voices pages
  ([`a091104`](https://github.com/domoskanonos/quisy-tts/commit/a0911042e65d745db62ffc43379a1583499f5b58))


## v0.8.0 (2026-03-21)

### Features

- Add PowerShell scripts for local backend and frontend startup with dynamic proxy configuration and
  update project version.
  ([`afb9c3d`](https://github.com/domoskanonos/quisy-tts/commit/afb9c3d7b5c024c1823a8ae707f7456314534f83))


## v0.7.0 (2026-03-20)


## v0.6.1 (2026-03-20)

### Features

- Bump project version to 0.6.0 and move torch/torchaudio to an optional `gpu` extra.
  ([`768f5d6`](https://github.com/domoskanonos/quisy-tts/commit/768f5d6f6ea3953a506d1a6e4caa0c49e0f12390))


## v0.6.0 (2026-03-20)

### Bug Fixes

- Copy voices
  ([`3cdbd55`](https://github.com/domoskanonos/quisy-tts/commit/3cdbd550040758831e00a7573670b6275601073a))

### Build System

- Remove copying `voices/` directory from Dockerfile.
  ([`19808c2`](https://github.com/domoskanonos/quisy-tts/commit/19808c2760badd5dee29389b97624ceacedb1b1e))

### Features

- Init new version
  ([`fa8d7c2`](https://github.com/domoskanonos/quisy-tts/commit/fa8d7c2e46a8e1c6720ffa80aa9129170e80affe))


## v0.5.0 (2026-03-20)

### Bug Fixes

- Fehler korrigiert
  ([`4475d96`](https://github.com/domoskanonos/quisy-tts/commit/4475d96d04e37166222b3c2ff1848f95733133f6))

- Fix formatter
  ([`b4addab`](https://github.com/domoskanonos/quisy-tts/commit/b4addab6879eed3a0cba1ead4ce7cc5176d8d2b9))

### Chores

- Add remaining local edits (scripts, api info, core interfaces, voice schema)
  ([`f62dd95`](https://github.com/domoskanonos/quisy-tts/commit/f62dd9556cab6d3249587fb3a8910b45887186b3))

### Features

- Add language-aware text splitting service using spaCy with regex fallback for TTS chunking.
  ([`0ffbcbd`](https://github.com/domoskanonos/quisy-tts/commit/0ffbcbd281dfefcfe29a49b2251d45a2a3fa0e92))

- Add Text-to-Speech synthesis and voice management functionality with dedicated frontend pages and
  backend services.
  ([`ab9802c`](https://github.com/domoskanonos/quisy-tts/commit/ab9802c0a946a6022e6b10d73ab4be614aec23d9))

- Frontend and backen will be startet now
  ([`ab2b981`](https://github.com/domoskanonos/quisy-tts/commit/ab2b981ada090933c93e1cfa12de8deafdfe1fa3))

- Implement custom voice mode with API endpoints for generation and streaming, and a new synthesis
  UI.
  ([`a96c37a`](https://github.com/domoskanonos/quisy-tts/commit/a96c37a03cb720b47296b9b1d458ba1031d1237b))

- Implement the Qwen3-TTS engine, establish core API structure, and add performance benchmarks.
  ([`77b0360`](https://github.com/domoskanonos/quisy-tts/commit/77b036086dadd608dc88c03388ed292114aad254))

- Initialize the Angular frontend application and FastAPI backend for voice management.
  ([`fa4569f`](https://github.com/domoskanonos/quisy-tts/commit/fa4569fb9aa0ddb358fcc39010abf96c33698c41))

### Testing

- Make benchmark tests async-safe and case-insensitive language check
  ([`96553ee`](https://github.com/domoskanonos/quisy-tts/commit/96553ee0cc41e65d3945a1ce03adf785421d60ec))


## v0.4.6 (2026-02-12)

### Bug Fixes

- Dockerfile verschlanken
  ([`6e25174`](https://github.com/domoskanonos/quisy-tts/commit/6e25174da22803f4a64357793d8fbf637435e821))


## v0.4.5 (2026-02-12)

### Bug Fixes

- Audio error
  ([`1a4adde`](https://github.com/domoskanonos/quisy-tts/commit/1a4adde19d7c8bff3be1c6187c0866ba513f12e0))


## v0.4.4 (2026-02-12)

### Bug Fixes

- Fix build
  ([`17db3c0`](https://github.com/domoskanonos/quisy-tts/commit/17db3c0ddc643821e0bcbc6b02ddf0149c3937cc))


## v0.4.3 (2026-02-12)

### Bug Fixes

- Merge branch 'main' of github.com:domoskanonos/quisy-tts
  ([`c31d729`](https://github.com/domoskanonos/quisy-tts/commit/c31d729911c02abcbae33cf8c04537849640b0cf))


## v0.4.2 (2026-02-12)

### Bug Fixes

- Fix build
  ([`2ac8081`](https://github.com/domoskanonos/quisy-tts/commit/2ac8081889f9e7a522084e5ab768af961e03deae))

- Modified
  ([`98b0f36`](https://github.com/domoskanonos/quisy-tts/commit/98b0f368ed82ac3ec4e8facd7cd3b73ed639d03e))

- Uv now avaliable
  ([`0236c60`](https://github.com/domoskanonos/quisy-tts/commit/0236c602c009b76ab695d0062fb4f5463dce1770))


## v0.4.1 (2026-02-11)

### Bug Fixes

- Corrected docker build
  ([`1edcda9`](https://github.com/domoskanonos/quisy-tts/commit/1edcda923122e49288b1277691e802a4620eefb6))

- Modified
  ([`838e358`](https://github.com/domoskanonos/quisy-tts/commit/838e358bcf03f0369c08be746e25beac65f021dd))


## v0.4.0 (2026-02-11)

### Bug Fixes

- Merge branch 'main' of github.com:domoskanonos/cosmo-tts
  ([`6ebed7d`](https://github.com/domoskanonos/quisy-tts/commit/6ebed7df1d7c3d8061dd8e5a8b74291078c29ef6))


## v0.3.0 (2026-02-11)

### Features

- Add readme to dockerhub
  ([`60a6c2a`](https://github.com/domoskanonos/quisy-tts/commit/60a6c2a84a53cfd03283f69371ce60fbc10b3f26))

- Modified reamde path
  ([`69544d2`](https://github.com/domoskanonos/quisy-tts/commit/69544d232b11997116bb8de55415c20f63fced9d))


## v0.2.0 (2026-02-11)

### Bug Fixes

- Corrected Dockerhub NAME
  ([`d87d30b`](https://github.com/domoskanonos/quisy-tts/commit/d87d30ba3552a52d8e98587b16cdc0c11d7bb44c))

### Features

- Merge branch 'main' of github.com:domoskanonos/cosmo-tts
  ([`db91223`](https://github.com/domoskanonos/quisy-tts/commit/db91223ba9933af8d6585b247f514b9d9eb71181))


## v0.1.0 (2026-02-11)

### Bug Fixes

- Corrected file errors
  ([`85824d4`](https://github.com/domoskanonos/quisy-tts/commit/85824d481b4f3a3ca0c2af17bab007ef0ee187a1))

- Fix tests
  ([`63ee4d8`](https://github.com/domoskanonos/quisy-tts/commit/63ee4d8a7ade8de99e172a8879c4a7ef00af7b72))

- Format code
  ([`64452f0`](https://github.com/domoskanonos/quisy-tts/commit/64452f03e89f25d531218514f4d364a7523ea2ba))

- Reduce docker size for pipeline
  ([`1aee7b6`](https://github.com/domoskanonos/quisy-tts/commit/1aee7b6bfb8ca11a1118ffce65467398ac82e59e))

### Documentation

- Update README with Docker usage and new granular API endpoints, remove `DEFAULT_MODEL_SIZE`
  references, and add `verify_output.txt` to .gitignore.
  ([`d6a919b`](https://github.com/domoskanonos/quisy-tts/commit/d6a919b6273ab323a18e572d1aac2a26f7fb7c2d))

### Features

- Add `ModelManager` for Qwen3-TTS model loading and caching, remove default model size from `.env`,
  and refine `.gitignore` for the models directory.
  ([`34db1ac`](https://github.com/domoskanonos/quisy-tts/commit/34db1acae99752bbb9cfc6011c58913b70b5d646))

- Add docker readme
  ([`adf958e`](https://github.com/domoskanonos/quisy-tts/commit/adf958e7b1f996aa9f398601d52e4bfdea9cb83b))

- Add Qwen3-TTS engine implementation with both Transformers and vLLM backends.
  ([`a4e0e63`](https://github.com/domoskanonos/quisy-tts/commit/a4e0e637a9b6acb1a765895f69f3a0708e9637c1))

- Establish core TTS generation services, API request schemas, and a comprehensive CI/CD pipeline.
  ([`a8685cb`](https://github.com/domoskanonos/quisy-tts/commit/a8685cbb8cf0ccf94558a723456c2807faf454d7))

- Implement initial FastAPI application with core TTS service, API routes, and language handling.
  ([`0b6f2c8`](https://github.com/domoskanonos/quisy-tts/commit/0b6f2c88b791d7d031ee6753b96b4a5ff081e8e9))

- Implement Qwen TTS engine, add comprehensive testing and benchmarking, and introduce model
  download scripts.
  ([`1f2a631`](https://github.com/domoskanonos/quisy-tts/commit/1f2a631f2f6bcb639bb2f7db0defc9730b107d93))

- Implement Qwen3-TTS engine with a new orchestration service and reference audio assets.
  ([`30a8240`](https://github.com/domoskanonos/quisy-tts/commit/30a8240c79db80cd11c382fbcc3c6780f0f8e0e9))

- Implement Qwen3-TTS engine with audio generation, saving, and streaming capabilities.
  ([`22966d9`](https://github.com/domoskanonos/quisy-tts/commit/22966d91e563998b3d8e867a615fb5a4465a8276))

- Implement Qwen3-TTS engine with both Transformers and vLLM backends, introducing a new TTS backend
  interface.
  ([`66cb9d9`](https://github.com/domoskanonos/quisy-tts/commit/66cb9d97bf98386b66241fa91c5023ce348e7063))

- Implement Qwen3-TTS engine with centralized project configuration and audio streaming
  capabilities.
  ([`2d39b8f`](https://github.com/domoskanonos/quisy-tts/commit/2d39b8f08dab903d636db7106e10c19b2fea9a7c))

- Implement Qwen3-TTS engine with centralized project configuration and request schemas.
  ([`87e6b0e`](https://github.com/domoskanonos/quisy-tts/commit/87e6b0ec47c3d14c9fd5ebfd1696706dd92b79a3))

- Implement Qwen3-TTS engine with streaming API, voice cloning, and add diagnostic/benchmark
  scripts.
  ([`1d1ac96`](https://github.com/domoskanonos/quisy-tts/commit/1d1ac96a5d218b3dd6bb81dc677b76f0b5638326))

- Implement Qwen3-TTS engine, project configuration, audio processing utilities, device validation,
  and a Docker publish workflow.
  ([`7854f61`](https://github.com/domoskanonos/quisy-tts/commit/7854f61810b8bdb76bbbe8529be59ad0af0c4314))

- Modify pipeline
  ([`ad12912`](https://github.com/domoskanonos/quisy-tts/commit/ad12912bec26c42562e39358150f6adb06c05b7f))

### Refactoring

- Configure local `mypy` pre-commit hook to use `uv run` and fix README formatting.
  ([`b6ae500`](https://github.com/domoskanonos/quisy-tts/commit/b6ae5000d4b19185e417a16bd47358ec302cdc48))


## v0.0.0 (2026-01-23)
