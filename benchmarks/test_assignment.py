from collections import Counter

from pytest_benchmark.fixture import BenchmarkFixture

from main import find_feasible_assignment


def test_assignment_warm(benchmark: BenchmarkFixture) -> None:
    n, k = 1_000, 20
    choices = [list(range(k)) for _ in range(n)]
    capacity = n // k

    assignment = benchmark.pedantic(
        find_feasible_assignment,
        args=(choices,),
        kwargs={
            "k": k,
            "lower_bound": capacity,
            "upper_bound": capacity,
        },
        iterations=1,
        rounds=20,
        warmup_rounds=3,
    )

    # Validate the result outside the timed operation.
    assert assignment is not None
    assert len(assignment) == n
    assert all(c in choices[i] for i, c in enumerate(assignment))
    loads = Counter(assignment)
    assert all(loads[c] == capacity for c in range(k))
