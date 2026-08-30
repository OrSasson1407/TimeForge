"""Full scheduling-workflow smoke test (docs/03-ARCHITECTURE.md #26):
generate -> inspect -> validate a move -> apply it -> publish -> compare,
all through real HTTP requests against the FastAPI app. This is what proves
`GenerateScheduleUseCase`, `ValidateMoveUseCase`, `ApplyMoveUseCase`,
`PublishScheduleUseCase`, and `CompareVersionsUseCase` are wired correctly
end-to-end, not just individually unit-tested.
"""

from dataclasses import replace
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

_ALL_SLOTS = [("day_mon", "p1"), ("day_mon", "p2"), ("day_tue", "p1"), ("day_tue", "p2")]


def _seed_minimal_solvable_school(api: ApiFixtures) -> None:
    """One class, one teacher, one room, two weekly MATH periods across two
    days x two periods (four slots for two lessons) — deliberately small so
    the solver resolves instantly and the test stays deterministic."""
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
    api.rooms.save(
        "s1", Room(id="r1", school_id="s1", name="Room 1", capacity=30, room_type="STANDARD")
    )
    api.lesson_requirements.save(
        "s1",
        LessonRequirement(
            id="req1", school_id="s1", class_id="c1", subject_id="MATH", weekly_periods=2
        ),
    )


