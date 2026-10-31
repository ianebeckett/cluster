import math

import pytest

from main import solve


@pytest.mark.parametrize(
    "points,centers,lower_bound,upper_bound,radius,assignment",
    [
        ([[0], [1]], [[0], [10]], 0, 2, 1.0, [0, 0]),
        ([[0], [1]], [[0], [10]], 1, 1, 9.0, [0, 1]),
        ([[0, 0]], [[1, 1]], 0, 1, math.sqrt(2), [0]),
        ([], [], 0, 0, 0.0, []),
    ],
)
def test_solve_reports_minimum_radius_and_assignment(
    points: list[list[int]],
    centers: list[list[int]],
    lower_bound: int,
    upper_bound: int,
    radius: float,
    assignment: list[int],
    capsys: pytest.CaptureFixture[str],
) -> None:
    solve(points, centers, lower_bound=lower_bound, upper_bound=upper_bound)
    output = capsys.readouterr().out
    assert f"Minimum feasible radius: {radius}\n" in output
    assert f"Assignment (center indices): {assignment}\n" in output
    assert f"Maximum assigned distance: {radius}\n" in output


def test_solve_infeasible(capsys: pytest.CaptureFixture[str]) -> None:
    solve([[0], [1]], [[0]], upper_bound=1)
    assert capsys.readouterr().out == "Infeasible\n"


def test_solve_uses_custom_distance(capsys: pytest.CaptureFixture[str]) -> None:
    def manhattan(a: list[int], b: list[int]) -> float:
        return float(sum(abs(x - y) for x, y in zip(a, b, strict=True)))

    solve([[0, 0]], [[1, 1]], upper_bound=1, distance=manhattan)
    output = capsys.readouterr().out
    assert "Minimum feasible radius: 2.0\n" in output
    assert "Assignment (center indices): [0]\n" in output
    assert "Maximum assigned distance: 2.0\n" in output
