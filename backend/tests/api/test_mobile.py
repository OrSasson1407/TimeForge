"""The two endpoints the mobile client depends on: a teacher's own
published timetable, and push-device registration."""

from datetime import time

from app.domain.models import (
    Class,
    LessonRequirement,
    Room,
    School,
    SchoolDay,
    Subject,
    Teacher,
    TimePeriod,
    TimePeriodKind,
    Weekday,
)
from app.domain.models.device import DevicePlatform, DeviceToken
from tests.api.conftest import ApiFixtures


def _seed_school(api: ApiFixtures) -> None:
    api.schools.save(School(id="s1", name="Riverside High", timezone="UTC"))
    api.school_days.save(
        "s1", SchoolDay(id="day_mon", school_id="s1", weekday=Weekday.MONDAY, is_active=True)
    )
    api.time_periods.save(
        "s1",
        TimePeriod(
            id="p1",
            school_id="s1",
            index=0,
            start_time=time(8, 0),
            end_time=time(8, 45),
            kind=TimePeriodKind.LESSON,
        ),
    )
    api.classes.save("s1", Class(id="c1", school_id="s1", name="7A", grade=7, student_count=20))
    api.subjects.save("s1", Subject(id="MATH", school_id="s1", name="Mathematics", code="MATH"))
    api.teachers.save(
        "s1",
        Teacher(
            id="t1",
            school_id="s1",
            name="Dana",
            email="dana@example.com",
            subject_ids=frozenset({"MATH"}),
        ),
    )
    api.rooms.save(
        "s1", Room(id="r1", school_id="s1", name="Room 1", capacity=30, room_type="STANDARD")
    )
    api.lesson_requirements.save(
        "s1",
        LessonRequirement(
            id="req1", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=1
        ),
    )


def _generate_and_publish(api: ApiFixtures) -> str:
    generated = api.client.post("/schedules/generate?school_id=s1", json={"request_id": "r1"})
    version_id = generated.json()["version"]["id"]
    api.client.post(
        f"/schedules/versions/{version_id}/publish?school_id=s1",
        json={"expected_version_tag": 0},
    )
    return version_id


def test_my_timetable_is_empty_before_anything_is_published(api: ApiFixtures) -> None:
    _seed_school(api)
    api.teacher(school_id="s1", teacher_id="t1")

    response = api.client.get("/schedules/my-timetable?school_id=s1")

    assert response.status_code == 200
    assert response.json() == {"version_id": None, "entries": []}


def test_my_timetable_returns_denormalized_names_not_ids(api: ApiFixtures) -> None:
    """The whole point of this endpoint for a phone: one request that is
    renderable offline, with no follow-up catalog lookups."""
    _seed_school(api)
    api.admin(school_id="s1")
    version_id = _generate_and_publish(api)
    api.teacher(school_id="s1", teacher_id="t1")

    body = api.client.get("/schedules/my-timetable?school_id=s1").json()

    assert body["version_id"] == version_id
    assert len(body["entries"]) == 1
    entry = body["entries"][0]
    assert entry["class_name"] == "7A"
    assert entry["room_name"] == "Room 1"
    assert entry["subject_code"] == "MATH"
    assert entry["subject_name"] == "Mathematics"
    assert entry["weekday"] == "MONDAY"
    assert entry["start_time"] == "08:00:00"


def test_my_timetable_only_shows_the_callers_own_lessons(api: ApiFixtures) -> None:
    _seed_school(api)
    api.admin(school_id="s1")
    _generate_and_publish(api)
    # A teacher with no assignments in the published version.
    api.teacher(school_id="s1", user_id="other_teacher", teacher_id="t_other")

    body = api.client.get("/schedules/my-timetable?school_id=s1").json()

    assert body["entries"] == []


def test_an_admin_without_a_teacher_record_gets_an_empty_timetable(api: ApiFixtures) -> None:
    _seed_school(api)
    api.admin(school_id="s1")
    _generate_and_publish(api)

    body = api.client.get("/schedules/my-timetable?school_id=s1").json()

    assert body["entries"] == []


