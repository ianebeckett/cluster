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

Assignment feasibility also requires Julia (tested with Julia 1.10.10) and the
local solver `julia_solvers/st-cut/newMaxFlow.jl`. Make `julia` available on `PATH`,
or set `JULIA` to its executable path:

```bash
export JULIA=/absolute/path/to/julia
```

The `julia_solvers/` directory is ignored by Git and must be supplied separately
in a fresh checkout. Set `JULIA_MAXFLOW_PATH` if `newMaxFlow.jl` lives elsewhere.
The bridge loads that file directly and uses only Julia's standard libraries;
the other experiment dependencies in `julia_solvers/functions.jl` are unnecessary.

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

`find_eligible_centers` computes the allowed center indices for each point within
the trial radius, preserving point order. `find_feasible_assignment` uses these
lists to build a network and calls `newMaxFlow.maxflow` through `julia_flow.py`.
An assignment is feasible only when every point can be assigned and every
center's load is between the supplied minimum and capacity. Julia's flow value
must equal the number of points; the assignment is extracted from its edge flows.

The bridge starts Julia on the first nontrivial flow request and reuses that
process until Python exits or `julia_flow.close()` is called. Missing Julia,
missing solver source, and solver failures raise `RuntimeError`, rather than
returning `None` for an infeasible assignment.

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
