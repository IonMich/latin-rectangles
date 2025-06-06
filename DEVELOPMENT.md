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
uv run latin-rectangles

# Or run directly with Python
uv run python -m latin_rectangles
```

## Project Structure
```
latin-rectangles/
├── src/
│   └── latin_rectangles/
│       └── __init__.py          # Main module with entry point
├── .venv/                       # Virtual environment (created by uv)
├── .vscode/
│   └── settings.json           # VS Code settings for the project
├── pyproject.toml              # Project configuration
└── README.md
```
