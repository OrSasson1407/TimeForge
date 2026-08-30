from app.domain.models import Availability, OwnerType
from tests.support.fakes import FakeAvailabilityRepository


def _record(**overrides: object) -> Availability:
    defaults: dict[str, object] = {
        "id": "a1",
        "school_id": "s1",
        "owner_type": OwnerType.TEACHER,
        "owner_id": "t1",
        "time_period_id": "p1",
        "is_available": True,
    }
    defaults.update(overrides)
    return Availability(**defaults)  # type: ignore[arg-type]


def test_list_for_owner_filters_by_owner_type_and_id() -> None:
    repo = FakeAvailabilityRepository()
    repo.save("s1", _record(id="a1", owner_type=OwnerType.TEACHER, owner_id="t1"))
    repo.save("s1", _record(id="a2", owner_type=OwnerType.TEACHER, owner_id="t2"))
    repo.save("s1", _record(id="a3", owner_type=OwnerType.CLASS, owner_id="t1"))

    results = repo.list_for_owner("s1", OwnerType.TEACHER, "t1")

    assert [r.id for r in results] == ["a1"]


def test_list_all_returns_every_record_for_the_school() -> None:
    repo = FakeAvailabilityRepository()
    repo.save("s1", _record(id="a1"))
    repo.save("s1", _record(id="a2", owner_id="t2"))
    repo.save("s2", _record(id="a3"))

    assert {r.id for r in repo.list_all("s1")} == {"a1", "a2"}
