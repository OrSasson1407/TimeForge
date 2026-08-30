"""Full disruption -> repair workflow smoke test (docs/04-DESIGN.md #17),
through real HTTP requests: generate -> publish -> report a disruption ->
verify the repaired draft version and the recorded disruption event.
"""

from datetime import time

from app.domain.models import (
    Class,
    LessonRequirement,
    Room,
    SchoolDay,
    Teacher,
    TimePeriod,
    TimePeriodKind,
    Weekday,
)
from tests.api.conftest import ApiFixtures


def _seed_two_teacher_school(api: ApiFixtures) -> None:
    api.school_days.save(
        "s1", SchoolDay(id="day_mon", school_id="s1", weekday=Weekday.MONDAY, is_active=True)
    )
    api.school_days.save(
        "s1", SchoolDay(id="day_tue", school_id="s1", weekday=Weekday.TUESDAY, is_active=True)
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
    api.time_periods.save(
        "s1",
        TimePeriod(
            id="p2",
            school_id="s1",
            index=1,
            start_time=time(8, 45),
            end_time=time(9, 30),
            kind=TimePeriodKind.LESSON,
        ),
    )
    api.classes.save("s1", Class(id="c1", school_id="s1", name="7A", grade=7, student_count=20))
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
    api.teachers.save(
        "s1",
        Teacher(
            id="t2",
            school_id="s1",
            name="Noa",
            email="noa@example.com",
            subject_ids=frozenset({"MATH"}),
        ),
    )
    api.rooms.save(
        "s1", Room(id="r1", school_id="s1", name="Room 1", capacity=30, room_type="STANDARD")
    )
    api.lesson_requirements.save(
        "s1",
        LessonRequirement(
            id="req1", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=2
        ),
    )


def test_full_reschedule_workflow(api: ApiFixtures) -> None:
    _seed_two_teacher_school(api)
    api.admin()

    generate_response = api.client.post(
        "/schedules/generate?school_id=s1", json={"request_id": "gen-1"}
    )
    assert generate_response.status_code == 200
    version_id = generate_response.json()["version"]["id"]

    publish_response = api.client.post(
        f"/schedules/versions/{version_id}/publish?school_id=s1", json={"expected_version_tag": 0}
    )
    assert publish_response.status_code == 200

    assignments = api.client.get(
        f"/schedules/versions/{version_id}/assignments?school_id=s1"
    ).json()
    disrupted = assignments[0]

    reschedule_response = api.client.post(
        "/schedules/reschedule?school_id=s1",
        json={
            "request_id": "resched-1",
            "event_type": "TEACHER_UNAVAILABLE",
            "target_entity_id": disrupted["teacher_id"],
            "affected_slots": [
                {"day_id": disrupted["day_id"], "time_period_id": disrupted["time_period_id"]}
            ],
            "reason": "Teacher called in sick",
        },
    )
    assert reschedule_response.status_code == 200
    body = reschedule_response.json()
    assert body["status"] == "REPAIRED"
    assert body["version"] is not None
    assert body["version"]["parent_version_id"] == version_id
    assert body["version"]["status"] == "DRAFT"
    assert body["disruption_cost"] is not None

    # Idempotent replay: same request_id never repairs twice.
    replay_response = api.client.post(
        "/schedules/reschedule?school_id=s1",
        json={
            "request_id": "resched-1",
            "event_type": "TEACHER_UNAVAILABLE",
            "target_entity_id": disrupted["teacher_id"],
            "affected_slots": [
                {"day_id": disrupted["day_id"], "time_period_id": disrupted["time_period_id"]}
            ],
            "reason": "Teacher called in sick",
        },
    )
    assert replay_response.status_code == 200
    assert replay_response.json()["version"]["id"] == body["version"]["id"]

    events_response = api.client.get("/schedules/rescheduling-events?school_id=s1")
    assert events_response.status_code == 200
    events = events_response.json()
    assert len(events) == 1
    assert events[0]["type"] == "TEACHER_UNAVAILABLE"
    assert events[0]["target_entity_id"] == disrupted["teacher_id"]


def test_reschedule_is_admin_only(api: ApiFixtures) -> None:
    _seed_two_teacher_school(api)
    api.teacher()

    response = api.client.post(
        "/schedules/reschedule?school_id=s1",
        json={
            "request_id": "resched-1",
            "event_type": "TEACHER_UNAVAILABLE",
            "target_entity_id": "t1",
            "affected_slots": [{"day_id": "day_mon", "time_period_id": "p1"}],
            "reason": "Teacher called in sick",
        },
    )

    assert response.status_code == 403


def test_reschedule_without_a_published_version_is_rejected(api: ApiFixtures) -> None:
    _seed_two_teacher_school(api)
    api.admin()

    response = api.client.post(
        "/schedules/reschedule?school_id=s1",
        json={
            "request_id": "resched-1",
            "event_type": "TEACHER_UNAVAILABLE",
            "target_entity_id": "t1",
            "affected_slots": [{"day_id": "day_mon", "time_period_id": "p1"}],
            "reason": "Teacher called in sick",
        },
    )

    assert response.status_code == 400
