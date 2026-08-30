from app.domain.models import LessonRequirement
from app.domain.scheduling import InfeasibilityAnalyzer
from app.domain.scheduling.infeasibility import BottleneckReport, InfeasibilityResult

from .conftest import build_problem


def test_bottleneck_report_shortage_is_never_negative() -> None:
    report = BottleneckReport(
        subject_id="MATH",
        required_capability=None,
        required=5,
        available=10,
        affected_class_ids=(),
        affected_teacher_ids=(),
    )

    assert report.shortage == 0


def test_bottleneck_report_shortage_when_under_provisioned() -> None:
    report = BottleneckReport(
        subject_id="CHEM",
        required_capability="CHEMISTRY_LAB",
        required=10,
        available=4,
        affected_class_ids=("c1",),
        affected_teacher_ids=("t1",),
    )

    assert report.shortage == 6


def test_infeasibility_result_default_is_feasible() -> None:
    assert InfeasibilityResult().is_infeasible is False


def test_analyzer_finds_no_bottleneck_for_an_easy_problem(
    two_days, three_periods, two_classes, two_teachers, two_rooms, math_requirement
) -> None:
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=two_teachers,
        rooms=two_rooms,
        requirements=[math_requirement],
    )

    result = InfeasibilityAnalyzer(problem).analyze()

    assert result.is_infeasible is False


def test_analyzer_reports_a_shortage_when_no_room_has_the_capability(
    two_days, three_periods, two_classes, two_teachers, two_rooms
) -> None:
    lab_requirement = LessonRequirement(
        id="req_c1_chem",
        school_id="s1",
        class_id="c1",
        subject_id="CHEM",
        weekly_periods=3,
        required_capability="CHEMISTRY_LAB",
    )
    problem = build_problem(
        days=two_days,
        periods=three_periods,
        classes=two_classes,
        teachers=[
            t.__class__(
                id=t.id, school_id="s1", name=t.name, email=t.email, subject_ids=frozenset({"CHEM"})
            )
            for t in two_teachers
        ],
        rooms=two_rooms,  # neither has CHEMISTRY_LAB
        requirements=[lab_requirement],
    )

    result = InfeasibilityAnalyzer(problem).analyze()

    assert result.is_infeasible is True
    assert len(result.bottlenecks) == 1
    bottleneck = result.bottlenecks[0]
    assert bottleneck.subject_id == "CHEM"
    assert bottleneck.required_capability == "CHEMISTRY_LAB"
    assert bottleneck.required == 3
    assert bottleneck.available == 0
    assert bottleneck.shortage == 3
    assert bottleneck.affected_class_ids == ("c1",)
