from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import julia_flow
from main import find_feasible_assignment


@pytest.fixture
def fresh_worker() -> Iterator[None]:
    julia_flow.close()
    yield
    julia_flow.close()


@pytest.mark.usefixtures("fresh_worker")
def test_missing_julia_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("JULIA", str(tmp_path / "missing-julia"))
    assert find_feasible_assignment([], k=0, upper_bound=0) == []
    assert find_feasible_assignment([[]], k=1, upper_bound=1) is None
    assert find_feasible_assignment([[0]], k=1, upper_bound=0) is None
    with pytest.raises(RuntimeError, match="Could not start Julia"):
        _ = find_feasible_assignment([[0]], k=1, upper_bound=1)


@pytest.mark.usefixtures("fresh_worker")
def test_missing_solver_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("JULIA_MAXFLOW_PATH", str(tmp_path / "missing-solver.jl"))
    with pytest.raises(RuntimeError, match="Julia solver not found"):
        _ = find_feasible_assignment([[0]], k=1, upper_bound=1)


@pytest.mark.usefixtures("fresh_worker")
def test_solver_failure_and_recovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    solver = tmp_path / "broken.jl"
    _ = solver.write_text('error("Intentional solver failure")\n')
    with monkeypatch.context() as settings:
        settings.setenv("JULIA_MAXFLOW_PATH", str(solver))
        with pytest.raises(RuntimeError, match="Julia max-flow solver failed"):
            _ = find_feasible_assignment([[0]], k=1, upper_bound=1)
    assert find_feasible_assignment([[0]], k=1, upper_bound=1) == [0]


def test_concurrent_calls() -> None:
    def assign(n: int) -> list[int] | None:
        return find_feasible_assignment([[0]] * n, k=1, upper_bound=n)

    with ThreadPoolExecutor(max_workers=4) as executor:
        assert list(executor.map(assign, range(1, 9))) == [[0] * n for n in range(1, 9)]
