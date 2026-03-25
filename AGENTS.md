AGENTS

This file is written for agentic coding tools working in this repository. It collects the commands, CI expectations and a compact, opinionated code-style guide so automated agents make consistent, safe changes.

- **Repo root references**: `pyproject.toml`, `pytest.ini`, `README.md`, `.github/workflows/pipeline.yml`, `.editorconfig`

1) Build / Lint / Test (commands)

- Install project and dev deps (uses `uv` as project launcher):
  - `uv sync` (installs runtime deps defined in `pyproject.toml`)
  - `uv sync --dev` (installs dev dependencies)
- Run full test suite:
  - `uv run pytest`
- Run a single test file or test case (recommended for fast iteration):
  - Single test function in a file: `uv run pytest tests/test_api.py::test_some_behavior`
  - Single test with substring match: `uv run pytest -k "substring"`
  - Run an entire test file: `uv run pytest tests/test_api.py`
  - Use `-q` (quiet) or `-k` (expression) to filter tests when useful.
- Linting / formatting / type checks (CI mirrors these):
  - Lint: `uv run ruff check .`
  - Auto-format: `uv run ruff format .` or `uv run ruff format <path>` for a subset
  - Type checks: `uv run mypy .`
- Pre-commit hooks (local):
  - `uv run pre-commit install --hook-type commit-msg --hook-type pre-commit`

Notes:
- CI uses `uv` and runs the above sequence (see `.github/workflows/pipeline.yml`). Use the same commands locally to reproduce CI.
- `pytest.ini` sets `pythonpath = src` and `testpaths = tests`, so run tests from repo root.

2) How to run/debug tests interactively

- To run tests with logging visible (mirrors CI): `uv run pytest -o log_cli=true -o log_cli_level=INFO`
- To run pytest in an isolated environment (no uv): `python -m pytest tests/test_api.py::test_name` (only if you have the environment already populated). Prefer `uv run` for consistent dependency resolution.

3) Static analysis configuration (what automated agents must respect)

- Ruff (linter/formatter): configuration is in `pyproject.toml` under `[tool.ruff]`:
  - `line-length = 120`
  - `indent-width = 4`
  - `target-version = "py312"`
  - Lint selection: `E`, `F`, `W` (errors, pyflakes, warnings)
  - `E501` (line-length) is ignored because line-length handled above
  - Ruff is configured as an auto-fixer where applicable (`fixable = ["ALL"]`)

- Mypy: configuration is in `pyproject.toml` under `[tool.mypy]`.
  - `python_version = "3.12"`
  - `check_untyped_defs = true` — prefer typed implementations
  - `ignore_missing_imports = true` in this repository (third-party stubs are not required)

4) Styling and code conventions (agents must follow)

- File layout and imports:
  - Keep top-level package code under `src/` (project already uses `src` layout)
  - Import ordering: standard library, third-party, local (one blank line between groups).
  - Avoid wildcard imports (`from module import *`). Prefer explicit imports.

- Formatting:
  - Use `ruff format` for automated formatting. If an agent modifies files, run `uv run ruff format <files>` before committing.
  - Line length: 120 characters. Prefer breaking long expressions early rather than violating the limit.
  - Indentation: 4 spaces (see `.editorconfig` and `pyproject.toml`).

- Types and typing policy:
  - Type hints are encouraged for public functions and complex internal functions.
  - `check_untyped_defs = true` means functions that are typed should have typed internals checked — prefer adding annotations rather than disabling checks.
  - Do not aggressively annotate trivial one-liners where it harms readability; use best judgment.

- Naming conventions:
  - Modules and functions: `snake_case`
  - Classes and exceptions: `PascalCase` (CamelCase)
  - Constants: `UPPER_SNAKE_CASE`
  - Private/protected names: single leading underscore (e.g. `_helper`)

- Async / concurrency:
  - Use `async def` for coroutine functions that perform I/O or await behaviour.
  - Tests that use asyncio should use `pytest-asyncio` fixtures (already in dev deps).
  - Avoid blocking calls in async code. If you must run CPU-bound code, use `asyncio.to_thread` / `run_in_executor`.

- Error handling and logging:
  - Do not use bare `except:`. Catch specific exceptions (e.g. `except ValueError:`) or `except Exception:` when intentionally catching broad errors.
  - Log the error and re-raise when appropriate, or wrap low-level exceptions into clear, domain-specific exceptions.
  - Prefer explicit failure over silent swallowing; tests expect deterministic failures.

- Tests:
  - Tests live in `tests/` and follow `test_*.py` file and `test_*` function naming conventions (see `pytest.ini`).
  - Unit tests: keep them small, deterministic, and fast. Use pytest markers (`@pytest.mark.asyncio`, `@pytest.mark.parametrize`) where appropriate.
  - For failing tests, include minimal repro data and assert messages when helpful.

5) Git / commits / PR guidance for agents

- Agents should not push directly to `main`. Create topic branches and a PR with a clear title and brief description.
- Follow the repo CI: changes must pass `ruff`, `mypy`, and `pytest` before merging.
- If an automated change runs formatters or fixers, include the formatting changes in the same PR and mention it in the PR body.

6) Special files / project-specific notes

- `pyproject.toml` contains the authoritative config for ruff and mypy. Respect those settings.
- `pytest.ini` ensures `src/` is on `PYTHONPATH` for tests. Do not modify test discovery without updating `pytest.ini`.
- `.editorconfig` sets basic editor behaviour (tabs/spaces, eol). Prefer repository defaults.

7) Cursor / Copilot rules

- No repository-level Cursor rules found in `.cursor/rules/` or `.cursorrules`.
- No `/.github/copilot-instructions.md` found. (There are references to copilot in `frontend/node_modules` only — ignore vendor files.)

8) Safety and secrets

- Do not commit secrets or `.env` files with credentials. The repo contains a `.env.example` for guidance.
- If an agent needs to run anything that requires secrets (DockerHub, GitHub tokens), prompt for the secret or ask the human operator.

9) If you're unsure

- Prefer conservative changes: smaller commits, clear tests, and follow established patterns in `src/`.
- If a change touches runtime behaviour (model loading, device selection `DEVICE`), include an integration test or manual verification steps in the PR description.

Appendix: Quick command cheatsheet

- `uv sync --dev` — install dev deps
- `uv run ruff check .` — lint
- `uv run ruff format .` — format
- `uv run mypy .` — type checks
- `uv run pytest` — run all tests
- `uv run pytest tests/test_api.py::test_name` — run single test

End of AGENTS
