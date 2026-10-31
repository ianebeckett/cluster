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

The demo keeps centers fixed at `[0]` and `[10]` and assigns points `[0]` and
`[1]`. With capacity two per center, the minimum radius is `1.0`. Requiring
exactly one point per center increases it to `9.0`. Zero capacity is infeasible.
`solve` searches for the minimum radius, reconstructs an assignment there, and
prints both the radius and the actual maximum assigned distance. Reconstruction
performs one additional assignment solve after the radius search.

`find_eligible_centers` computes the allowed center indices for each point within
the trial radius, preserving point order. `find_feasible_assignment` uses these
lists to build a network and calls `newMaxFlow.maxflow` through `julia_flow.py`.
An assignment is feasible only when every point can be assigned and every
center's load is between the supplied minimum and capacity. Julia's flow value
must equal the number of points; the assignment is extracted from its edge flows.

`find_min_radius(points, centers, U=..., L=0)` finds the
smallest feasible radius for the supplied centers. It computes each point-center
distance once, sorts the distinct distances, and uses `bisect_left` with an
assignment feasibility check. No radius tolerance is needed. It returns `None`
when the load constraints cannot be satisfied, or `0.0` for empty points when
the load bounds allow them. A custom `distance` must return finite, nonnegative
values; invalid bounds or distances raise an error.

The bridge starts Julia on the first nontrivial flow request and reuses that
process until Python exits or `julia_flow.close()` is called. Missing Julia,
missing solver source, and solver failures raise `RuntimeError`, rather than
returning `None` for an infeasible assignment.

## Call graphs

Pyan-generated diagrams for `main.py` are available with
[function names](docs/callgraphs/main-names.svg) or
[full function signatures](docs/callgraphs/main-signatures.svg).
PNG copies and editable Graphviz DOT files are in the same directory.

To regenerate them, install Pyan and ensure Graphviz's `dot` command is on PATH:

```bash
uv tool install pyan3==2.9.0
uv run python scripts/generate_callgraphs.py
```

The script preserves Pyan's nodes and edges and adds signature labels parsed
from the source. The dashed edge denotes the `bisect_left` key callback.
These are static uses graphs limited to `main.py`; imported functions such as
`julia_flow.maximum_flow` and Julia's solver internals are outside their scope.

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
