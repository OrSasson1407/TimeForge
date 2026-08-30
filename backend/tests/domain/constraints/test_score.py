import math

import pytest

from app.domain.constraints.score import PenaltyContribution, Score, compute_quality


def test_penalty_contribution_rejects_negative_raw_penalty() -> None:
    with pytest.raises(ValueError, match="raw_penalty"):
        PenaltyContribution(
            constraint_id="SC-001", weight=1.0, raw_penalty=-1.0, weighted_penalty=-1.0, message="x"
        )


def test_score_rejects_negative_hard_violations() -> None:
    with pytest.raises(ValueError, match="hard_violations"):
        Score(hard_violations=-1, soft_penalty=0.0)


def test_score_rejects_negative_soft_penalty() -> None:
    with pytest.raises(ValueError, match="soft_penalty"):
        Score(hard_violations=0, soft_penalty=-1.0)


def test_score_defaults_to_empty_breakdown() -> None:
    score = Score(hard_violations=0, soft_penalty=0.0)

    assert score.breakdown == ()


def test_compute_quality_is_100_for_zero_penalty() -> None:
    assert compute_quality(soft_penalty=0.0, k=0.05, lesson_count=100) == 100.0


def test_compute_quality_decreases_as_penalty_grows() -> None:
    low = compute_quality(soft_penalty=1.0, k=0.05, lesson_count=10)
    high = compute_quality(soft_penalty=10.0, k=0.05, lesson_count=10)

    assert 0 < high < low <= 100


def test_compute_quality_is_scale_invariant_per_lesson() -> None:
    """The same AVERAGE per-lesson penalty should give the same quality
    regardless of how many lessons the school has — this is the whole
    point of normalizing by lesson_count (docs/03-ARCHITECTURE.md #30)."""
    small = compute_quality(soft_penalty=20.0, k=0.05, lesson_count=10)
    large = compute_quality(soft_penalty=200.0, k=0.05, lesson_count=100)

    assert small == pytest.approx(large)


def test_compute_quality_is_always_in_valid_range() -> None:
    quality = compute_quality(soft_penalty=1000.0, k=0.05, lesson_count=10)

    assert 0 < quality <= 100
    assert math.isfinite(quality)


def test_compute_quality_rejects_non_positive_k() -> None:
    with pytest.raises(ValueError, match="k must be"):
        compute_quality(soft_penalty=1.0, k=0.0, lesson_count=10)


def test_compute_quality_rejects_negative_penalty() -> None:
    with pytest.raises(ValueError, match="soft_penalty"):
        compute_quality(soft_penalty=-1.0, k=0.05, lesson_count=10)


def test_compute_quality_rejects_non_positive_lesson_count() -> None:
    with pytest.raises(ValueError, match="lesson_count"):
        compute_quality(soft_penalty=1.0, k=0.05, lesson_count=0)
