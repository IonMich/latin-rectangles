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

## One-Time Trusted Publishing Setup

PyPI trusted publishing must be configured once before the release workflow can
publish:

- PyPI project: `latin-rectangles`
- GitHub owner: `IonMich`
- GitHub repository: `latin-rectangles`
- Workflow filename: `release.yml`
- GitHub environment: `pypi`

Create the matching GitHub repository environment named `pypi` under repository
settings. Add approval rules there if releases should require manual approval
before PyPI upload.
