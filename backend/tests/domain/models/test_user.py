import pytest

from app.domain.models.enums import UserRole
from app.domain.models.user import User


def test_admin_does_not_require_teacher_id() -> None:
    user = User(id="u1", role=UserRole.ADMIN, school_id="s1", display_name="Dana")

    assert user.teacher_id is None


def test_teacher_role_requires_teacher_id() -> None:
    with pytest.raises(ValueError, match="teacher_id"):
        User(id="u2", role=UserRole.TEACHER, school_id="s1", display_name="Yossi")


def test_teacher_role_with_teacher_id_is_valid() -> None:
    user = User(
        id="u2", role=UserRole.TEACHER, school_id="s1", display_name="Yossi", teacher_id="t1"
    )

    assert user.teacher_id == "t1"
