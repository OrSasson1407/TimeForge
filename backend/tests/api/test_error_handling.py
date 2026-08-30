"""The DomainError -> ErrorEnvelope exception handler (docs/03-ARCHITECTURE.md
#27, docs/04-DESIGN.md #24): every error path below is exercised through a
real endpoint, not a synthetic handler unit test, so the actual FastAPI
wiring in `app.main.create_app` is what's under test.
"""

from tests.api.conftest import ApiFixtures


def test_missing_bearer_token_is_401(api: ApiFixtures) -> None:
    response = api.client.get("/schools")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["type"] == "AuthenticationError"


def test_malformed_authorization_header_is_401(api: ApiFixtures) -> None:
    response = api.client.get("/schools", headers={"Authorization": "NotBearer xyz"})

    assert response.status_code == 401


def test_non_admin_write_is_403(api: ApiFixtures) -> None:
    api.teacher()

    response = api.client.put("/schools/s1", json={"name": "Demo School", "timezone": "UTC"})

    assert response.status_code == 403
    assert response.json()["error"]["type"] == "AuthorizationError"


def test_missing_entity_is_404(api: ApiFixtures) -> None:
    api.admin()

    response = api.client.get("/schools/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "NotFoundError"
