# CHANGELOG


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
