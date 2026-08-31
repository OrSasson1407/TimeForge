"""Live-collaboration WebSocket: auth, school scoping, and presence.

Driven through Starlette's real `websocket_connect`, so the handshake,
first-message auth, and close codes are exercised for real rather than by
calling the handler directly.
"""

import pytest
from starlette.websockets import WebSocketDisconnect

from app.api.dependencies import get_user_repository
from app.infrastructure.firebase import auth as firebase_auth_module
from app.infrastructure.realtime import broadcaster, topic_for_version
from app.main import app
from tests.api.conftest import ApiFixtures

_POLICY_VIOLATION = 1008


@pytest.fixture(autouse=True)
def _fake_token_resolution(api: ApiFixtures, monkeypatch: pytest.MonkeyPatch):
    """The WebSocket route calls `resolve_user` directly (it needs to verify
    a token from a message body, not a header, so it cannot reuse the
    `get_current_user` dependency the other tests override). Stand in for
    Firebase: the token IS the uid, and it resolves through the same fake
    user repository as everything else."""

    def fake_resolve_user(token: str, user_repository):
        user = user_repository.get(token)
        if user is None:
            raise firebase_auth_module.AuthenticationError("no such user")
        if not user.is_active:
            raise firebase_auth_module.AuthenticationError("suspended")
        return user

    monkeypatch.setattr("app.api.routers.collaboration.resolve_user", fake_resolve_user)
    app.dependency_overrides[get_user_repository] = lambda: api.users
    yield


def test_a_socket_that_never_authenticates_is_closed(api: ApiFixtures) -> None:
    api.admin(school_id="s1")

    with api.client.websocket_connect("/ws/schedules/v1?school_id=s1") as socket:
        socket.send_json({"not": "a token"})
        with pytest.raises(WebSocketDisconnect) as excinfo:
            socket.receive_json()

    assert excinfo.value.code == _POLICY_VIOLATION


def test_an_unknown_token_is_rejected(api: ApiFixtures) -> None:
    api.admin(school_id="s1")

    with api.client.websocket_connect("/ws/schedules/v1?school_id=s1") as socket:
        socket.send_json({"token": "nobody"})
        with pytest.raises(WebSocketDisconnect) as excinfo:
            socket.receive_json()

    assert excinfo.value.code == _POLICY_VIOLATION


def test_a_user_cannot_join_another_schools_room(api: ApiFixtures) -> None:
    """A perfectly valid token still must not subscribe to a school the
    user does not belong to."""
    admin = api.admin(school_id="s1")

    with api.client.websocket_connect("/ws/schedules/v1?school_id=other_school") as socket:
        socket.send_json({"token": admin.id})
        with pytest.raises(WebSocketDisconnect) as excinfo:
            socket.receive_json()

    assert excinfo.value.code == _POLICY_VIOLATION


def test_an_authenticated_socket_receives_its_own_presence(api: ApiFixtures) -> None:
    admin = api.admin(school_id="s1")

    with api.client.websocket_connect("/ws/schedules/v1?school_id=s1") as socket:
        socket.send_json({"token": admin.id})
        message = socket.receive_json()

    assert message["type"] == "presence"
    assert [p["user_id"] for p in message["participants"]] == [admin.id]
    assert message["participants"][0]["display_name"] == admin.display_name


def test_a_second_participant_is_announced_to_the_first(api: ApiFixtures) -> None:
    admin = api.admin(school_id="s1")
    teacher = api.teacher(school_id="s1", user_id="teacher_1", teacher_id="t1")

    with api.client.websocket_connect("/ws/schedules/v1?school_id=s1") as first:
        first.send_json({"token": admin.id})
        first.receive_json()  # own presence

        with api.client.websocket_connect("/ws/schedules/v1?school_id=s1") as second:
            second.send_json({"token": teacher.id})
            second.receive_json()  # its own presence broadcast

            update = first.receive_json()
            assert update["type"] == "presence"
            assert {p["user_id"] for p in update["participants"]} == {admin.id, teacher.id}

        # ...and the departure is announced too.
        after_leaving = first.receive_json()
        assert {p["user_id"] for p in after_leaving["participants"]} == {admin.id}


def test_disconnecting_clears_the_topic(api: ApiFixtures) -> None:
    """No leaked registry entries: an empty topic is removed outright, so a
    long-lived server does not accumulate a dict entry per version ever
    opened."""
    admin = api.admin(school_id="s1")
    topic = topic_for_version("s1", "v_cleanup")

    with api.client.websocket_connect("/ws/schedules/v_cleanup?school_id=s1") as socket:
        socket.send_json({"token": admin.id})
        socket.receive_json()
        assert len(broadcaster.participants(topic)) == 1

    assert broadcaster.participants(topic) == ()