def test_registering_a_device_is_bound_to_the_caller(api: ApiFixtures) -> None:
    """The stored token takes its user and school from the verified session,
    never from the request body."""
    teacher = api.teacher(school_id="s1", teacher_id="t1")

    response = api.client.post(
        "/notifications/devices", json={"token": "fcm-abc", "platform": "ANDROID"}
    )

    assert response.status_code == 201
    stored = api.devices.get("fcm-abc")
    assert stored is not None
    assert stored.user_id == teacher.id
    assert stored.school_id == "s1"
    assert stored.platform is DevicePlatform.ANDROID


def test_registering_the_same_token_twice_does_not_duplicate(api: ApiFixtures) -> None:
    api.teacher(school_id="s1", teacher_id="t1")

    api.client.post("/notifications/devices", json={"token": "fcm-abc", "platform": "IOS"})
    api.client.post("/notifications/devices", json={"token": "fcm-abc", "platform": "IOS"})

    assert len(api.devices.list_for_school("s1")) == 1


def test_a_user_cannot_unregister_someone_elses_device(api: ApiFixtures) -> None:
    api.devices.save(
        DeviceToken(
            token="someone-elses",  # noqa: S106 -- an FCM device token, not a password
            user_id="a_different_user",
            school_id="s1",
            platform=DevicePlatform.IOS,
        )
    )
    api.teacher(school_id="s1", teacher_id="t1")

    response = api.client.delete("/notifications/devices/someone-elses")

    # Reports success either way so it cannot be used to probe which tokens
    # exist — but the token is still there.
    assert response.status_code == 200
    assert api.devices.get("someone-elses") is not None


def test_a_user_can_unregister_their_own_device(api: ApiFixtures) -> None:
    api.teacher(school_id="s1", teacher_id="t1")
    api.client.post("/notifications/devices", json={"token": "mine", "platform": "IOS"})

    api.client.delete("/notifications/devices/mine")

    assert api.devices.get("mine") is None


def test_publishing_pushes_to_every_registered_device(api: ApiFixtures) -> None:
    _seed_school(api)
    api.teacher(school_id="s1", teacher_id="t1")
    api.client.post("/notifications/devices", json={"token": "phone-1", "platform": "IOS"})
    api.admin(school_id="s1")

    _generate_and_publish(api)

    assert len(api.push_sender.sent) == 1
    tokens, title, body = api.push_sender.sent[0]
    assert tokens == ["phone-1"]
    assert title == "Timetable updated"
    assert "Riverside High" in body


def test_a_draft_edit_does_not_push(api: ApiFixtures) -> None:
    """Only publication notifies — pushing on every draft move would train
    people to ignore the notifications entirely."""
    _seed_school(api)
    api.teacher(school_id="s1", teacher_id="t1")
    api.client.post("/notifications/devices", json={"token": "phone-1", "platform": "IOS"})
    api.admin(school_id="s1")

    generated = api.client.post("/schedules/generate?school_id=s1", json={"request_id": "r1"})
    version_id = generated.json()["version"]["id"]
    assignment = api.client.get(
        f"/schedules/versions/{version_id}/assignments?school_id=s1"
    ).json()[0]
    api.client.post(
        f"/schedules/versions/{version_id}/apply-move?school_id=s1",
        json={
            "assignment_id": assignment["id"],
            "teacher_id": assignment["teacher_id"],
            "room_id": assignment["room_id"],
            "day_id": assignment["day_id"],
            "time_period_id": assignment["time_period_id"],
            "expected_version_tag": 0,
        },
    )

    assert api.push_sender.sent == []


def test_permanently_invalid_tokens_are_pruned_after_a_push(api: ApiFixtures) -> None:
    _seed_school(api)
    api.teacher(school_id="s1", teacher_id="t1")
    api.client.post("/notifications/devices", json={"token": "dead-phone", "platform": "IOS"})
    api.push_sender.invalid_tokens = {"dead-phone"}
    api.admin(school_id="s1")

    _generate_and_publish(api)

    assert api.devices.get("dead-phone") is None
