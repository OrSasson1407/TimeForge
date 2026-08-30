"""Seed a realistic demo school into Firestore/the Auth emulator
(docs/02-PRD.md §10 "Seed data for a realistic demo school";
docs/06-TECH_STACK.md's `scripts/seed.py` promise).

Reuses the "Small" benchmark scenario (`scripts/scenario_factory.py`) as
the demo data rather than a second, hand-maintained dataset — the master
prompt's "no unrealistic random data that produces trivial schedules"
warning applies to a demo just as much as a benchmark, and Small is already
calibrated to be genuinely, non-trivially schedulable
(docs/03-ARCHITECTURE.md #30). `build_demo_school_subjects` adds real
`Subject` catalog entities on top — the benchmark scenarios don't need them
(the solver only cares about subject_id strings), but the Subjects
management screen does.

Also creates one demo Administrator account, via the Firebase Auth Admin
SDK (works against the Auth emulator) plus a matching `users/{uid}`
Firestore document (docs/05-DATABASE.md #3) — so the printed sign-in
credentials are immediately usable, not a manual follow-up step.

Refuses to run unless FIRESTORE_EMULATOR_HOST or FIREBASE_AUTH_EMULATOR_HOST
is set, so it can never accidentally write demo data into a real
production Firebase project.

Usage (from backend/, against a running `firebase emulators:start`):
    uv run python -m scripts.seed
    uv run python -m scripts.seed --admin-email dana@timeforge.demo --admin-password change-me-123
"""

import argparse
import sys

from firebase_admin import auth as firebase_auth

from app.core.config import get_settings
from app.domain.models import Subject, User, UserRole
from app.infrastructure.firebase.client import get_auth_client, get_firestore_client
from app.infrastructure.repositories import (
    FirestoreAvailabilityRepository,
    FirestoreSchoolRepository,
    FirestoreUserRepository,
    build_class_repository,
    build_lesson_requirement_repository,
    build_room_repository,
    build_school_day_repository,
    build_subject_repository,
    build_teacher_repository,
    build_time_period_repository,
)
from scripts.scenario_factory import SUBJECT_CATALOG, small_scenario

DEFAULT_ADMIN_EMAIL = "admin@timeforge.demo"
DEFAULT_ADMIN_PASSWORD = "TimeForgeDemo123!"  # noqa: S105 -- a documented local-emulator-only demo credential, not a real secret


def build_demo_school_subjects(school_id: str) -> list[Subject]:
    """The one place `SUBJECT_CATALOG` becomes real `Subject` entities —
    reused so the seeded Subjects screen and the LessonRequirements the
    scenario already generates (by subject *code*) never disagree."""
    return [
        Subject(id=code, school_id=school_id, name=name, code=code, required_capability=capability)
        for code, name, _weekly_periods, capability in SUBJECT_CATALOG
    ]


def _ensure_emulator_configured() -> None:
    settings = get_settings()
    if not (settings.firestore_emulator_host or settings.firebase_auth_emulator_host):
        print(
            "Refusing to seed: neither FIRESTORE_EMULATOR_HOST nor "
            "FIREBASE_AUTH_EMULATOR_HOST is set. This script only ever "
            "writes to a local emulator, never a real Firebase project — "
            "set one of those environment variables (see .env.example) and "
            "run `firebase emulators:start` first.",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _ensure_admin_user(*, school_id: str, email: str, password: str) -> str:
    """Idempotent: reuses the existing Auth user if this script has already
    been run against the same emulator, rather than erroring."""
    auth_client = get_auth_client()
    try:
        record = auth_client.get_user_by_email(email)
    except firebase_auth.UserNotFoundError:
        record = auth_client.create_user(email=email, password=password)

    FirestoreUserRepository(get_firestore_client()).save(
        User(
            id=record.uid,
            role=UserRole.ADMIN,
            school_id=school_id,
            display_name="Demo Administrator",
            email_verified=True,
        )
    )
    return record.uid


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin-email", default=DEFAULT_ADMIN_EMAIL)
    parser.add_argument("--admin-password", default=DEFAULT_ADMIN_PASSWORD)
    args = parser.parse_args()

    _ensure_emulator_configured()

    scenario = small_scenario()
    subjects = build_demo_school_subjects(scenario.school.id)
    client = get_firestore_client()

    FirestoreSchoolRepository(client).save(scenario.school)

    school_day_repository = build_school_day_repository(client)
    for day in scenario.school_days:
        school_day_repository.save(scenario.school.id, day)

    time_period_repository = build_time_period_repository(client)
    for period in scenario.time_periods:
        time_period_repository.save(scenario.school.id, period)

    subject_repository = build_subject_repository(client)
    for subject in subjects:
        subject_repository.save(scenario.school.id, subject)

    teacher_repository = build_teacher_repository(client)
    for teacher in scenario.problem.teachers:
        teacher_repository.save(scenario.school.id, teacher)

    class_repository = build_class_repository(client)
    for class_ in scenario.problem.classes:
        class_repository.save(scenario.school.id, class_)

    room_repository = build_room_repository(client)
    for room in scenario.problem.rooms:
        room_repository.save(scenario.school.id, room)

    requirement_repository = build_lesson_requirement_repository(client)
    for requirement in scenario.problem.requirements:
        requirement_repository.save(scenario.school.id, requirement)

    availability_repository = FirestoreAvailabilityRepository(client)
    for record in scenario.problem.availability:
        availability_repository.save(scenario.school.id, record)

    admin_uid = _ensure_admin_user(
        school_id=scenario.school.id, email=args.admin_email, password=args.admin_password
    )

    print(
        f"Seeded demo school {scenario.school.id!r}: "
        f"{len(scenario.problem.teachers)} teachers, {len(scenario.problem.classes)} classes, "
        f"{len(subjects)} subjects, {len(scenario.problem.rooms)} rooms, "
        f"{len(scenario.problem.requirements)} lesson requirements, "
        f"{len(scenario.problem.availability)} availability records.\n"
        f"Admin sign-in: {args.admin_email} / {args.admin_password} (uid {admin_uid}).\n"
        "No schedule has been generated yet — sign in and use Generate to "
        "produce the first draft, matching the demonstration scenario in "
        "docs/03-ARCHITECTURE.md."
    )


if __name__ == "__main__":
    main()
