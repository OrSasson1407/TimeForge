"""BR-003 ownership authorization (docs/03-ARCHITECTURE.md #23-24): a
teacher may write their own availability but nobody else's; an admin may
write anyone's.
"""

from tests.api.conftest import ApiFixtures


def test_teacher_can_submit_their_own_availability(api: ApiFixtures) -> None:
    api.teacher(teacher_id="t1")

    response = api.client.put(
        "/availability/avail1?school_id=s1",
        json={
            "owner_type": "TEACHER",
            "owner_id": "t1",
            "time_period_id": "p1",
            "is_available": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_available"] is False


def test_teacher_cannot_submit_another_teachers_availability(api: ApiFixtures) -> None:
    api.teacher(teacher_id="t1")

    response = api.client.put(
        "/availability/avail1?school_id=s1",
        json={"owner_type": "TEACHER", "owner_id": "t2", "time_period_id": "p1"},
    )

    assert response.status_code == 403


def test_teacher_cannot_submit_class_availability(api: ApiFixtures) -> None:
    api.teacher(teacher_id="t1")

    response = api.client.put(
        "/availability/avail1?school_id=s1",
        json={"owner_type": "CLASS", "owner_id": "c1", "time_period_id": "p1"},
    )

    assert response.status_code == 403


def test_admin_can_submit_any_availability(api: ApiFixtures) -> None:
    api.admin()

    response = api.client.put(
        "/availability/avail1?school_id=s1",
        json={"owner_type": "TEACHER", "owner_id": "t1", "time_period_id": "p1"},
    )

    assert response.status_code == 200


def test_list_availability_can_filter_by_owner(api: ApiFixtures) -> None:
    api.admin()
    api.client.put(
        "/availability/a1?school_id=s1",
        json={"owner_type": "TEACHER", "owner_id": "t1", "time_period_id": "p1"},
    )
    api.client.put(
        "/availability/a2?school_id=s1",
        json={"owner_type": "TEACHER", "owner_id": "t2", "time_period_id": "p1"},
    )

    response = api.client.get("/availability?school_id=s1&owner_type=TEACHER&owner_id=t1")

    assert [a["id"] for a in response.json()] == ["a1"]
