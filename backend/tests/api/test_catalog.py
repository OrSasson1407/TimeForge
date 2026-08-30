"""Exercises `build_crud_router` (docs/03-ARCHITECTURE.md #26) through one
representative entity (Teacher) end-to-end over real HTTP — in particular,
this is what proves the `upsert_entity.__annotations__["body"] = upsert_model`
trick in `app/api/crud_router.py` actually resolves to the concrete
`TeacherUpsertRequest` model at request-validation time, not just that it
type-checks statically.
"""

from tests.api.conftest import ApiFixtures


def test_admin_can_upsert_list_and_get_a_teacher(api: ApiFixtures) -> None:
    api.admin()

    put_response = api.client.put(
        "/teachers/t1?school_id=s1",
        json={"name": "Dana Cohen", "email": "dana@example.com", "subject_ids": ["MATH"]},
    )
    assert put_response.status_code == 200
    body = put_response.json()
    assert body["id"] == "t1"
    assert body["name"] == "Dana Cohen"
    assert body["subject_ids"] == ["MATH"]
    assert body["max_weekly_load"] == 30  # default

    list_response = api.client.get("/teachers?school_id=s1")
    assert [t["id"] for t in list_response.json()] == ["t1"]

    get_response = api.client.get("/teachers/t1?school_id=s1")
    assert get_response.status_code == 200
    assert get_response.json()["email"] == "dana@example.com"


def test_upsert_rejects_an_invalid_body(api: ApiFixtures) -> None:
    api.admin()

    response = api.client.put(
        "/teachers/t1?school_id=s1", json={"name": "", "email": "dana@example.com"}
    )

    assert response.status_code == 422  # Pydantic schema validation, not a DomainError


def test_get_unknown_teacher_is_404(api: ApiFixtures) -> None:
    api.admin()

    response = api.client.get("/teachers/unknown?school_id=s1")

    assert response.status_code == 404


def test_non_admin_cannot_upsert_a_teacher(api: ApiFixtures) -> None:
    api.teacher()

    response = api.client.put(
        "/teachers/t1?school_id=s1", json={"name": "Dana Cohen", "email": "dana@example.com"}
    )

    assert response.status_code == 403
