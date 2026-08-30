from app.domain.models import Teacher
from tests.support.fakes import FakeRepository


def _teacher(**overrides: object) -> Teacher:
    defaults: dict[str, object] = {
        "id": "t1",
        "school_id": "s1",
        "name": "Yossi Cohen",
        "email": "yossi@example.com",
    }
    defaults.update(overrides)
    return Teacher(**defaults)  # type: ignore[arg-type]


def test_get_returns_none_when_absent() -> None:
    repo: FakeRepository[Teacher] = FakeRepository()

    assert repo.get("s1", "t1") is None


def test_save_then_get_round_trips() -> None:
    repo: FakeRepository[Teacher] = FakeRepository()
    teacher = _teacher()

    repo.save("s1", teacher)

    assert repo.get("s1", "t1") == teacher


def test_save_upserts_an_existing_entity() -> None:
    repo: FakeRepository[Teacher] = FakeRepository()
    repo.save("s1", _teacher(name="Original"))

    repo.save("s1", _teacher(name="Renamed"))

    assert repo.get("s1", "t1").name == "Renamed"  # type: ignore[union-attr]


def test_list_returns_only_entities_for_the_given_school() -> None:
    repo: FakeRepository[Teacher] = FakeRepository()
    repo.save("s1", _teacher(id="t1", school_id="s1"))
    repo.save("s2", _teacher(id="t2", school_id="s2"))

    assert [t.id for t in repo.list("s1")] == ["t1"]


def test_list_is_empty_for_an_unknown_school() -> None:
    repo: FakeRepository[Teacher] = FakeRepository()

    assert repo.list("nonexistent") == []
