import math
from bisect import bisect_left
from collections.abc import Callable

from julia_flow import maximum_flow


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
    for name, value in (
        ("k", k),
        ("L", L),
        ("U", U),
    ):
        if isinstance(value, bool):
            raise TypeError(f"{name} must be an integer, not a boolean")
    if any(
        isinstance(j, bool) for choices in eligible_centers_by_point for j in choices
    ):
        raise TypeError("Eligible center indices must be integers, not booleans")
    n = len(eligible_centers_by_point)
    if k < 0 or not 0 <= L <= U <= n:
        raise ValueError("Require k >= 0 and 0 <= L <= U <= n")
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
    source, overflow, sink = 1, n + k + offset, n + k + 1 + offset
    # each edge is described as [u, v, capacity]
    edges: list[tuple[int, int, int]] = []
    for point, choices in enumerate(eligible_centers_by_point):
        edges.append((source, point + offset, 1))
        for center in dict.fromkeys(choices):
            edges.append((point + offset, n + center + offset, 1))
    for center in range(k):
        edges.append((n + center + offset, sink, L))
        edges.append((n + center + offset, overflow, U - L))
    # Total capacity into sink is n. Sending n units saturates every direct
    # center -> sink edge, enforcing minimum loads. Extra load uses overflow.
    edges.append((overflow, sink, n - k * L))

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
    U: int,
    L: int = 0,
    distance: Callable[[list[int], list[int]], float] = math.dist,
) -> float | None:
    """Return the smallest feasible point-center distance, or None if impossible.

    Centers are fixed and each must have a load in [L, U], with U <= len(points).
    Empty points have radius 0.0 only when L = U = 0. Distances must
    be finite and nonnegative. Solver failures propagate as RuntimeError.
    """
    for name, value in (("L", L), ("U", U)):
        if isinstance(value, bool):
            raise TypeError(f"{name} must be an integer, not a boolean")
    n, k = len(points), len(centers)
    if not 0 <= L <= U <= n:
        raise ValueError("Require 0 <= L <= U <= n")

    if not k * L <= n <= k * U:
        return None
    if n == 0:
        return 0.0

    distances = [[distance(point, center) for center in centers] for point in points]
    radii = sorted({value for row in distances for value in row})
    if any(not math.isfinite(radius) or radius < 0 for radius in radii):
        raise ValueError("Distances must be finite and nonnegative")

    def is_feasible(radius: float) -> bool:
        eligible_centers_by_point = [
            [center for center, value in enumerate(row) if value <= radius]
            for row in distances
        ]
        return (
            find_feasible_assignment(
                eligible_centers_by_point,
                k=k,
                U=U,
                L=L,
            )
            is not None
        )

    # Feasibility is monotone: increasing the radius only adds eligible edges.
    # bisect_left locates the first True without evaluating every candidate.
    index = bisect_left(radii, True, key=is_feasible)
    return radii[index] if index < len(radii) else None


def solve(
    points: list[list[int]],
    centers: list[list[int]],
    *,
    U: int,
    L: int = 0,
    distance: Callable[[list[int], list[int]], float] = math.dist,
) -> None:
    """Print the minimum feasible radius and an assignment for fixed centers."""
    radius = find_min_radius(
        points,
        centers,
        U=U,
        L=L,
        distance=distance,
    )
    if radius is None:
        print("Infeasible")
        return

    # Reconstruct an assignment at the minimum radius returned by the search.
    eligible_centers_by_point = find_eligible_centers(
        points, centers, radius, distance=distance
    )
    assignment = find_feasible_assignment(
        eligible_centers_by_point,
        k=len(centers),
        U=U,
        L=L,
    )

    if assignment is None:
        raise RuntimeError("No assignment found at the minimum feasible radius")

    maximum_distance = max(
        (
            distance(point, centers[center])
            for point, center in zip(points, assignment, strict=True)
        ),
        default=0.0,
    )
    print("Minimum feasible radius:", radius)
    print("Assignment (center indices):", assignment)
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
