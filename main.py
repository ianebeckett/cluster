import math
from collections.abc import Callable

from julia_flow import maximum_flow


def find_eligible_centers(
    points: list[list[int]],
    centers: list[list[int]],
    radius: float,
    *,
    distance: Callable[[list[int], list[int]], float] = math.dist,
) -> list[list[int]]:
    """Return center indices within radius, preserving the order of points."""
    return [
        [j for j, center in enumerate(centers) if distance(point, center) <= radius]
        for point in points
    ]


def find_feasible_assignment(
    eligible_centers: list[list[int]],
    *,
    k: int,
    upper_bound: int,
    lower_bound: int = 0,
) -> list[int] | None:
    """Return one eligible center index per point, or None if infeasible.

    Input row i and output entry i refer to the same point. All k centers must
    have loads in [lower_bound, upper_bound], including unused centers.
    Booleans are rejected for k, bounds, and center indices with TypeError.
    Invalid bounds or center indices raise ValueError; Julia failures raise
    RuntimeError rather than being treated as infeasible assignments.
    """
    for name, value in (
        ("k", k),
        ("lower_bound", lower_bound),
        ("upper_bound", upper_bound),
    ):
        if isinstance(value, bool):
            raise TypeError(f"{name} must be an integer, not a boolean")
    if any(isinstance(j, bool) for choices in eligible_centers for j in choices):
        raise TypeError("Eligible center indices must be integers, not booleans")
    if k < 0 or not 0 <= lower_bound <= upper_bound:
        raise ValueError("Require k >= 0 and 0 <= lower_bound <= upper_bound")
    if any(not 0 <= j < k for choices in eligible_centers for j in choices):
        raise ValueError("Eligible center indices must be in range(k)")

    n = len(eligible_centers)
    if any(not choices for choices in eligible_centers):
        return None  # A centerless point cannot be assigned.
    if not k * lower_bound <= n <= k * upper_bound:
        return None
    if n == 0:
        return []

    # newMaxFlow uses one-based indices, source = 1, and sink = last node.
    # Points occupy 2..n+1; centers occupy n+2..n+k+1.
    offset = 2
    unit_flow = 1
    source, overflow, sink = 1, n + k + offset, n + k + 1 + offset
    edges: list[tuple[int, int, int]] = []
    for point, choices in enumerate(eligible_centers):
        edges.append((source, point + offset, unit_flow))
        for center in dict.fromkeys(choices):
            edges.append((point + offset, n + center + offset, unit_flow))
    for center in range(k):
        edges.append((n + center + offset, sink, lower_bound))
        edges.append((n + center + offset, overflow, min(upper_bound, n) - lower_bound))
    # Total capacity into sink is n. Sending n units saturates every direct
    # center -> sink edge, enforcing minimum loads. Extra load uses overflow.
    edges.append((overflow, sink, n - k * lower_bound))

    max_flow, edge_flows = maximum_flow(sink, edges)
    if max_flow != n:
        return None

    assignment = [-1] * n
    # note: Assignment by index assumes the flow solver returns edges in the
    # order they were given.
    for (u, v, _), flow in zip(edges, edge_flows, strict=True):
        if offset <= u <= n + 1 and n + offset <= v <= n + k + 1 and flow == unit_flow:
            assignment[u - offset] = v - n - offset
    if -1 in assignment:
        raise RuntimeError("Julia returned full flow without a complete assignment")
    return assignment


def solve(
    points: list[list[int]],
    centers: list[list[int]],
    radius: float,
    *,
    upper_bound: int,
    lower_bound: int = 0,
) -> None:
    eligible_centers = find_eligible_centers(points, centers, radius)
    assignment = find_feasible_assignment(
        eligible_centers,
        k=len(centers),
        upper_bound=upper_bound,
        lower_bound=lower_bound,
    )

    if assignment is None:
        print("Infeasible")
    else:
        print("Feasible:", assignment)


def main() -> None:
    points = [[0]]
    centers = [[0]]

    # Infeasible: the center has zero capacity.
    solve(points, centers, radius=0, upper_bound=0)

    # Feasible: the center has capacity for the point.
    solve(points, centers, radius=0, upper_bound=1)


if __name__ == "__main__":
    main()
