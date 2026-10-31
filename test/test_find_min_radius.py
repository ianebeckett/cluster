import math
from itertools import product
from random import Random

import pytest

import main
from main import find_min_radius, solve


@pytest.mark.parametrize(
    "points,centers,lower_bound,upper_bound,expected",
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
        pytest.param([[0]], [[0], [1]], 1, 2, None, id="insufficient-points"),
        pytest.param([[0]], [], 0, 1, None, id="no-centers"),
        pytest.param([], [], 0, 0, 0.0, id="empty-instance"),
        pytest.param([], [[0]], 0, 1, 0.0, id="empty-points-zero-minimum"),
        pytest.param([], [[0]], 1, 1, None, id="empty-points-positive-minimum"),
    ],
)
def test_find_min_radius(
    points: list[list[int]],
    centers: list[list[int]],
    lower_bound: int,
    upper_bound: int,
    expected: float | None,
) -> None:
    assert (
        find_min_radius(
            points, centers, lower_bound=lower_bound, upper_bound=upper_bound
        )
        == expected
    )


def test_custom_distance() -> None:
    def manhattan(a: list[int], b: list[int]) -> float:
        return float(sum(abs(x - y) for x, y in zip(a, b, strict=True)))

    assert (
        find_min_radius(
            [[0, 0], [1, 1]],
            [[0, 0], [3, 3]],
            lower_bound=1,
            upper_bound=1,
            distance=manhattan,
        )
        == 4.0
    )


@pytest.mark.parametrize("points", [[], [[0]]])
@pytest.mark.parametrize(
    "lower_bound,upper_bound,error",
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
    lower_bound: int,
    upper_bound: int,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        _ = find_min_radius(
            points, [[0]], lower_bound=lower_bound, upper_bound=upper_bound
        )


@pytest.mark.parametrize("value", [-1.0, math.inf, -math.inf, math.nan])
def test_invalid_distance(value: float) -> None:
    def distance(_a: list[int], _b: list[int]) -> float:
        return value

    with pytest.raises(ValueError, match="finite and nonnegative"):
        _ = find_min_radius([[0]], [[1]], upper_bound=1, distance=distance)


def test_solver_failure_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(
        _node_count: int, _edges: list[tuple[int, int, int]]
    ) -> tuple[int, list[int]]:
        raise RuntimeError("Solver failed")

    monkeypatch.setattr(main, "maximum_flow", fail)
    with pytest.raises(RuntimeError, match="Solver failed"):
        _ = find_min_radius([[0]], [[1]], upper_bound=1)


@pytest.mark.parametrize("seed", range(20))
def test_matches_exhaustive_assignments(seed: int) -> None:
    rng = Random(seed)
    points = [[rng.randrange(8), rng.randrange(8)] for _ in range(rng.randint(1, 5))]
    centers = [[rng.randrange(8), rng.randrange(8)] for _ in range(rng.randint(1, 3))]
    lower_bound = rng.randrange(3)
    upper_bound = rng.randint(max(1, lower_bound), len(points) + lower_bound)

    # Enumerate whole assignments independently of binary search and max flow.
    expected: float | None = None
    for assignment in product(range(len(centers)), repeat=len(points)):
        if not all(
            lower_bound <= assignment.count(center) <= upper_bound
            for center in range(len(centers))
        ):
            continue
        radius = max(
            math.dist(point, centers[center])
            for point, center in zip(points, assignment, strict=True)
        )
        if expected is None or radius < expected:
            expected = radius

    result = solve(points, centers, lower_bound=lower_bound, upper_bound=upper_bound)
    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result.radius == expected
        assert len(result.assignment) == len(points)
        assert all(0 <= center < len(centers) for center in result.assignment)
        assert all(
            lower_bound <= result.assignment.count(center) <= upper_bound
            for center in range(len(centers))
        )
        assert (
            max(
                math.dist(point, centers[center])
                for point, center in zip(points, result.assignment, strict=True)
            )
            == expected
        )

    assert (
        find_min_radius(
            points, centers, lower_bound=lower_bound, upper_bound=upper_bound
        )
        == expected
    )
