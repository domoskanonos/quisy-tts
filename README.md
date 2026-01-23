# Python Project Starter

[![Pipeline](https://github.com/domoskanonos/python-starter/actions/workflows/pipeline.yml/badge.svg)](https://github.com/domoskanonos/python-starter/actions/workflows/pipeline.yml)
[![PyPI version](https://img.shields.io/pypi/v/domoskanonos-python-starter.svg)](https://pypi.org/project/domoskanonos-python-starter/)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

A modern, high-performance Python project template powered by [uv](https://github.com/astral-sh/uv). Designed for developers who want a clean, fast, and automated workflow.

---

## 🛠 Prerequisites

This project requires **uv**. If you don't have it installed, run:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 🚀 Quick Start

Get up and running in seconds:

```bash
# Clone the repository
git clone https://github.com/domoskanonos/python-starter.git
cd python-starter

# Install dependencies and create virtualenv automatically
uv sync

# Install pre-commit hooks (CRITICAL for development)
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

# Run the application
uv run python src/project/main.py
```

## ⚙️ Configuration

This project uses **Pydantic Settings** for configuration. You can use a `.env` file to override default values:

```bash
# .env
PROJECT_NAME="My Custom Project"
LOG_LEVEL="DEBUG"
```

## 🛠 Development Workflow

### 📝 Commit Messages (Conventional Commits)
This project enforces [Conventional Commits](https://www.conventionalcommits.org/). Your commit messages **must** start with one of the following prefixes:
- `feat:` (New feature, triggers a **minor** release)
- `fix:` (Bug fix, triggers a **patch** release)
- `docs:`, `style:`, `refactor:`, `test:`, `chore:` (No release triggered)

### ✅ Local Checks
Before pushing, run all checks locally to ensure the CI passes:
```bash
# Run all pre-commit hooks (Linting, Formatting, Type Checking)
uv run pre-commit run --all-files

# Run tests
uv run pytest
```

### 🔍 Tools used
- **Type Checking**: `uv run mypy .`
- **Linting & Formatting**: `uv run ruff check .` and `uv run ruff format .`

---

## 📦 Features

- **[uv](https://github.com/astral-sh/uv)**: Ultra-fast Python package and environment manager.
- **[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)**: Robust configuration management.
- **[Mypy](https://mypy-lang.org/)**: Static type checking.
- **[Ruff](https://github.com/astral-sh/ruff)**: All-in-one linter and formatter.
- **[Docker](https://www.docker.com/)**: Multi-stage Dockerfile for optimized images.
- **[Semantic Release](https://python-semantic-release.readthedocs.io/)**: Automated versioning and PyPI publishing via GitHub Actions.

---

## 🚢 Automated Releases

Releases are fully automated via GitHub Actions in the [Pipeline](.github/workflows/pipeline.yml).

1. **Push to main**: When you push a `feat:` or `fix:` commit to the `main` branch.
2. **Auto-Versioning**: The pipeline calculates the new version using `python-semantic-release`.
3. **Auto-Tagging**: A new Git tag and a `CHANGELOG.md` are created.
4. **Auto-Publish**: The package is built and published to PyPI automatically.

> **Note**: Ensure you have configured the [PyPI Trusted Publisher](https://pypi.org/manage/account/publishing/) for the workflow.

---

## 🤖 Dependency Management

Dependencies are managed via `uv`.
```bash
uv add <package-name>
uv add --dev <dev-package-name>
```

**Renovate** is active and will automatically create PRs for updates. Non-major updates are merged automatically if CI passes.

### Manuelle Updates
```bash
# Update all packages in uv.lock
uv lock --upgrade

# Sync local environment
uv sync
```

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.


## 🛠 Development Workflow

### 📝 Commit Messages (Conventional Commits)
This project enforces [Conventional Commits](https://www.conventionalcommits.org/). Your commit messages **must** start with one of the following prefixes:
- `feat:` (New feature, triggers a **minor** release)
- `fix:` (Bug fix, triggers a **patch** release)
- `docs:`, `style:`, `refactor:`, `test:`, `chore:` (No release triggered)

**Example:** `feat: add pydantic settings support`

### ✅ Local Checks
Before pushing, run all checks locally to ensure the CI passes:
```bash
# Run all pre-commit hooks (Linting, Formatting, Type Checking)
uv run pre-commit run --all-files

# Run tests
uv run pytest
```

### 🔍 Tools used
- **Type Checking**: `uv run mypy .`
- **Linting & Formatting**: `uv run ruff check .` and `uv run ruff format .`

---

## 📦 Features

- **[uv](https://github.com/astral-sh/uv)**: Ultra-fast Python package and environment manager.
- **[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)**: Robust configuration management.
- **[Mypy](https://mypy-lang.org/)**: Static type checking.
- **[Ruff](https://github.com/astral-sh/ruff)**: All-in-one linter and formatter.
- **[Docker](https://www.docker.com/)**: Multi-stage Dockerfile for optimized images.
- **[Semantic Release](https://python-semantic-release.readthedocs.io/)**: Automated versioning and PyPI publishing.

---

## 🚢 Automated Releases

Releases are fully automated via GitHub Actions and `python-semantic-release`.

1. **Push to main**: When you push a `feat:` or `fix:` commit to the `main` branch.
2. **Auto-Versioning**: The `release.yml` workflow calculates the new version.
3. **Auto-Tagging**: A new Git tag (e.g., `v0.2.0`) and a `CHANGELOG.md` are created.
4. **Auto-Publish**: The package is built and published to PyPI automatically.

> **Note**: Ensure you have configured the [PyPI Trusted Publisher](https://pypi.org/manage/account/publishing/) for the `release.yml` workflow.

---

## 🤖 Dependency Management

Dependencies are managed via `uv`.
```bash
uv add <package-name>
uv add --dev <dev-package-name>
```

**Renovate** is active and will automatically create PRs for updates. Non-major updates are merged automatically if CI passes.


A modern, high-performance Python project template powered by [uv](https://github.com/astral-sh/uv). Designed for developers who want a clean, fast, and automated workflow.

---

## 🛠 Prerequisites

This project requires **uv**. If you don't have it installed, run:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 🚀 Quick Start

Get up and running in seconds:

```bash
# Clone the repository
git clone https://github.com/domoskanonos/python-starter.git
cd python-starter

# Install dependencies and create virtualenv automatically
uv sync

# Run the application
uv run python src/project/main.py
```

## ⚙️ Configuration

This project uses **Pydantic Settings** for configuration. You can use a `.env` file to override default values:

```bash
# .env
PROJECT_NAME="My Custom Project"
LOG_LEVEL="DEBUG"
```

## 🛠 Development Workflow

### Running Tests
We use `pytest` for testing.
```bash
uv run pytest
```

### Type Checking
Powered by `mypy` for static type analysis.
```bash
uv run mypy .
```

### Linting & Formatting
Powered by `ruff` for extreme speed.
```bash
# Check for linting issues
uv run ruff check .

# Format code
uv run ruff format .
```

### Pre-commit Hooks
Ensure code quality before every commit:
```bash
uv run pre-commit install
```

---

## 📦 Features

- **[uv](https://github.com/astral-sh/uv)**: Ultra-fast Python package and environment manager.
- **[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)**: Robust configuration management via environment variables.
- **[Mypy](https://mypy-lang.org/)**: Static type checking for better code quality.
- **[Ruff](https://github.com/astral-sh/ruff)**: All-in-one linter and formatter.
- **[Docker](https://www.docker.com/)**: Multi-stage Dockerfile for optimized container images.
- **GitHub Actions**:
  - **CI**: Automated testing, linting, and Docker build on every push.
  - **CD**: Automated publishing to PyPI on version tags.
- **Renovate**: Automated dependency updates with auto-merge support.

---

## 🚢 Deployment (PyPI)

This project is configured for **Trusted Publishing**.

1. **Update Version**: Change `version` in `pyproject.toml`.
2. **Tag & Push**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. **Auto-Deploy**: The `cd.yml` workflow will automatically build and publish to PyPI.

---

## 🤖 Dependency Management

Dependencies are managed via `uv`. To add a new package:
```bash
uv add <package-name>
uv add --dev <dev-package-name>
```
3.  **Secret hinzufügen**: Gehe in deinem Repository zu `Settings -> Secrets and variables -> Actions` und erstelle ein Secret namens `RENOVATE_TOKEN` mit dem Wert deines Tokens.

### Manuelle Updates
Du kannst die Abhängigkeiten auch jederzeit manuell mit `uv` aktualisieren:

```bash
# Alle Pakete in der uv.lock auf die neueste kompatible Version heben
uv lock --upgrade

# Ein spezifisches Paket aktualisieren
uv lock --upgrade-package ruff

# Die lokale Umgebung (.venv) mit der uv.lock synchronisieren
uv sync
```

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.
