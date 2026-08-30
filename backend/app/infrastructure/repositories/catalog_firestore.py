"""Firestore-backed catalog/config repositories (docs/05-DATABASE.md #3-4).
Runtime-verified in Phase 10 against a live emulator — see
generic_firestore.py's module docstring.
"""

from datetime import time

from google.cloud.firestore import Client

from app.domain.models import (
    Class,
    LessonRequirement,
    Room,
    RoomStatus,
    SchoolDay,
    Subject,
    Teacher,
    TimePeriod,
    TimePeriodKind,
    Weekday,
)
from app.infrastructure.repositories.generic_firestore import FirestoreRepository


def _teacher_to_document(teacher: Teacher) -> dict[str, object]:
    return {
        "schoolId": teacher.school_id,
        "name": teacher.name,
        "email": teacher.email,
        "subjectIds": sorted(teacher.subject_ids),
        "maxWeeklyLoad": teacher.max_weekly_load,
        "maxConsecutive": teacher.max_consecutive,
    }


def _teacher_from_document(doc_id: str, data: dict[str, object]) -> Teacher:
    return Teacher(
        id=doc_id,
        school_id=str(data["schoolId"]),
        name=str(data["name"]),
        email=str(data["email"]),
        subject_ids=frozenset(data.get("subjectIds", [])),  # type: ignore[arg-type]
        max_weekly_load=int(data.get("maxWeeklyLoad", 30)),  # type: ignore[arg-type]
        max_consecutive=int(data.get("maxConsecutive", 4)),  # type: ignore[arg-type]
    )


def build_teacher_repository(client: Client) -> FirestoreRepository[Teacher]:
    return FirestoreRepository(
        client,
        collection_name="teachers",
        to_document=_teacher_to_document,
        from_document=_teacher_from_document,
    )


def _class_to_document(class_: Class) -> dict[str, object]:
    return {
        "schoolId": class_.school_id,
        "name": class_.name,
        "grade": class_.grade,
        "studentCount": class_.student_count,
        "homeRoomId": class_.home_room_id,
    }


def _class_from_document(doc_id: str, data: dict[str, object]) -> Class:
    return Class(
        id=doc_id,
        school_id=str(data["schoolId"]),
        name=str(data["name"]),
        grade=int(data["grade"]),  # type: ignore[arg-type]
        student_count=int(data["studentCount"]),  # type: ignore[arg-type]
        home_room_id=data.get("homeRoomId"),  # type: ignore[arg-type]
    )


def build_class_repository(client: Client) -> FirestoreRepository[Class]:
    return FirestoreRepository(
        client,
        collection_name="classes",
        to_document=_class_to_document,
        from_document=_class_from_document,
    )


def _subject_to_document(subject: Subject) -> dict[str, object]:
    return {
        "schoolId": subject.school_id,
        "name": subject.name,
        "code": subject.code,
        "requiredCapability": subject.required_capability,
        "maxDailyOccurrences": subject.max_daily_occurrences,
        "minSpacingDays": subject.min_spacing_days,
    }


def _subject_from_document(doc_id: str, data: dict[str, object]) -> Subject:
    return Subject(
        id=doc_id,
        school_id=str(data["schoolId"]),
        name=str(data["name"]),
        code=str(data["code"]),
        required_capability=data.get("requiredCapability"),  # type: ignore[arg-type]
        max_daily_occurrences=int(data.get("maxDailyOccurrences", 1)),  # type: ignore[arg-type]
        min_spacing_days=int(data.get("minSpacingDays", 0)),  # type: ignore[arg-type]
    )


def build_subject_repository(client: Client) -> FirestoreRepository[Subject]:
    return FirestoreRepository(
        client,
        collection_name="subjects",
        to_document=_subject_to_document,
        from_document=_subject_from_document,
    )


def _room_to_document(room: Room) -> dict[str, object]:
    return {
        "schoolId": room.school_id,
        "name": room.name,
        "capacity": room.capacity,
        "roomType": room.room_type,
        "capabilities": sorted(room.capabilities),
        "status": room.status.value,
    }


def _room_from_document(doc_id: str, data: dict[str, object]) -> Room:
    return Room(
        id=doc_id,
        school_id=str(data["schoolId"]),
        name=str(data["name"]),
        capacity=int(data["capacity"]),  # type: ignore[arg-type]
        room_type=str(data["roomType"]),
        capabilities=frozenset(data.get("capabilities", [])),  # type: ignore[arg-type]
        status=RoomStatus(data.get("status", RoomStatus.ACTIVE.value)),  # type: ignore[arg-type]
    )


def build_room_repository(client: Client) -> FirestoreRepository[Room]:
    return FirestoreRepository(
        client,
        collection_name="rooms",
        to_document=_room_to_document,
        from_document=_room_from_document,
    )


def _school_day_to_document(day: SchoolDay) -> dict[str, object]:
    return {"schoolId": day.school_id, "weekday": day.weekday.value, "isActive": day.is_active}


def _school_day_from_document(doc_id: str, data: dict[str, object]) -> SchoolDay:
    return SchoolDay(
        id=doc_id,
        school_id=str(data["schoolId"]),
        weekday=Weekday(data["weekday"]),  # type: ignore[arg-type]
        is_active=bool(data["isActive"]),
    )


def build_school_day_repository(client: Client) -> FirestoreRepository[SchoolDay]:
    return FirestoreRepository(
        client,
        collection_name="schoolDays",
        to_document=_school_day_to_document,
        from_document=_school_day_from_document,
    )


def _time_period_to_document(period: TimePeriod) -> dict[str, object]:
    return {
        "schoolId": period.school_id,
        "index": period.index,
        "startTime": period.start_time.isoformat(timespec="minutes"),
        "endTime": period.end_time.isoformat(timespec="minutes"),
        "kind": period.kind.value,
    }


def _time_period_from_document(doc_id: str, data: dict[str, object]) -> TimePeriod:
    return TimePeriod(
        id=doc_id,
        school_id=str(data["schoolId"]),
        index=int(data["index"]),  # type: ignore[arg-type]
        start_time=time.fromisoformat(str(data["startTime"])),
        end_time=time.fromisoformat(str(data["endTime"])),
        kind=TimePeriodKind(data["kind"]),  # type: ignore[arg-type]
    )


def build_time_period_repository(client: Client) -> FirestoreRepository[TimePeriod]:
    return FirestoreRepository(
        client,
        collection_name="timePeriods",
        to_document=_time_period_to_document,
        from_document=_time_period_from_document,
    )


def _lesson_requirement_to_document(requirement: LessonRequirement) -> dict[str, object]:
    return {
        "schoolId": requirement.school_id,
        "classId": requirement.class_id,
        "subjectId": requirement.subject_id,
        "weeklyPeriods": requirement.weekly_periods,
        "requiredCapability": requirement.required_capability,
    }


def _lesson_requirement_from_document(doc_id: str, data: dict[str, object]) -> LessonRequirement:
    return LessonRequirement(
        id=doc_id,
        school_id=str(data["schoolId"]),
        class_id=str(data["classId"]),
        subject_id=str(data["subjectId"]),
        weekly_periods=int(data["weeklyPeriods"]),  # type: ignore[arg-type]
        required_capability=data.get("requiredCapability"),  # type: ignore[arg-type]
    )


def build_lesson_requirement_repository(client: Client) -> FirestoreRepository[LessonRequirement]:
    return FirestoreRepository(
        client,
        collection_name="lessonRequirements",
        to_document=_lesson_requirement_to_document,
        from_document=_lesson_requirement_from_document,
    )
