"""Tests the seed script's pure data-construction logic only
(`build_demo_school_subjects`) — `main()` itself needs a live
Firestore/Auth emulator, so it isn't covered by this unit test. It was
runtime-verified in Phase 10 by running it directly against a live
`firebase emulators:start` (see
`app/infrastructure/repositories/generic_firestore.py`'s module
docstring).
"""

from scripts.scenario_factory import SUBJECT_CATALOG, small_scenario
from scripts.seed import build_demo_school_subjects


def test_builds_one_subject_per_catalog_entry() -> None:
    subjects = build_demo_school_subjects("school_demo")

    assert len(subjects) == len(SUBJECT_CATALOG)
    assert {s.code for s in subjects} == {code for code, *_ in SUBJECT_CATALOG}
    assert all(s.school_id == "school_demo" for s in subjects)


def test_subject_required_capability_matches_the_catalog() -> None:
    subjects = build_demo_school_subjects("school_demo")
    by_code = {s.code: s for s in subjects}

    for code, _name, _weekly_periods, capability in SUBJECT_CATALOG:
        assert by_code[code].required_capability == capability


def test_every_scenario_lesson_requirement_references_a_seeded_subject() -> None:
    """The scenario's `LessonRequirement.subject_id` values are catalog
    codes — this is what actually proves the seeded Subjects and the
    seeded LessonRequirements never disagree about what subjects exist."""
    scenario = small_scenario()
    subjects = build_demo_school_subjects(scenario.school.id)
    subject_codes = {s.code for s in subjects}

    for requirement in scenario.problem.requirements:
        assert requirement.subject_id in subject_codes
