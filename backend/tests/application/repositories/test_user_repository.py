from app.domain.models import User, UserRole
from tests.support.fakes import FakeUserRepository


def test_save_then_get_round_trips() -> None:
    repo = FakeUserRepository()
    user = User(id="u1", role=UserRole.ADMIN, school_id="s1", display_name="Dana")

    repo.save(user)

    assert repo.get("u1") == user


def test_get_returns_none_when_absent() -> None:
    repo = FakeUserRepository()

    assert repo.get("nonexistent") is None
