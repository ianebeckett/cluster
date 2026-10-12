# Cluster

## Install

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run
from the project root:

```bash
uv sync
```

The project uses Python 3.14, selected by `.python-version`. uv manages `.venv`
and installs the project and its development tools: pytest, pytest-cov, Ruff,
and basedpyright.
Virtual environment activation is optional when using `uv run`.

## Test

```bash
uv run pytest
uv run ruff check .
uv run basedpyright
```

To run a specific test file, pass its path from the project root:

```bash
uv run pytest test/test_find_feasible_assignment.py
```

A coverage report is generated at `build/coverage/html/index.html`.

Open the HTML report in a browser, or use your system's command from the project
root:

```bash
open build/coverage/html/index.html      # macOS
xdg-open build/coverage/html/index.html  # Linux
```

To skip coverage for a particular run, use `uv run pytest --no-cov`.

## Run

```bash
uv run python main.py
```

## Dependencies

Add runtime dependencies with `uv add PACKAGE` and development dependencies with
`uv add --dev PACKAGE`. Remove dependencies with `uv remove PACKAGE` (or
`uv remove --dev PACKAGE` for development tools).

After editing dependencies in `pyproject.toml` manually, run `uv sync` to update
the lockfile and environment. Keep `pyproject.toml`, `uv.lock`, and `.python-version`
in version control; `.venv` and tool caches are local generated files.

To deliberately upgrade a dependency within its declared version constraints:

```bash
uv sync --upgrade-package PACKAGE
```
