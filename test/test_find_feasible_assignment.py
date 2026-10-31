import pytest

from main import find_feasible_assignment


@pytest.mark.parametrize(
    "eligible_centers_by_point,k,L,U",
    [
        ([], 0, 0, 1),
        ([], 1, 1, 1),
        ([list[int]()], 1, 0, 2),
        ([[0]], 1, 0, 2),
    ],
)
def test_capacity_exceeds_point_count(
    eligible_centers_by_point: list[list[int]], k: int, L: int, U: int
) -> None:
    with pytest.raises(ValueError, match="U <= n"):
        _ = find_feasible_assignment(eligible_centers_by_point, k=k, L=L, U=U)


@pytest.mark.parametrize("n", [0, 1, 3])
def test_capacity_equals_point_count(n: int) -> None:
    assert find_feasible_assignment([[0]] * n, k=1, U=n) == [0] * n


@pytest.mark.parametrize(
    "eligible_centers_by_point,k,L,U,feasible",
    [
        pytest.param([], 0, 0, 0, True, id="no-points-no-centers"),
        pytest.param([], 1, 0, 0, True, id="no-points-zero-minimum-load"),
        pytest.param([[0], []], 1, 0, 2, False, id="one-centerless-point"),
        pytest.param([[0]], 1, 0, 0, False, id="zero-capacity"),
        pytest.param(
            [[0], [0], [1, 2]], 3, 0, 1, False, id="shared-center-capacity-exceeded"
        ),
        # Point 0 must use center 1; center 2 must remain empty because no point
        # is eligible for it. Its zero minimum load allows this.
        pytest.param(
            [[0, 1], [0], [0], [1]], 3, 0, 2, True, id="rerouting-with-unused-center"
        ),
        # Valid per-center bounds, but too few points to meet all minimums.
        pytest.param([[0, 1]] * 3, 2, 2, 3, False, id="below-minimum-load"),
        # The coefficient on eligible_centers_by_point represents n points.
        pytest.param([[0]] * 2 + [[1]] * 2, 2, 2, 4, True, id="at-minimum-load"),
        pytest.param(
            [[0]] * 3 + [[1]] * 3,
            2,
            2,
            4,
            True,
            id="between-minimum-load-and-capacity",
        ),
        pytest.param([[0]] * 4, 1, 2, 4, True, id="at-capacity"),
        # Three points need center 0's two slots, despite four slots overall.
        pytest.param([[0]] * 3, 2, 0, 2, False, id="exceeds-individual-capacity"),
        # Every point can use either center, but three points exceed two slots.
        pytest.param([[0, 1]] * 3, 2, 0, 1, False, id="exceeds-overall-capacity"),
        pytest.param(
            [[0, 1, 2], [3], [3], [3]], 4, 1, 3, False, id="minimum-load-conflict"
        ),
        pytest.param([[0, 1], [0, 1]], 2, 1, 1, True, id="multiple-valid-assignments"),
    ],
)
def test_find_feasible_assignment(
    eligible_centers_by_point: list[list[int]],
    k: int,
    L: int,
    U: int,
    feasible: bool,
) -> None:
    assignment = find_feasible_assignment(
        eligible_centers_by_point=eligible_centers_by_point,
        k=k,
        L=L,
        U=U,
    )
    if not feasible:
        assert assignment is None
        return

    # Accept any assignment satisfying the contract, regardless of solver order.
    assert assignment is not None
    assert len(assignment) == len(eligible_centers_by_point), (
        "Every point must be assigned"
    )
    for i, center in enumerate(assignment):
        assert 0 <= center < k, f"Point {i} has invalid center index {center}"
        assert center in eligible_centers_by_point[i], (
            f"Point {i} has ineligible center {center}"
        )
    for center in range(k):
        load = assignment.count(center)
        assert L <= load <= U, f"Center {center} has load {load}"


@pytest.mark.parametrize("name", ["k", "L", "U"])
@pytest.mark.parametrize("value", [False, True])
@pytest.mark.parametrize("eligible_centers_by_point", [[], [[0]]])
def test_rejects_boolean_parameters(
    name: str, value: bool, eligible_centers_by_point: list[list[int]]
) -> None:
    parameters = {"k": 1, "L": 0, "U": 1}
    parameters[name] = value
    with pytest.raises(TypeError, match=f"{name} must be an integer, not a boolean"):
        _ = find_feasible_assignment(
            eligible_centers_by_point,
            k=parameters["k"],
            L=parameters["L"],
            U=parameters["U"],
        )


@pytest.mark.parametrize("center", [False, True])
def test_rejects_boolean_center_indices(center: bool) -> None:
    with pytest.raises(
        TypeError, match="Eligible center indices must be integers, not booleans"
    ):
        _ = find_feasible_assignment([[center]], k=2, U=1)
