from tests.api.conftest import ApiFixtures


def test_admin_can_create_and_read_a_school(api: ApiFixtures) -> None:
    api.admin()

    put_response = api.client.put(
        "/schools/s1", json={"name": "Demo School", "timezone": "Asia/Jerusalem"}
    )
    assert put_response.status_code == 200
    assert put_response.json() == {"id": "s1", "name": "Demo School", "timezone": "Asia/Jerusalem"}

    list_response = api.client.get("/schools")
    assert list_response.status_code == 200
    assert [s["id"] for s in list_response.json()] == ["s1"]

    get_response = api.client.get("/schools/s1")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Demo School"


def test_teacher_can_read_but_not_write_a_school(api: ApiFixtures) -> None:
    api.admin()
    api.client.put("/schools/s1", json={"name": "Demo School", "timezone": "UTC"})

    api.teacher()
    read_response = api.client.get("/schools/s1")
    assert read_response.status_code == 200

    write_response = api.client.put("/schools/s1", json={"name": "Renamed", "timezone": "UTC"})
    assert write_response.status_code == 403
