from tests.api.conftest import ApiFixtures


def test_get_scheduling_config_returns_defaults_when_unset(api: ApiFixtures) -> None:
    api.admin()

    response = api.client.get("/constraints?school_id=s1")

    assert response.status_code == 200
    body = response.json()
    assert body["timeout_seconds"] == 60.0
    assert body["soft_constraint_weights"]["SC-001"] == 1.0


def test_admin_can_update_scheduling_config(api: ApiFixtures) -> None:
    api.admin()
    current = api.client.get("/constraints?school_id=s1").json()
    current["timeout_seconds"] = 90.0

    response = api.client.put("/constraints?school_id=s1", json=current)

    assert response.status_code == 200
    assert response.json()["timeout_seconds"] == 90.0
    assert api.client.get("/constraints?school_id=s1").json()["timeout_seconds"] == 90.0


def test_non_admin_cannot_update_scheduling_config(api: ApiFixtures) -> None:
    api.teacher()
    current = api.scheduling_config.get("s1")

    response = api.client.put(
        "/constraints?school_id=s1",
        json={
            "timeout_seconds": current.timeout_seconds,
            "random_seed": current.random_seed,
            "soft_constraint_weights": current.soft_constraint_weights,
            "initial_temperature": current.initial_temperature,
            "cooling_rate": current.cooling_rate,
            "min_temperature": current.min_temperature,
            "quality_decay_k": current.quality_decay_k,
        },
    )

    assert response.status_code == 403
