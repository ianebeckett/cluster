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


def solve():
    P = [[0]]
    candidates = [[0]]
    radius = 0
    k = 1

    C = find_eligible_centers(P, candidates, radius)

    U = 0
    assignment = find_feasible_assignment(C, k=k, upper_bound=U)

    if assignment is None:
        print("Infeasible")
    else:
        print("Feasible:", assignment)


def main():
    solve()


if __name__ == "__main__":
    main()
