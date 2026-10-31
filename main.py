import math
from bisect import bisect_left
from collections.abc import Callable
from dataclasses import dataclass

from julia_flow import maximum_flow


@dataclass(frozen=True)
class ClusteringResult:
    """A minimum radius and one center index per point, for fixed centers."""

    radius: float
    assignment: tuple[int, ...]


def _validate_load_bounds(k: int, lower_bound: int, upper_bound: int) -> None:
    for name, value in (
        ("k", k),
        ("lower_bound", lower_bound),
        ("upper_bound", upper_bound),
    ):
        if isinstance(value, bool):
            raise TypeError(f"{name} must be an integer, not a boolean")
    if k < 0 or not 0 <= lower_bound <= upper_bound:
        raise ValueError("Require k >= 0 and 0 <= lower_bound <= upper_bound")


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
    _validate_load_bounds(k, lower_bound, upper_bound)
    if any(isinstance(j, bool) for choices in eligible_centers for j in choices):
        raise TypeError("Eligible center indices must be integers, not booleans")
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
    source, overflow, sink = 1, n + k + offset, n + k + 1 + offset
    # Each edge is (from, to, capacity); each group expresses one constraint.
    supply_edges = ((source, point + offset, 1) for point in range(n))
    eligibility_edges = (
        (point + offset, n + center + offset, 1)
        for point, choices in enumerate(eligible_centers)
        for center in dict.fromkeys(choices)
    )
    minimum_load_edges = (
        (n + center + offset, sink, lower_bound) for center in range(k)
    )
    extra_capacity_edges = (
        (n + center + offset, overflow, min(upper_bound, n) - lower_bound)
        for center in range(k)
    )
    # Total capacity into sink is n. Sending n units saturates every direct
    # center -> sink edge, enforcing minimum loads. Extra load uses overflow.
    edges = [
        *supply_edges,
        *eligibility_edges,
        *minimum_load_edges,
        *extra_capacity_edges,
        (overflow, sink, n - k * lower_bound),
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


def find_min_radius(
    points: list[list[int]],
    centers: list[list[int]],
    *,
    upper_bound: int,
    lower_bound: int = 0,
    distance: Callable[[list[int], list[int]], float] = math.dist,
) -> float | None:
    """Return only the radius from solve, or None if the load bounds are infeasible."""
    result = solve(
        points,
        centers,
        upper_bound=upper_bound,
        lower_bound=lower_bound,
        distance=distance,
    )
    return None if result is None else result.radius


def solve(
    points: list[list[int]],
    centers: list[list[int]],
    *,
    upper_bound: int,
    lower_bound: int = 0,
    distance: Callable[[list[int], list[int]], float] = math.dist,
) -> ClusteringResult | None:
    """Return the minimum radius and its assignment without printing.

    Centers are fixed and each must have a load in [lower_bound, upper_bound].
    Empty points have radius 0.0 when the load bounds permit it. Distances must
    be finite and nonnegative. Solver failures propagate as RuntimeError.

    Follow Ding (2020), Section 2.1 and Algorithm 1, steps 2-3, for one fixed
    center tuple: sort candidate distances, binary-search feasibility, and
    retain the best feasible solution. Use point-level flow as the baseline.
    """
    n, k = len(points), len(centers)
    _validate_load_bounds(k, lower_bound, upper_bound)
    if not k * lower_bound <= n <= k * upper_bound:
        return None
    if n == 0:
        return ClusteringResult(radius=0.0, assignment=())

    distances = [[distance(point, center) for center in centers] for point in points]
    radii = sorted({value for row in distances for value in row})
    if any(not math.isfinite(radius) or radius < 0 for radius in radii):
        raise ValueError("Distances must be finite and nonnegative")

    best: ClusteringResult | None = None

    def is_feasible(radius: float) -> bool:
        nonlocal best
        eligible_centers = [
            [center for center, value in enumerate(row) if value <= radius]
            for row in distances
        ]
        assignment = find_feasible_assignment(
            eligible_centers,
            k=k,
            upper_bound=upper_bound,
            lower_bound=lower_bound,
        )
        if assignment is None:
            return False
        if best is None or radius < best.radius:
            best = ClusteringResult(radius=radius, assignment=tuple(assignment))
        return True

    # Feasibility is monotone: increasing the radius only adds eligible edges.
    # bisect_left locates the first True without evaluating every candidate.
    _ = bisect_left(radii, True, key=is_feasible)
    return best


def main() -> None:
    points = [[0], [1]]
    centers = [[0], [10]]
    print("Points:", points)
    print("Fixed centers:", centers)

    examples = (
        ("Capacity 2 per center", 0, 2),  # Both points fit at center 0: radius 1.
        ("Exactly 1 point per center", 1, 1),  # Point 1 must use center 1: radius 9.
        ("Zero capacity", 0, 0),
    )
    for label, lower_bound, upper_bound in examples:
        print(f"\n{label}:")
        result = solve(
            points, centers, lower_bound=lower_bound, upper_bound=upper_bound
        )
        if result is None:
            print("Infeasible")
            continue
        maximum_distance = max(
            (
                math.dist(point, centers[center])
                for point, center in zip(points, result.assignment, strict=True)
            ),
            default=0.0,
        )
        print("Minimum feasible radius:", result.radius)
        print("Assignment (center indices):", list(result.assignment))
        print("Maximum assigned p-c distance:", maximum_distance)


if __name__ == "__main__":
    main()
