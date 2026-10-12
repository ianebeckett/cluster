import pytest

from main import find_feasible_assignment


@pytest.mark.parametrize(
    "eligible_centers,k,lower_bound,upper_bound,feasible",
    [
        pytest.param([], 0, 0, 0, True, id="no-points-no-centers"),
        pytest.param([], 1, 0, 1, True, id="no-points-zero-minimum-load"),
        pytest.param([[0], []], 1, 0, 2, False, id="one-centerless-point"),
        pytest.param([[0]], 1, 0, 0, False, id="zero-capacity"),
        pytest.param([[0], [0], [1, 2]], 3, 0, 1, False, id="shared-center-capacity-exceeded"),
        # Point 0 must use center 1; center 2 must remain empty because no point
        # is eligible for it. Its zero minimum load allows this.
        pytest.param(
            [[0, 1], [0], [0], [1]], 3, 0, 2, True, id="rerouting-with-unused-center"
        ),
        # One center, with loads below, at, between, and above its bounds.
        pytest.param([], 1, 1, 1, False, id="no-points-positive-minimum-load"),
        pytest.param([[0]], 1, 2, 4, False, id="below-minimum-load"),
        # The coefficient on eligible_centers represents n points.
        pytest.param([[0]] * 2, 1, 2, 4, True, id="at-minimum-load"),
        pytest.param([[0]] * 3, 1, 2, 4, True, id="between-minimum-load-and-capacity"),
        pytest.param([[0]] * 4, 1, 2, 4, True, id="at-capacity"),
        # Three points need center 0's two slots, despite four slots overall.
        pytest.param([[0]] * 3, 2, 0, 2, False, id="exceeds-individual-capacity"),
        # Every point can use either center, but three points exceed two slots.
        pytest.param([[0, 1]] * 3, 2, 0, 1, False, id="exceeds-overall-capacity"),
        pytest.param(
            [[0, 1, 2], [3], [3], [3]], 4, 1, 3, False, id="minimum-load-conflict"
        ),
        # -----------hand-audited-----------------------------------
        pytest.param([[0, 1], [0, 1]], 2, 1, 1, True, id="multiple-valid-assignments"),
    ],
)
def test_find_feasible_assignment(
    eligible_centers: list[list[int]],
    k: int,
    lower_bound: int,
    upper_bound: int,
    feasible: bool,
) -> None:
    assignment = find_feasible_assignment(
        eligible_centers=eligible_centers,
        k=k,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )
    if not feasible:
        assert assignment is None
        return

    # Accept any assignment satisfying the contract, regardless of solver order.
    assert assignment is not None
    assert len(assignment) == len(eligible_centers), "Every point must be assigned"
    for i, center in enumerate(assignment):
        assert 0 <= center < k, f"Point {i} has invalid center index {center}"
        assert center in eligible_centers[i], (
            f"Point {i} has ineligible center {center}"
        )
    for center in range(k):
        load = assignment.count(center)
        assert lower_bound <= load <= upper_bound, f"Center {center} has load {load}"
