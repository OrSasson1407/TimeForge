from tests.api.conftest import ApiFixtures


def test_me_returns_the_current_user(api: ApiFixtures) -> None:
    user = api.teacher(user_id="teacher_user_1", teacher_id="t1")

    response = api.client.get("/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user.id
    assert body["role"] == "TEACHER"
    assert body["teacher_id"] == "t1"


def test_me_without_a_token_is_401(api: ApiFixtures) -> None:
    response = api.client.get("/auth/me")

    assert response.status_code == 401
