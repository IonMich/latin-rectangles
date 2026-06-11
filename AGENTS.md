# Repository Instructions

- Run Python scripts with `uv run ...` instead of `python ...`.
- Install Python project dependencies with `uv add <dependency>` instead of
  `pip` or manual `pyproject.toml` edits.

## Release Process

- Publish releases through GitHub Actions trusted publishing, not from a local
  machine.
- Before releasing, merge the version bump and changelog/docs changes to
  `main`.
- Tag the merged `main` commit with the exact project version:

  ```console
  git switch main
  git pull --ff-only
  git tag -a vX.Y.Z -m vX.Y.Z
  git push origin vX.Y.Z
  ```

- The `.github/workflows/release.yml` workflow verifies that the pushed tag
  matches `pyproject.toml`, runs lint/type/tests, builds wheel and sdist,
  smoke-tests both artifacts, and publishes to PyPI.
- Do not use local PyPI tokens for normal releases. Local publishing is only an
  emergency fallback after the GitHub release path is unavailable or broken.

## Trusted Publishing Setup

PyPI trusted publishing is configured for this project:

- PyPI project: `latin-rectangles`
- GitHub owner: `IonMich`
- GitHub repository: `latin-rectangles`
- Workflow filename: `release.yml`
- GitHub environment: `pypi`

The matching GitHub repository environment named `pypi` exists. It does not
need GitHub environment secrets or variables for PyPI publishing. Add approval
rules there only if releases should require manual approval before PyPI upload.
