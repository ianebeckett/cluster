import math

import pytest

import main
from julia_flow import maximum_flow
from main import solve


@pytest.mark.parametrize(
    "points,centers,lower_bound,upper_bound,radius,assignment",
    [
        ([[0], [1]], [[0], [10]], 0, 2, 1.0, [0, 0]),
        ([[0], [1]], [[0], [10]], 1, 1, 9.0, [0, 1]),
        ([[0, 0]], [[1, 1]], 0, 1, math.sqrt(2), [0]),
        ([[1], [2]], [[0]], 0, 2, 2.0, [0, 0]),
        ([], [], 0, 0, 0.0, []),
    ],
)
def test_solve_returns_minimum_radius_and_assignment(
    points: list[list[int]],
    centers: list[list[int]],
    lower_bound: int,
    upper_bound: int,
    radius: float,
    assignment: list[int],
    capsys: pytest.CaptureFixture[str],
) -> None:
    original_points = [point.copy() for point in points]
    original_centers = [center.copy() for center in centers]
    result = solve(points, centers, lower_bound=lower_bound, upper_bound=upper_bound)
    assert result is not None
    assert result.radius == radius
    assert result.assignment == tuple(assignment)
    assert points == original_points
    assert centers == original_centers
    assert capsys.readouterr().out == ""


def test_solve_infeasible(capsys: pytest.CaptureFixture[str]) -> None:
    assert solve([[0], [1]], [[0]], upper_bound=1) is None
    assert capsys.readouterr().out == ""


def test_solve_uses_custom_distance(capsys: pytest.CaptureFixture[str]) -> None:
    def manhattan(a: list[int], b: list[int]) -> float:
        return float(sum(abs(x - y) for x, y in zip(a, b, strict=True)))

    result = solve([[0, 0]], [[1, 1]], upper_bound=1, distance=manhattan)
    assert result is not None
    assert result.radius == 2.0
    assert result.assignment == (0,)
    assert capsys.readouterr().out == ""


def test_solve_reuses_distances_and_winning_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[int, tuple[tuple[int, int, int], ...]]] = []
    distance_calls = 0

    def counting_flow(
        node_count: int, edges: list[tuple[int, int, int]]
    ) -> tuple[int, list[int]]:
        calls.append((node_count, tuple(edges)))
        return maximum_flow(node_count, edges)

    def counting_distance(a: list[int], b: list[int]) -> float:
        nonlocal distance_calls
        distance_calls += 1
        return math.dist(a, b)

    monkeypatch.setattr(main, "maximum_flow", counting_flow)
    result = solve(
        [[0], [1]],
        [[0], [10]],
        lower_bound=1,
        upper_bound=1,
        distance=counting_distance,
    )
    assert result is not None
    assert result.radius == 9.0
    assert distance_calls == 4
    assert calls
    assert len(calls) == len(set(calls)), "The winning network must not be solved again"


def test_main_demonstrates_minimum_radius(capsys: pytest.CaptureFixture[str]) -> None:
    main.main()
    output = capsys.readouterr().out
    assert "Minimum feasible radius: 1.0\n" in output
    assert "Maximum assigned p-c distance: 1.0\n" in output
    assert "Minimum feasible radius: 9.0\n" in output
    assert "Maximum assigned p-c distance: 9.0\n" in output
    assert "Infeasible\n" in output
