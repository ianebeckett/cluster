import math

import pytest

import main
from julia_flow import maximum_flow
from main import solve


@pytest.mark.parametrize("points", [[], [[0]]])
def test_capacity_exceeds_point_count(points: list[list[int]]) -> None:
    with pytest.raises(ValueError, match="U <= n"):
        solve(points, [[0]], U=len(points) + 1)


@pytest.mark.parametrize(
    "points,centers,L,U,radius,assignment",
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
    L: int,
    U: int,
    radius: float,
    assignment: list[int],
    capsys: pytest.CaptureFixture[str],
) -> None:
    solve(points, centers, L=L, U=U)
    output = capsys.readouterr().out
    assert f"Minimum feasible radius: {radius}\n" in output
    assert f"Assignment (center indices): {assignment}\n" in output
    assert f"Maximum assigned p-c distance: {radius}\n" in output


def test_solve_infeasible(capsys: pytest.CaptureFixture[str]) -> None:
    solve([[0], [1]], [[0]], U=1)
    assert capsys.readouterr().out == "Infeasible\n"


def test_solve_uses_custom_distance(capsys: pytest.CaptureFixture[str]) -> None:
    def manhattan(a: list[int], b: list[int]) -> float:
        return float(sum(abs(x - y) for x, y in zip(a, b, strict=True)))

    solve([[0, 0]], [[1, 1]], U=1, distance=manhattan)
    output = capsys.readouterr().out
    assert "Minimum feasible radius: 2.0\n" in output
    assert "Assignment (center indices): [0]\n" in output
    assert "Maximum assigned p-c distance: 2.0\n" in output


def test_solve_does_not_repeat_winning_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, tuple[tuple[int, int, int], ...]]] = []

    def counting_flow(
        node_count: int, edges: list[tuple[int, int, int]]
    ) -> tuple[int, list[int]]:
        calls.append((node_count, tuple(edges)))
        return maximum_flow(node_count, edges)

    monkeypatch.setattr(main, "maximum_flow", counting_flow)
    solve([[0], [1]], [[0], [10]], L=1, U=1)
    assert calls
    assert len(calls) == len(set(calls)), "The winning network was solved again"
