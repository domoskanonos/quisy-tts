# CHANGELOG


## v0.3.0 (2026-02-11)

### Features

- Add readme to dockerhub
  ([`60a6c2a`](https://github.com/domoskanonos/quisy-tts/commit/60a6c2a84a53cfd03283f69371ce60fbc10b3f26))


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
