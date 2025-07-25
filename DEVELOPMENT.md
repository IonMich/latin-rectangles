# Development commands

## Setup

```bash
# Install the project in development mode
uv sync --dev

# Activate the virtual environment
source .venv/bin/activate  # or use `uv run` prefix for commands
```

## Linting and Formatting

```bash
# Check code style and lint
uv run ruff check

# Fix auto-fixable issues
uv run ruff check --fix

# Format code
uv run ruff format

# Check formatting without making changes
uv run ruff format --check
```

## Running the application

```bash
# Run the main script
uv run latin-rectangles --n 42
```