def test_full_schedule_workflow(api: ApiFixtures) -> None:
    _seed_minimal_solvable_school(api)
    api.admin()

    # --- generate ---
    generate_response = api.client.post(
        "/schedules/generate?school_id=s1",
        json={"request_id": "req-1", "reason": "Initial generation"},
    )
    assert generate_response.status_code == 200
    generate_body = generate_response.json()
    assert generate_body["status"] == "VALID"
    assert generate_body["version"] is not None
    version_id = generate_body["version"]["id"]
    assert generate_body["version"]["assignment_count"] == 2
    assert generate_body["version"]["score"]["hard_violations"] == 0

    # --- idempotent replay: same request_id never solves twice ---
    replay_response = api.client.post(
        "/schedules/generate?school_id=s1", json={"request_id": "req-1"}
    )
    assert replay_response.status_code == 200
    assert replay_response.json()["version"]["id"] == version_id

    # --- get schedule / list versions / get version / list assignments ---
    schedule_response = api.client.get("/schedules?school_id=s1")
    assert schedule_response.status_code == 200
    assert schedule_response.json()["active_version_id"] is None  # not published yet

    versions_response = api.client.get("/schedules/versions?school_id=s1")
    assert [v["id"] for v in versions_response.json()] == [version_id]

    version_response = api.client.get(f"/schedules/versions/{version_id}?school_id=s1")
    assert version_response.status_code == 200
    assert version_response.json()["status"] == "DRAFT"

    assignments_response = api.client.get(
        f"/schedules/versions/{version_id}/assignments?school_id=s1"
    )
    assert assignments_response.status_code == 200
    assignments = assignments_response.json()
    assert len(assignments) == 2

    target, other = assignments[0], assignments[1]
    used_slots = {
        (target["day_id"], target["time_period_id"]),
        (other["day_id"], other["time_period_id"]),
    }
    free_slot = next(s for s in _ALL_SLOTS if s not in used_slots)

    # --- validate-move: moving `target` to an unused slot is never a hard
    # conflict (only one teacher/room/class exists); it may still land a
    # soft-constraint WARNING depending on the distribution constraints, so
    # only the absence of a hard violation is asserted here. ---
    validate_response = api.client.post(
        f"/schedules/versions/{version_id}/validate-move?school_id=s1",
        json={
            "assignment_id": target["id"],
            "teacher_id": target["teacher_id"],
            "room_id": target["room_id"],
            "day_id": free_slot[0],
            "time_period_id": free_slot[1],
        },
    )
    assert validate_response.status_code == 200
    validate_body = validate_response.json()
    assert validate_body["result"] in {"VALID", "WARNING"}
    assert validate_body["violation"] is None

    # --- apply-move ---
    apply_response = api.client.post(
        f"/schedules/versions/{version_id}/apply-move?school_id=s1",
        json={
            "assignment_id": target["id"],
            "teacher_id": target["teacher_id"],
            "room_id": target["room_id"],
            "day_id": free_slot[0],
            "time_period_id": free_slot[1],
            "expected_version_tag": 0,
        },
    )
    assert apply_response.status_code == 200
    assert apply_response.json()["day_id"] == free_slot[0]
    assert apply_response.json()["time_period_id"] == free_slot[1]

    # --- a stale version_tag is rejected, even for an otherwise-valid move ---
    now_used = {free_slot, (other["day_id"], other["time_period_id"])}
    still_free_slot = next(s for s in _ALL_SLOTS if s not in now_used)
    stale_response = api.client.post(
        f"/schedules/versions/{version_id}/apply-move?school_id=s1",
        json={
            "assignment_id": target["id"],
            "teacher_id": target["teacher_id"],
            "room_id": target["room_id"],
            "day_id": still_free_slot[0],
            "time_period_id": still_free_slot[1],
            "expected_version_tag": 0,  # stale: the move above already bumped it to 1
        },
    )
    assert stale_response.status_code == 409

    # --- publish ---
    publish_response = api.client.post(
        f"/schedules/versions/{version_id}/publish?school_id=s1", json={"expected_version_tag": 1}
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "PUBLISHED"

    schedule_after_publish = api.client.get("/schedules?school_id=s1").json()
    assert schedule_after_publish["active_version_id"] == version_id

    # --- compare (a version against itself: no diff) ---
    compare_response = api.client.get(
        "/schedules/compare",
        params={"school_id": "s1", "from_version_id": version_id, "to_version_id": version_id},
    )
    assert compare_response.status_code == 200
    compare_body = compare_response.json()
    assert compare_body["added"] == []
    assert compare_body["removed"] == []
    assert compare_body["moved"] == []
    assert compare_body["unchanged_count"] == 2

    # --- the audit trail recorded both the generation and the publish ---
    audit_response = api.client.get(
        "/audit", params={"entity_type": "SCHEDULE_VERSION", "entity_id": version_id}
    )
    operations = {e["operation"] for e in audit_response.json()}
    assert "SCHEDULE_GENERATED" in operations
    assert "SCHEDULE_PUBLISHED" in operations


def test_generate_is_admin_only(api: ApiFixtures) -> None:
    _seed_minimal_solvable_school(api)
    api.teacher()

    response = api.client.post("/schedules/generate?school_id=s1", json={"request_id": "req-1"})

    assert response.status_code == 403


def test_violations_endpoint_reflects_the_persisted_state(api: ApiFixtures) -> None:
    """A freshly generated draft is hard-constraint-clean. Corrupting it
    directly at the repository (bypassing apply-move's own re-validation,
    the same way an externally-constructed state is exercised elsewhere —
    see HardConstraint.violations_in's docstring) proves the endpoint is a
    real full-state scan, not just an echo of validate-move's last check."""
    _seed_minimal_solvable_school(api)
    api.admin()

    generate_response = api.client.post(
        "/schedules/generate?school_id=s1", json={"request_id": "req-1"}
    )
    version_id = generate_response.json()["version"]["id"]

    clean_response = api.client.get(f"/schedules/versions/{version_id}/violations?school_id=s1")
    assert clean_response.status_code == 200
    assert clean_response.json() == []

    assignments = api.schedule_versions.list_assignments("s1", version_id)
    target, other = assignments[0], assignments[1]
    collided = replace(other, day_id=target.day_id, time_period_id=target.time_period_id)
    api.schedule_versions.apply_assignment_change(
        "s1", version_id, collided, expected_version_tag=0
    )

    dirty_response = api.client.get(f"/schedules/versions/{version_id}/violations?school_id=s1")
    assert dirty_response.status_code == 200
    violations = dirty_response.json()
    assert len(violations) > 0
    involved = {entity for v in violations for entity in v["involved_entities"]}
    assert target.lesson_id in involved
    assert other.lesson_id in involved
