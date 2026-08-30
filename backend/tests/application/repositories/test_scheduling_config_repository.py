from app.domain.scheduling import SchedulingConfig
from tests.support.fakes import FakeSchedulingConfigRepository


def test_get_returns_defaults_when_nothing_saved() -> None:
    repo = FakeSchedulingConfigRepository()

    config = repo.get("s1")

    assert config == SchedulingConfig()


def test_save_then_get_round_trips() -> None:
    repo = FakeSchedulingConfigRepository()
    custom = SchedulingConfig(timeout_seconds=120.0, random_seed=7)

    repo.save("s1", custom)

    assert repo.get("s1") == custom


def test_config_is_scoped_per_school() -> None:
    repo = FakeSchedulingConfigRepository()
    repo.save("s1", SchedulingConfig(timeout_seconds=120.0))

    assert repo.get("s2") == SchedulingConfig()
