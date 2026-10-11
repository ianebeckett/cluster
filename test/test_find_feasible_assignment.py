import pytest

from main import find_feasible_assignment


@pytest.mark.parametrize(
    "eligible_centers,k,lower_bound,upper_bound,expected",
    [
        pytest.param([], 0, 0, 0, [], id="no-points"),
        pytest.param([[0]], 1, 0, 1, [0], id="one-point-fits"),
        pytest.param([[]], 1, 0, 1, None, id="no-eligible-center"),
        pytest.param([[0]], 1, 0, 0, None, id="zero-capacity"),
        pytest.param([[0], [0]], 1, 0, 1, None, id="capacity-exceeded"),
        pytest.param([[0], [0]], 1, 0, 2, [0, 0], id="multiple-points-fit"),
        pytest.param([[0], [0]], 2, 0, 1, None, id="spare-capacity-unreachable"),
        pytest.param([[0, 1], [0]], 2, 0, 1, [1, 0], id="greedy-choice-fails"),
        pytest.param([[0], [0]], 1, 2, 2, [0, 0], id="lower-bound-met-exactly"),
        pytest.param(
            [[0], [0], [0]], 1, 2, 3, [0, 0, 0], id="lower-bound-is-not-exact-size"
        ),
        pytest.param([], 1, 1, 1, None, id="lower-bound-with-no-points"),
        pytest.param([[0, 1]], 2, 1, 1, None, id="too-few-points-for-lower-bounds"),
        pytest.param([[0], [0]], 2, 1, 2, None, id="lower-bound-at-unreachable-center"),
        pytest.param(
            [[0, 1], [0]], 2, 1, 2, [1, 0], id="lower-bound-forces-other-center"
        ),
    ],
)
def test_find_feasible_assignment(
    eligible_centers: list[list[int]],
    k: int,
    lower_bound: int,
    upper_bound: int,
    expected: list[int] | None,
) -> None:
    assignment = find_feasible_assignment(
        eligible_centers=eligible_centers,
        k=k,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )
    assert assignment == expected
