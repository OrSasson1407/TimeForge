import pytest

from app.domain.scheduling.infeasibility import InfeasibilityResult
from app.domain.scheduling.result import ScheduleResult, SolverStatus


def test_valid_result_defaults() -> None:
    result = ScheduleResult(status=SolverStatus.VALID)

    assert result.is_valid is True
    assert result.assignments == ()


def test_infeasible_result_requires_a_diagnosis() -> None:
    with pytest.raises(ValueError, match="infeasibility report"):
        ScheduleResult(status=SolverStatus.INFEASIBLE)


def test_infeasible_result_with_diagnosis_is_accepted() -> None:
    result = ScheduleResult(
        status=SolverStatus.INFEASIBLE, infeasibility=InfeasibilityResult(note="no solution")
    )

    assert result.is_valid is False


def test_failed_result_requires_an_error_message() -> None:
    with pytest.raises(ValueError, match="error message"):
        ScheduleResult(status=SolverStatus.FAILED)
