import math
from collections.abc import Callable
from itertools import product
from random import Random

import pytest

import main
from main import ClusteringResult, find_minimax_assignment


def _assert_valid_assignment(
    result: ClusteringResult,
    points: list[list[int]],
    centers: list[list[int]],
    L: int,
    U: int,
    distance: Callable[[list[int], list[int]], float] = math.dist,
) -> None:
    assert len(result.assignment) == len(points)
    assert all(0 <= center < len(centers) for center in result.assignment)
    assert all(
        L <= result.assignment.count(center) <= U for center in range(len(centers))
    )
    assert (
        max(
            (
                distance(point, centers[center])
                for point, center in zip(points, result.assignment, strict=True)
            ),
            default=0.0,
        )
        == result.radius
    )


@pytest.mark.parametrize(
    "points,centers,L,U",
    [
        ([], [], 0, 1),
        ([], [[0]], 1, 1),
        ([[0]], [], 0, 2),
        ([[0]], [[0]], 0, 2),
    ],
)
def test_capacity_exceeds_point_count(
    points: list[list[int]], centers: list[list[int]], L: int, U: int
) -> None:
    with pytest.raises(ValueError, match="U <= n"):
        _ = find_minimax_assignment(points, centers, L=L, U=U)


@pytest.mark.parametrize("n", [0, 1, 3])
def test_capacity_equals_point_count(n: int) -> None:
    points = [[i] for i in range(n)]
    result = find_minimax_assignment(points, [[0]], U=n)
    assert result is not None
    assert result.radius == float(max(n - 1, 0))
    _assert_valid_assignment(result, points, [[0]], 0, n)


@pytest.mark.parametrize(
    "points,centers,L,U,expected",
    [
        pytest.param([[0]], [[0]], 0, 1, 0.0, id="zero-radius"),
        pytest.param([[1]], [[0], [10]], 0, 1, 1.0, id="first-candidate"),
        pytest.param([[1], [3]], [[0]], 0, 2, 3.0, id="last-candidate"),
        pytest.param([[1], [9]], [[0], [10]], 1, 1, 1.0, id="duplicate-distances"),
        pytest.param(
            [[0], [1]], [[0], [10]], 0, 1, 9.0, id="capacity-forces-rerouting"
        ),
        pytest.param(
            [[0], [1]], [[0], [10]], 1, 2, 9.0, id="minimum-load-forces-rerouting"
        ),
        pytest.param([[0, 0]], [[1, 1]], 0, 1, math.sqrt(2), id="fractional-distance"),
        pytest.param([[0], [1]], [[0]], 0, 1, None, id="insufficient-capacity"),
        pytest.param([[0]], [[0], [1]], 1, 1, None, id="insufficient-points"),
        pytest.param([[0]], [], 0, 1, None, id="no-centers"),
        pytest.param([], [], 0, 0, 0.0, id="empty-instance"),
        pytest.param([], [[0]], 0, 0, 0.0, id="empty-points-zero-minimum"),
    ],
)
def test_find_minimax_assignment(
    points: list[list[int]],
    centers: list[list[int]],
    L: int,
    U: int,
    expected: float | None,
) -> None:
    result = find_minimax_assignment(points, centers, L=L, U=U)
    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result.radius == expected
        _assert_valid_assignment(result, points, centers, L, U)


def test_preserves_point_order_when_rerouting() -> None:
    points, centers = [[1], [0]], [[0], [2]]
    result = find_minimax_assignment(points, centers, L=1, U=1)
    assert result is not None
    assert result.radius == 1.0
    # Point 1 can only use center 0 at this radius, forcing point 0 to center 1.
    assert result.assignment == (1, 0)
    _assert_valid_assignment(result, points, centers, 1, 1)


def test_custom_distance() -> None:
    def manhattan(a: list[int], b: list[int]) -> float:
        return float(sum(abs(x - y) for x, y in zip(a, b, strict=True)))

    points, centers = [[0, 0], [1, 1]], [[0, 0], [3, 3]]
    result = find_minimax_assignment(
        points,
        centers,
        L=1,
        U=1,
        distance=manhattan,
    )
    assert result is not None
    assert result.radius == 4.0
    _assert_valid_assignment(result, points, centers, 1, 1, manhattan)


@pytest.mark.parametrize("points", [[], [[0]]])
@pytest.mark.parametrize(
    "L,U,error",
    [
        (-1, 1, ValueError),
        (0, -1, ValueError),
        (2, 1, ValueError),
        (False, 1, TypeError),
        (0, True, TypeError),
    ],
)
def test_invalid_bounds(
    points: list[list[int]],
    L: int,
    U: int,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        _ = find_minimax_assignment(points, [[0]], L=L, U=U)


@pytest.mark.parametrize("value", [-1.0, math.inf, -math.inf, math.nan])
def test_invalid_distance(value: float) -> None:
    def distance(_a: list[int], _b: list[int]) -> float:
        return value

    with pytest.raises(ValueError, match="finite and nonnegative"):
        _ = find_minimax_assignment([[0]], [[1]], U=1, distance=distance)


def test_solver_failure_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(
        _node_count: int, _edges: list[tuple[int, int, int]]
    ) -> tuple[int, list[int]]:
        raise RuntimeError("Solver failed")

    monkeypatch.setattr(main, "maximum_flow", fail)
    with pytest.raises(RuntimeError, match="Solver failed"):
        _ = find_minimax_assignment([[0]], [[1]], U=1)


@pytest.mark.parametrize("seed", range(20))
def test_matches_exhaustive_assignments(seed: int) -> None:
    rng = Random(seed)
    points = [[rng.randrange(8), rng.randrange(8)] for _ in range(rng.randint(1, 5))]
    centers = [[rng.randrange(8), rng.randrange(8)] for _ in range(rng.randint(1, 3))]
    L = rng.randint(0, min(2, len(points)))
    U = rng.randint(max(1, L), len(points))

    # Enumerate whole assignments independently of binary search and max flow.
    expected: float | None = None
    for assignment in product(range(len(centers)), repeat=len(points)):
        if not all(
            L <= assignment.count(center) <= U for center in range(len(centers))
        ):
            continue
        radius = max(
            math.dist(point, centers[center])
            for point, center in zip(points, assignment, strict=True)
        )
        if expected is None or radius < expected:
            expected = radius

    result = find_minimax_assignment(points, centers, L=L, U=U)
    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result.radius == expected
        _assert_valid_assignment(result, points, centers, L, U)


def test_search_reuses_distances_without_mutating_inputs() -> None:
    points, centers = [[0], [1]], [[0], [10]]
    original_points = [point.copy() for point in points]
    original_centers = [center.copy() for center in centers]
    calls = 0

    def distance(a: list[int], b: list[int]) -> float:
        nonlocal calls
        calls += 1
        return math.dist(a, b)

    result = find_minimax_assignment(points, centers, L=1, U=1, distance=distance)
    assert result is not None
    assert result.radius == 9.0
    assert calls == len(points) * len(centers)
    assert points == original_points
    assert centers == original_centers
