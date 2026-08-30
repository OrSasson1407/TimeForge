"""Self-service registration: register -> verify-code -> admin approve/
reject (docs/02-PRD.md #28a). Exercises the full flow against the fakes
from `tests.support.fakes` — `FakeIdentityAdmin` stands in for the real
Firebase Auth Admin SDK, `FakeEmailSender` records what would have been
sent instead of calling SMTP.
"""

from app.api.dependencies import get_register_rate_limiter
from app.core.rate_limit import RateLimiter
from app.domain.models import AuditEntityType, School, Teacher
from app.main import app
from tests.api.conftest import ApiFixtures


def _seed_school(api: ApiFixtures, school_id: str = "s1") -> None:
    api.schools.save(School(id=school_id, name="Riverside High", timezone="UTC"))


def _register(api: ApiFixtures, *, email: str = "new.teacher@example.com", school_id: str = "s1"):
    return api.client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "Str0ngPassw0rd!",
            "display_name": "New Teacher",
            "school_id": school_id,
            "recaptcha_token": "test-token",
        },
    )


def test_register_creates_a_pending_user_and_sends_a_code(api: ApiFixtures) -> None:
    _seed_school(api)

    response = _register(api)

    assert response.status_code == 201
    body = response.json()
    uid = body["user_id"]

    user = api.users.get(uid)
    assert user is not None
    assert user.role == "PENDING"
    assert user.email_verified is False

    assert len(api.email_sender.sent) == 1
    sent_email, code, ttl = api.email_sender.sent[0]
    assert sent_email == "new.teacher@example.com"
    assert len(code) == 6 and code.isdigit()
    assert ttl == 10


def test_register_rejects_a_weak_password(api: ApiFixtures) -> None:
    _seed_school(api)

    response = api.client.post(
        "/auth/register",
        json={
            "email": "weak@example.com",
            "password": "weak",
            "display_name": "Weak Password",
            "school_id": "s1",
            "recaptcha_token": "test-token",
        },
    )

    assert response.status_code == 400
    assert api.email_sender.sent == []


def test_register_rejects_a_password_without_a_symbol(api: ApiFixtures) -> None:
    _seed_school(api)

    response = api.client.post(
        "/auth/register",
        json={
            "email": "no-symbol@example.com",
            "password": "Str0ngPassw0rd",
            "display_name": "No Symbol",
            "school_id": "s1",
            "recaptcha_token": "test-token",
        },
    )

    assert response.status_code == 400
    assert "symbol" in str(response.json()["error"]["details"]).lower()


def test_register_rejects_an_unknown_school(api: ApiFixtures) -> None:
    response = _register(api, school_id="does-not-exist")

    assert response.status_code == 404


def test_register_rejects_a_duplicate_email(api: ApiFixtures) -> None:
    _seed_school(api)
    first = _register(api)
    assert first.status_code == 201

    second = _register(api)

    assert second.status_code == 409


def test_verify_code_happy_path_marks_email_verified(api: ApiFixtures) -> None:
    _seed_school(api)
    _register(api)
    _, code, _ = api.email_sender.sent[0]

    response = api.client.post(
        "/auth/verify-code", json={"email": "new.teacher@example.com", "code": code}
    )

    assert response.status_code == 200
    uid = api.identity_admin.get_uid_by_email("new.teacher@example.com")
    assert uid is not None
    user = api.users.get(uid)
    assert user is not None
    assert user.email_verified is True
    assert user.role == "PENDING"  # verifying email does not itself grant access


def test_verify_code_with_wrong_code_is_rejected_and_counts_an_attempt(api: ApiFixtures) -> None:
    _seed_school(api)
    _register(api)

    response = api.client.post(
        "/auth/verify-code", json={"email": "new.teacher@example.com", "code": "000000"}
    )

    assert response.status_code == 400
    verification = api.verifications.get("new.teacher@example.com")
    assert verification is not None
    assert verification.attempts == 1


def test_verify_code_locks_out_after_max_attempts(api: ApiFixtures) -> None:
    _seed_school(api)
    _register(api)

    for _ in range(5):
        api.client.post(
            "/auth/verify-code", json={"email": "new.teacher@example.com", "code": "000000"}
        )

    final = api.client.post(
        "/auth/verify-code", json={"email": "new.teacher@example.com", "code": "000000"}
    )

    assert final.status_code == 400
    assert "new code" in final.json()["error"]["message"].lower()


