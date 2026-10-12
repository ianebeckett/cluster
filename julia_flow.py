"""Call the local Julia newMaxFlow solver through a reusable subprocess."""

import atexit
import os
import subprocess
from pathlib import Path
from threading import Lock
from typing import cast

# Each request is a node/edge count followed by integer (from, to, capacity)
# rows. Each response is the flow value followed by the flow on each input edge.
# newMaxFlow requires source = 1 and sink = node_count.
_BRIDGE = """
using SparseArrays
include(ARGS[1])
for header in eachline(stdin)
    node_count, edge_count = parse.(Int, split(header))
    rows = Int[]
    cols = Int[]
    capacities = Int[]
    for _ in 1:edge_count
        u, v, capacity = parse.(Int, split(readline(stdin)))
        push!(rows, u)
        push!(cols, v)
        push!(capacities, capacity)
    end
    network = sparse(rows, cols, capacities, node_count, node_count)
    result = newMaxFlow.maxflow(network)
    values = [result.flowvalue; [result.F[u, v] for (u, v) in zip(rows, cols)]]
    println(join(values, " "))
    flush(stdout)
end
"""

_process: subprocess.Popen[str] | None = None
_lock = Lock()


def _stop_worker() -> None:
    global _process
    if _process is not None:
        if _process.stdin is not None:
            try:
                _process.stdin.close()
            except BrokenPipeError:
                pass  # The worker may have exited before consuming a request.
        try:
            _ = _process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _process.kill()
            _ = _process.wait()
        if _process.stdout is not None:
            _process.stdout.close()
        _process = None


def close() -> None:
    """Stop the worker; a later maximum_flow call starts a new one."""
    with _lock:
        _stop_worker()


_ = atexit.register(close)


def maximum_flow(
    node_count: int, edges: list[tuple[int, int, int]]
) -> tuple[int, list[int]]:
    """Return Julia's flow value and edge flows; source is 1, sink is node_count.

    Calls are serialized and reuse one Julia process to avoid repeated startup
    and compilation. Runtime failures raise RuntimeError, not infeasibility.
    """
    global _process
    with _lock:
        if _process is None or _process.poll() is not None:
            _stop_worker()
            solver = Path(
                os.environ.get(
                    "JULIA_MAXFLOW_PATH",
                    str(Path(__file__).parent / "julia_solvers/st-cut/newMaxFlow.jl"),
                )
            )
            if not solver.is_file():
                raise RuntimeError(
                    f"Julia solver not found: {solver}. Set JULIA_MAXFLOW_PATH to newMaxFlow.jl."
                )
            try:
                _process = subprocess.Popen(
                    [
                        os.environ.get("JULIA", "julia"),
                        "--startup-file=no",
                        "--history-file=no",
                        "-e",
                        _BRIDGE,
                        str(solver.resolve()),
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                )
            except OSError as exc:
                raise RuntimeError(
                    "Could not start Julia. Put Julia on PATH or set JULIA to its executable path."
                ) from exc

        assert _process.stdin is not None and _process.stdout is not None
        request = f"{node_count} {len(edges)}\n" + "".join(
            f"{u} {v} {capacity}\n" for u, v, capacity in edges
        )
        try:
            _ = _process.stdin.write(request)
            _process.stdin.flush()
            response = cast(str, _process.stdout.readline())
            values = [int(value) for value in response.split()]
            if len(values) != len(edges) + 1:
                raise ValueError("Missing or malformed Julia flow response")
        except (OSError, ValueError) as exc:
            _stop_worker()
            raise RuntimeError(
                "Julia max-flow solver failed; see its stderr output"
            ) from exc
        return values[0], values[1:]
