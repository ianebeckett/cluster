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
`main` prints the minimum radius, the assignment, and the actual maximum
assigned distance for each example.

`solve` returns a frozen `ClusteringResult` with `radius` and `assignment` fields,
or `None` if the load constraints are infeasible. The assignment is a tuple of
center indices in point order. It does not print or modify its inputs, so it can
be called directly by tests and benchmarks:

```python
from main import solve

result = solve([[0], [1]], [[0], [10]], lower_bound=1, upper_bound=1)
if result is not None:
    print(result.radius)      # 9.0
    print(result.assignment)  # (0, 1)
```

`find_eligible_centers` computes the allowed center indices for each point within
the trial radius, preserving point order. `find_feasible_assignment` uses these
lists to build a network and calls `newMaxFlow.maxflow` through `julia_flow.py`.
An assignment is feasible only when every point can be assigned and every
center's load is between the supplied minimum and capacity. Julia's flow value
must equal the number of points; the assignment is extracted from its edge flows.

The fixed-center baseline follows Section 2.1 and the per-tuple procedure in
Algorithm 1, steps 2–3, of [Ding (2020)](https://doi.org/10.1016/j.tcs.2020.07.022):

1. Compute each point-center distance once and sort the distinct candidate radii.
2. Use `bisect_left` to search feasibility, building a point-level flow network
   at each trial radius with the original lower and upper load bounds.
3. Retain the smallest feasible radius and its integral assignment. Return that
   result without repeating the winning flow computation.

The search keeps only the best assignment in local state, rather than caching
every trial. This baseline uses supplied centers; it does not implement the
paper's center selection, outer center-tuple enumeration, or eligibility grouping.

`find_min_radius(points, centers, upper_bound=..., lower_bound=0)` remains a
radius-only interface to `solve`. No radius tolerance is needed. Empty points
have radius `0.0` and an empty assignment when the load bounds allow them.
A custom `distance` must return finite, nonnegative values; invalid bounds or
distances raise an error. Radius optimality is with respect to the computed
distances and supplied centers.

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
