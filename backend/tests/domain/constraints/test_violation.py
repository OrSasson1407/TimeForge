import pytest

from app.domain.constraints.violation import Severity, Violation


def test_violation_defaults_to_empty_involved_entities() -> None:
    violation = Violation(constraint_id="HC-001", severity=Severity.ERROR, message="conflict")

    assert violation.involved_entities == ()


def test_violation_rejects_empty_constraint_id() -> None:
    with pytest.raises(ValueError, match="constraint_id"):
        Violation(constraint_id="", severity=Severity.ERROR, message="conflict")


def test_violation_rejects_empty_message() -> None:
    with pytest.raises(ValueError, match="message"):
        Violation(constraint_id="HC-001", severity=Severity.ERROR, message="")
