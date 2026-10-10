def find_eligible_centers(
    points: list[list[float]],
    centers: list[list[float]],
    radius: float,
) -> list[list[int]]:
    """Return, for each point, all center indices within radius."""
    pass


def find_feasible_assignment(
    eligible_centers: list[list[int]],
    capacities: list[int],
) -> list[int] | None:
    """Assign each point to an eligible center without exceeding capacities."""
    pass


def solve():
    eligible_centers = find_eligible_centers(points, centers, radius)
    assignment = find_feasible_assignment(eligible_centers, capacities)
    if assignment is None:
        print("Infeasible")
    else:
        print("Feasible:", assignment)


def main():
    solve()


if __name__ == "__main__":
    main()