def test_resend_code_issues_a_new_code(api: ApiFixtures) -> None:
    _seed_school(api)
    _register(api)
    _, first_code, _ = api.email_sender.sent[0]

    response = api.client.post("/auth/resend-code", json={"email": "new.teacher@example.com"})

    assert response.status_code == 200
    assert len(api.email_sender.sent) == 2

    # the old code no longer verifies (resend overwrites it) — a random
    # 6-digit collision with the new code is astronomically unlikely
    stale = api.client.post(
        "/auth/verify-code", json={"email": "new.teacher@example.com", "code": first_code}
    )
    assert stale.status_code == 400


def test_registration_is_rate_limited(api: ApiFixtures) -> None:
    _seed_school(api)
    tight_limiter = RateLimiter(max_calls=1, window_seconds=3600)
    app.dependency_overrides[get_register_rate_limiter] = lambda: tight_limiter

    first = _register(api, email="one@example.com")
    second = _register(api, email="two@example.com")

    assert first.status_code == 201
    assert second.status_code == 429


def test_admin_can_list_approve_and_reject_pending_users(api: ApiFixtures) -> None:
    _seed_school(api)
    api.teachers.save("s1", Teacher(id="t1", school_id="s1", name="Tal", email="tal@example.com"))
    admin = api.admin(school_id="s1")

    register_response = _register(api)
    uid = register_response.json()["user_id"]
    _, code, _ = api.email_sender.sent[0]
    api.client.post("/auth/verify-code", json={"email": "new.teacher@example.com", "code": code})

    # Re-establish the admin as the current user (verify-code doesn't touch
    # auth state, but being explicit here documents the actor for each call).
    api.set_current_user(admin)

    pending = api.client.get("/users/pending")
    assert pending.status_code == 200
    assert [u["id"] for u in pending.json()] == [uid]
    assert pending.json()[0]["email"] == "new.teacher@example.com"

    approve = api.client.post(f"/users/{uid}/approve", json={"role": "TEACHER", "teacher_id": "t1"})
    assert approve.status_code == 200
    approved = approve.json()
    assert approved["role"] == "TEACHER"
    assert approved["teacher_id"] == "t1"

    still_pending = api.client.get("/users/pending")
    assert still_pending.json() == []


def test_approve_as_teacher_requires_a_valid_teacher_id(api: ApiFixtures) -> None:
    _seed_school(api)
    api.admin(school_id="s1")
    register_response = _register(api)
    uid = register_response.json()["user_id"]
    _, code, _ = api.email_sender.sent[0]
    api.client.post("/auth/verify-code", json={"email": "new.teacher@example.com", "code": code})

    response = api.client.post(
        f"/users/{uid}/approve", json={"role": "TEACHER", "teacher_id": "does-not-exist"}
    )

    assert response.status_code == 404


def test_reject_deletes_the_pending_registration(api: ApiFixtures) -> None:
    _seed_school(api)
    api.admin(school_id="s1")
    register_response = _register(api)
    uid = register_response.json()["user_id"]

    response = api.client.post(f"/users/{uid}/reject")

    assert response.status_code == 200
    assert api.users.get(uid) is None
    assert api.identity_admin.get_uid_by_email("new.teacher@example.com") is None


def test_non_admin_cannot_list_pending_users(api: ApiFixtures) -> None:
    api.teacher()

    response = api.client.get("/users/pending")

    assert response.status_code == 403


def test_public_schools_endpoint_requires_no_auth(api: ApiFixtures) -> None:
    _seed_school(api)

    response = api.client.get("/public/schools")

    assert response.status_code == 200
    assert response.json() == [{"id": "s1", "name": "Riverside High"}]


def test_register_and_verify_write_audit_events(api: ApiFixtures) -> None:
    _seed_school(api)
    register_response = _register(api)
    uid = register_response.json()["user_id"]
    _, code, _ = api.email_sender.sent[0]

    api.client.post("/auth/verify-code", json={"email": "new.teacher@example.com", "code": code})

    events = api.audit.list_for_entity(AuditEntityType.USER, uid)
    operations = {event.operation for event in events}
    assert "USER_REGISTERED" in operations
    assert "USER_EMAIL_VERIFIED" in operations


