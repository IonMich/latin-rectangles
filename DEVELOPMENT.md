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

## Releasing

Releases are published by GitHub Actions from version tags. Do not publish to
PyPI from a local machine during the normal release path.

### Trusted Publishing Setup

PyPI trusted publishing is configured for this project:

- PyPI project: `latin-rectangles`
- GitHub owner: `IonMich`
- GitHub repository: `latin-rectangles`
- Workflow filename: `release.yml`
- GitHub environment: `pypi`

The GitHub repository environment named `pypi` does not need environment
secrets or variables for PyPI publishing. Add required reviewers there only if
PyPI deployment should require manual approval.

### Release Steps

1. Merge the release/version change to `main`.
2. Tag the merged commit with the exact version in `pyproject.toml`.

```bash
git switch main
git pull --ff-only
git tag -a vX.Y.Z -m vX.Y.Z
git push origin vX.Y.Z
```

The release workflow verifies that `vX.Y.Z` matches `pyproject.toml`, runs
linting, formatting checks, mypy, tests, builds the wheel and sdist, smoke-tests
both artifacts, and publishes to PyPI via trusted publishing.
