import pytest

from main import find_eligible_centers, find_feasible_assignment


@pytest.mark.parametrize(
    "points,centers,radius,expected",
    [
        ([], [[0]], 1, []),
        ([[0], [1]], [], 1, [list[int](), list[int]()]),
        ([[0], [1], [3]], [[0], [2]], 1, [[0], [0, 1], [1]]),
        ([[0], [1]], [[0]], 0, [[0], []]),
        ([[0, 0]], [[3, 4], [4, 4]], 5, [[0]]),
    ],
)
def test_find_eligible_centers(
    points: list[list[int]],
    centers: list[list[int]],
    radius: float,
    expected: list[list[int]],
) -> None:
    assert find_eligible_centers(points, centers, radius) == expected


def test_custom_distance() -> None:
    def manhattan(a: list[int], b: list[int]) -> float:
        return sum(abs(x - y) for x, y in zip(a, b, strict=True))

    assert find_eligible_centers([[0, 0]], [[1, 1]], 1.5, distance=manhattan) == [[]]


def test_geometry_to_assignment() -> None:
    choices = find_eligible_centers([[1], [0]], [[0], [2]], radius=1)
    assert find_feasible_assignment(choices, k=2, lower_bound=1, upper_bound=1) == [
        1,
        0,
    ]
