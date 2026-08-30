import pytest

from app.core.errors import (
    AuthorizationError,
    ConcurrencyError,
    ConflictError,
    DomainError,
    InfeasibleScheduleError,
    NotFoundError,
    ReschedulingError,
    SchedulingError,
    ValidationError,
)


@pytest.mark.parametrize(
    "error_cls,expected_status",
    [
        (ValidationError, 400),
        (ConflictError, 409),
        (AuthorizationError, 403),
        (NotFoundError, 404),
        (SchedulingError, 422),
        (InfeasibleScheduleError, 422),
        (ReschedulingError, 422),
        (ConcurrencyError, 409),
    ],
)
def test_each_error_maps_to_its_documented_status_code(
    error_cls: type[DomainError], expected_status: int
) -> None:
    assert error_cls.status_code == expected_status


def test_every_error_is_a_domain_error() -> None:
    for error_cls in (
        ValidationError,
        ConflictError,
        AuthorizationError,
        NotFoundError,
        SchedulingError,
        InfeasibleScheduleError,
        ReschedulingError,
        ConcurrencyError,
    ):
        assert issubclass(error_cls, DomainError)


def test_error_carries_message_and_optional_details() -> None:
    error = NotFoundError("Teacher t1 not found", details={"teacher_id": "t1"})

    assert error.message == "Teacher t1 not found"
    assert error.details == {"teacher_id": "t1"}
    assert str(error) == "Teacher t1 not found"


def test_error_details_default_to_empty_dict() -> None:
    error = ValidationError("bad input")

    assert error.details == {}
