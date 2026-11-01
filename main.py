import math
from collections.abc import Callable
from dataclasses import dataclass

from julia_flow import maximum_flow


@dataclass(frozen=True)
class ClusteringResult:
    """A minimax radius and one center index per point, for supplied centers."""

    radius: float
    assignment: tuple[int, ...]


def find_eligible_centers(
    points: list[list[int]],
    centers: list[list[int]],
    radius: float,
    *,
    distance: Callable[[list[int], list[int]], float] = math.dist,
) -> list[list[int]]:
    """Return eligible center indices for each point, preserving input order.

    Result row i contains indices into centers for points[i]
    """
    return [
        [j for j, center in enumerate(centers) if distance(point, center) <= radius]
        for point in points
    ]


def _validate_load_bounds(*, n: int, k: int, L: int, U: int) -> None:
    """Validate load-bound inputs; assignment feasibility is checked separately."""
    for name, value in (("k", k), ("L", L), ("U", U)):
        if isinstance(value, bool):
            raise TypeError(f"{name} must be an integer, not a boolean")
    if k < 0 or not 0 <= L <= U <= n:
        raise ValueError("Require k >= 0 and 0 <= L <= U <= n")


def find_feasible_assignment(
    eligible_centers_by_point: list[list[int]],
    *,
    k: int,
    U: int,
    L: int = 0,
) -> list[int] | None:
    """Return one eligible center index per point, or None if infeasible.

    eligible_centers_by_point[i] lists center indices eligible for points[i]
    in the original input order. Output entry i refers to that same point.
    All k centers must have loads in [L, U].
    Booleans are rejected for k, bounds, and center indices with TypeError.
    Bounds must satisfy 0 <= L <= U <= n, where n is the number of points.
    Invalid bounds or center indices raise ValueError; Julia failures raise
    RuntimeError rather than being treated as infeasible assignments.
    """
    n = len(eligible_centers_by_point)
    _validate_load_bounds(n=n, k=k, L=L, U=U)
    if any(
        isinstance(j, bool) for choices in eligible_centers_by_point for j in choices
    ):
        raise TypeError("Eligible center indices must be integers, not booleans")
    if any(not 0 <= j < k for choices in eligible_centers_by_point for j in choices):
        raise ValueError("Eligible center indices must be in range(k)")

    if any(not choices for choices in eligible_centers_by_point):
        return None  # A centerless point cannot be assigned.
    if not k * L <= n <= k * U:
        return None
    if n == 0:
        return []

    # newMaxFlow uses one-based indices, source = 1, and sink = last node.
    # Points occupy 2..n+1; centers occupy n+2..n+k+1.
    offset = 2
    source, overflow, sink = 1, n + k + offset, n + k + offset + 1

    # Each edge is (from, to, capacity); each category expresses a constraint.

    supply_edges = (
        (source, point + offset, 1)
        for point in range(n)
    )

    eligibility_edges = (
        (point + offset, n + center + offset, 1)
        for point, choices in enumerate(eligible_centers_by_point)
        for center in dict.fromkeys(choices)
    )

    minimum_load_edges = (
        (n + center + offset, sink, L)
        for center in range(k)
    )

    extra_capacity_edges = (
        (n + center + offset, overflow, U - L)
        for center in range(k)
    )

    overflow_edge = [
        (overflow, sink, n - k * L)
    ]

    # Total capacity into sink is n. Sending n units saturates every direct
    # center -> sink edge, enforcing minimum loads. Extra load uses overflow.
    edges = [
        *supply_edges,
        *eligibility_edges,
        *minimum_load_edges,
        *extra_capacity_edges,
        *overflow_edge
    ]

    max_flow, edge_flows = maximum_flow(sink, edges)
    if max_flow != n:
        return None

    assignment = [-1] * n
    # note: Assignment by index assumes the flow solver returns edges in the
    # order they were given.
    for (u, v, _), flow in zip(edges, edge_flows, strict=True):
        if offset <= u <= n + 1 and n + offset <= v <= n + k + 1 and flow == 1:
            assignment[u - offset] = v - n - offset
    if -1 in assignment:
        raise RuntimeError("Julia returned full flow without a complete assignment")
    return assignment


def find_minimax_assignment(
    points: list[list[int]],
    centers: list[list[int]],
    *,
    U: int,
    L: int = 0,
    distance: Callable[[list[int], list[int]], float] = math.dist,
) -> ClusteringResult | None:
    """Return a minimum-radius assignment for fixed centers, or None if impossible.

    Centers are fixed and each must have a load in [L, U], with U <= len(points).
    Empty points have radius 0.0 and an empty assignment only when L = U = 0.
    Distances must be finite and nonnegative. Solver failures propagate as
    RuntimeError. Follow Ding's per-tuple search: test sorted candidate radii
    and retain the best feasible solution.
    """
    n, k = len(points), len(centers)
    _validate_load_bounds(n=n, k=k, L=L, U=U)

    if not k * L <= n <= k * U:
        return None
    if n == 0:
        return ClusteringResult(radius=0.0, assignment=())

    distances = [[distance(point, center) for center in centers] for point in points]
    radii = sorted({value for row in distances for value in row})
    if any(not math.isfinite(radius) or radius < 0 for radius in radii):
        raise ValueError("Distances must be finite and nonnegative")

    lo, hi = 0, len(radii)
    best: ClusteringResult | None = None
    # Search the half-open index interval [lo, hi). A feasible midpoint narrows
    # the search left; an infeasible midpoint rules out itself and smaller radii.
    while lo < hi:
        mid = (lo + hi) // 2
        radius = radii[mid]
        # Filter cached distances; find_eligible_centers would recompute every
        # point-center distance for each trial radius.
        eligible_centers_by_point = [
            [center for center, value in enumerate(row) if value <= radius]
            for row in distances
        ]
        assignment = find_feasible_assignment(
            eligible_centers_by_point,
            k=k,
            U=U,
            L=L,
        )
        if assignment is None:
            lo = mid + 1
        else:
            best = ClusteringResult(radius=radius, assignment=tuple(assignment))
            hi = mid

    return best


def solve(
    points: list[list[int]],
    centers: list[list[int]],
    *,
    U: int,
    L: int = 0,
    distance: Callable[[list[int], list[int]], float] = math.dist,
) -> None:
    """Print the minimum feasible radius and an assignment for fixed centers."""
    result = find_minimax_assignment(
        points,
        centers,
        U=U,
        L=L,
        distance=distance,
    )
    if result is None:
        print("Infeasible")
        return

    maximum_distance = max(
        (
            distance(point, centers[center])
            for point, center in zip(points, result.assignment, strict=True)
        ),
        default=0.0,
    )
    print("Minimum feasible radius:", result.radius)
    print("Assignment (center indices):", list(result.assignment))
    print("Maximum assigned p-c distance:", maximum_distance)


def main() -> None:
    points = [[0], [1]]
    centers = [[0], [10]]
    print("Points:", points)
    print("Fixed centers:", centers)

    # Both points fit at center 0, so the minimum radius is 1.
    print("\nCapacity 2 per center:")
    solve(points, centers, U=2)

    # Center 1 must receive a point. Point 1 is its closest option, at distance 9.
    print("\nExactly 1 point per center:")
    solve(points, centers, L=1, U=1)

    print("\nZero capacity:")
    solve(points, centers, U=0)


if __name__ == "__main__":
    main()
