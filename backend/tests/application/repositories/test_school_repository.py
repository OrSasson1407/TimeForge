from app.domain.models import School
from tests.support.fakes import FakeSchoolRepository


def test_save_then_get_round_trips() -> None:
    repo = FakeSchoolRepository()
    school = School(id="s1", name="Northgate High", timezone="Asia/Jerusalem")

    repo.save(school)

    assert repo.get("s1") == school


def test_get_returns_none_when_absent() -> None:
    repo = FakeSchoolRepository()

    assert repo.get("nonexistent") is None


def test_list_returns_every_saved_school() -> None:
    repo = FakeSchoolRepository()
    repo.save(School(id="s1", name="A", timezone="Asia/Jerusalem"))
    repo.save(School(id="s2", name="B", timezone="Asia/Jerusalem"))

    assert {s.id for s in repo.list()} == {"s1", "s2"}