def test_approve_and_reject_write_audit_events(api: ApiFixtures) -> None:
    _seed_school(api)
    api.teachers.save("s1", Teacher(id="t1", school_id="s1", name="Tal", email="tal@example.com"))
    admin = api.admin(school_id="s1")

    approved_uid = _register(api, email="approved@example.com").json()["user_id"]
    rejected_uid = _register(api, email="rejected@example.com").json()["user_id"]
    api.set_current_user(admin)

    api.client.post(f"/users/{approved_uid}/approve", json={"role": "TEACHER", "teacher_id": "t1"})
    api.client.post(f"/users/{rejected_uid}/reject")

    approved_events = api.audit.list_for_entity(AuditEntityType.USER, approved_uid)
    assert any(e.operation == "USER_APPROVED" for e in approved_events)
    rejected_events = api.audit.list_for_entity(AuditEntityType.USER, rejected_uid)
    assert any(e.operation == "USER_REJECTED" for e in rejected_events)


def test_list_users_returns_admins_and_teachers_but_not_pending(api: ApiFixtures) -> None:
    _seed_school(api)
    admin = api.admin(school_id="s1")
    teacher = api.teacher(school_id="s1")
    _register(api, email="still.pending@example.com")
    api.set_current_user(admin)

    response = api.client.get("/users")

    assert response.status_code == 200
    ids = {u["id"] for u in response.json()}
    assert ids == {admin.id, teacher.id}


def test_admin_can_suspend_and_reactivate_a_teacher(api: ApiFixtures) -> None:
    admin = api.admin(school_id="s1")
    teacher = api.teacher(school_id="s1")
    api.set_current_user(admin)

    suspend = api.client.post(f"/users/{teacher.id}/suspend")
    assert suspend.status_code == 200
    assert suspend.json()["is_active"] is False
    assert teacher.id in api.identity_admin.disabled_uids

    suspend_again = api.client.post(f"/users/{teacher.id}/suspend")
    assert suspend_again.status_code == 409

    reactivate = api.client.post(f"/users/{teacher.id}/reactivate")
    assert reactivate.status_code == 200
    assert reactivate.json()["is_active"] is True
    assert teacher.id not in api.identity_admin.disabled_uids

    events = api.audit.list_for_entity(AuditEntityType.USER, teacher.id)
    operations = {event.operation for event in events}
    assert {"USER_SUSPENDED", "USER_REACTIVATED"} <= operations


def test_admin_cannot_suspend_their_own_account(api: ApiFixtures) -> None:
    admin = api.admin(school_id="s1")

    response = api.client.post(f"/users/{admin.id}/suspend")

    assert response.status_code == 400


def test_non_admin_cannot_suspend_a_user(api: ApiFixtures) -> None:
    teacher = api.teacher(school_id="s1", user_id="teacher_1", teacher_id="t1")
    other = api.teacher(school_id="s1", user_id="teacher_2", teacher_id="t2")

    response = api.client.post(f"/users/{other.id}/suspend")

    assert response.status_code == 403
    del teacher  # not the actor under test; kept for clarity of setup


def test_complete_oauth_profile_creates_a_pending_user(api: ApiFixtures) -> None:
    _seed_school(api)
    api.identity_admin.register_known_account(uid="google_uid_1", email="google.user@example.com")

    response = api.client.post(
        "/auth/complete-oauth-profile",
        json={"display_name": "Google User", "school_id": "s1"},
        headers={"Authorization": "Bearer google_uid_1"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == "google_uid_1"
    assert body["email"] == "google.user@example.com"

    user = api.users.get("google_uid_1")
    assert user is not None
    assert user.role == "PENDING"
    assert user.email_verified is True  # OAuth providers already verify the email


def test_complete_oauth_profile_rejects_an_existing_profile(api: ApiFixtures) -> None:
    _seed_school(api)
    api.teacher(school_id="s1", user_id="already_onboarded")

    response = api.client.post(
        "/auth/complete-oauth-profile",
        json={"display_name": "Already Onboarded", "school_id": "s1"},
        headers={"Authorization": "Bearer already_onboarded"},
    )

    assert response.status_code == 409
