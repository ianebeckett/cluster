import math
from collections.abc import Callable

def find_eligible_centers(
    points: list[list[int]],
    centers: list[list[int]],
    radius: float,
    *,
    distance: Callable[[list[int], list[int]], float] = math.dist,
) -> list[list[int]]:
    """Return, for each point, all center indices within radius."""
    return [[]]


def find_feasible_assignment(
    eligible_centers: list[list[int]],
    *,
    k: int,
    upper_bound: int,
    lower_bound: int = 0,
) -> list[int] | None:
    """Assign each point to an eligible center without exceeding upper or lower bounds."""
    pass


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
