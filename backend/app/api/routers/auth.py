"""`/auth` — identity introspection plus self-service registration.

`GET /me`: Firebase Authentication issues ID tokens directly to the
frontend (docs/03-ARCHITECTURE.md #23); the backend only ever verifies and
resolves one to the backend's own User record.

`POST /register`, `/verify-code`, `/resend-code`: the one place the
backend *does* create a Firebase Auth account and a Firestore User record
on a client's say-so — but the account is born with `role=PENDING` and no
`teacher_id`, so it can authenticate but do nothing else until an Admin
approves it via `/users/{id}/approve` (docs/02-PRD.md #28a). The password
passes through this endpoint once, over HTTPS, to hand to the Firebase
Admin SDK — it is never stored or logged.

`POST /complete-oauth-profile`: the equivalent first step for a Google
sign-in, which arrives with a verified Firebase identity and a
Firebase-verified email already — no password, no 6-digit code, just the
TimeForge-specific fields (school, display name) before the account lands
in the same PENDING-until-approved state.
"""

import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import (
    extract_bearer_token,
    get_audit_repository,
    get_current_user,
    get_email_sender,
    get_identity_admin,
    get_register_rate_limiter,
    get_resend_code_rate_limiter,
    get_school_repository,
    get_user_repository,
    get_verification_repository,
)
from app.api.schemas.auth import (
    CompleteOAuthProfileRequest,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    ResendCodeRequest,
    UserResponse,
    VerifyCodeRequest,
    user_to_response,
)
from app.application.repositories import (
    AuditRepository,
    IdentityAdminPort,
    SchoolRepository,
    UserRepository,
    VerificationCodeRepository,
)
from app.core.config import Settings, get_settings
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.rate_limit import RateLimiter
from app.core.security import (
    check_password_not_breached,
    generate_numeric_code,
    hash_code,
    validate_password_strength,
    verify_recaptcha,
)
from app.domain.models import (
    Actor,
    AuditEntityType,
    AuditEvent,
    AuditOperation,
    EmailVerification,
    User,
    UserRole,
)
from app.infrastructure.email import EmailSender

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return user_to_response(user)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _issue_and_send_code(
    email: str,
    verification_repository: VerificationCodeRepository,
    email_sender: EmailSender,
    settings: Settings,
) -> None:
    code = generate_numeric_code()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.verification_code_ttl_minutes)
    verification_repository.save(
        EmailVerification(email=email, code_hash=hash_code(code), expires_at=expires_at)
    )
    email_sender.send_verification_code(
        to_email=email, code=code, ttl_minutes=settings.verification_code_ttl_minutes
    )


def _record_auth_event(
    audit_repository: AuditRepository,
    *,
    actor: User,
    operation: AuditOperation,
    user_id: str,
    reason: str | None = None,
) -> None:
    audit_repository.append(
        AuditEvent(
            id=f"audit_{uuid.uuid4().hex[:16]}",
            actor=Actor(user_id=actor.id, role=actor.role),
            timestamp=datetime.now(UTC),
            operation=operation,
            entity_type=AuditEntityType.USER,
            entity_id=user_id,
            reason=reason,
        )
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(
    body: RegisterRequest,
    request: Request,
    school_repository: SchoolRepository = Depends(get_school_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    verification_repository: VerificationCodeRepository = Depends(get_verification_repository),
    identity_admin: IdentityAdminPort = Depends(get_identity_admin),
    email_sender: EmailSender = Depends(get_email_sender),
    audit_repository: AuditRepository = Depends(get_audit_repository),
    rate_limiter: RateLimiter = Depends(get_register_rate_limiter),
    settings: Settings = Depends(get_settings),
) -> RegisterResponse:
    rate_limiter.check(_client_ip(request))  # caps total registrations attempted from one source
    verify_recaptcha(body.recaptcha_token, secret_key=settings.recaptcha_secret_key)
    validate_password_strength(body.password, require_symbol=settings.password_require_symbol)
    if settings.password_check_breached:
        check_password_not_breached(body.password)

    if school_repository.get(body.school_id) is None:
        raise NotFoundError(f"School {body.school_id} not found")

    uid = identity_admin.create_user(
        email=body.email, password=body.password, display_name=body.display_name
    )

    new_user = User(
        id=uid,
        role=UserRole.PENDING,
        school_id=body.school_id,
        display_name=body.display_name,
    )
    user_repository.save(new_user)
    _record_auth_event(
        audit_repository, actor=new_user, operation=AuditOperation.USER_REGISTERED, user_id=uid
    )
    _issue_and_send_code(body.email, verification_repository, email_sender, settings)

    return RegisterResponse(user_id=uid, email=body.email)


@router.post("/complete-oauth-profile", response_model=RegisterResponse, status_code=201)
def complete_oauth_profile(
    body: CompleteOAuthProfileRequest,
    request: Request,
    token: str = Depends(extract_bearer_token),
    school_repository: SchoolRepository = Depends(get_school_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    identity_admin: IdentityAdminPort = Depends(get_identity_admin),
    audit_repository: AuditRepository = Depends(get_audit_repository),
    rate_limiter: RateLimiter = Depends(get_register_rate_limiter),
) -> RegisterResponse:
    rate_limiter.check(_client_ip(request))
    uid = identity_admin.verify_token(token)

    if user_repository.get(uid) is not None:
        raise ConflictError("This account already has a TimeForge profile")
    if school_repository.get(body.school_id) is None:
        raise NotFoundError(f"School {body.school_id} not found")

    new_user = User(
        id=uid,
        role=UserRole.PENDING,
        school_id=body.school_id,
        display_name=body.display_name,
        email_verified=True,  # the OAuth provider already verified it
    )
    user_repository.save(new_user)
    _record_auth_event(
        audit_repository,
        actor=new_user,
        operation=AuditOperation.USER_REGISTERED,
        user_id=uid,
        reason="Signed up via Google",
    )

    return RegisterResponse(
        user_id=uid,
        email=identity_admin.get_email(uid) or "",
        message="Registered via Google. An administrator will review your account.",
    )


@router.post("/verify-code", response_model=MessageResponse)
def verify_code(
    body: VerifyCodeRequest,
    user_repository: UserRepository = Depends(get_user_repository),
    verification_repository: VerificationCodeRepository = Depends(get_verification_repository),
    identity_admin: IdentityAdminPort = Depends(get_identity_admin),
    audit_repository: AuditRepository = Depends(get_audit_repository),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    verification = verification_repository.get(body.email)
    if verification is None:
        raise ValidationError("No pending verification for this email — request a new code")
    if verification.is_expired(now=datetime.now(UTC)):
        verification_repository.delete(body.email)
        raise ValidationError("This code has expired — request a new one")
    if verification.attempts >= settings.verification_code_max_attempts:
        verification_repository.delete(body.email)
        raise ValidationError("Too many incorrect attempts — request a new code")

    if hash_code(body.code) != verification.code_hash:
        attempts = verification_repository.record_attempt(body.email)
        remaining = max(settings.verification_code_max_attempts - attempts, 0)
        raise ValidationError(f"Incorrect code ({remaining} attempt(s) remaining)")

    verification_repository.delete(body.email)

    uid = identity_admin.get_uid_by_email(body.email)
    if uid is None:
        raise NotFoundError("No account found for this email")

    user = user_repository.get(uid)
    if user is None:
        raise NotFoundError("No TimeForge account found for this email")

    verified_user = replace(user, email_verified=True)
    user_repository.save(verified_user)
    identity_admin.mark_email_verified(uid)
    _record_auth_event(
        audit_repository,
        actor=verified_user,
        operation=AuditOperation.USER_EMAIL_VERIFIED,
        user_id=uid,
    )

    return MessageResponse(
        message="Email verified. An administrator will review your account before you can sign in."
    )


@router.post("/resend-code", response_model=MessageResponse)
def resend_code(
    body: ResendCodeRequest,
    user_repository: UserRepository = Depends(get_user_repository),
    verification_repository: VerificationCodeRepository = Depends(get_verification_repository),
    identity_admin: IdentityAdminPort = Depends(get_identity_admin),
    email_sender: EmailSender = Depends(get_email_sender),
    rate_limiter: RateLimiter = Depends(get_resend_code_rate_limiter),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    rate_limiter.check(body.email)  # caps how many times one inbox can be spammed

    uid = identity_admin.get_uid_by_email(body.email)
    if uid is None:
        raise ValidationError("No pending registration for this email")

    user = user_repository.get(uid)
    if user is None or user.email_verified:
        raise ValidationError("No pending registration for this email")

    _issue_and_send_code(body.email, verification_repository, email_sender, settings)
    return MessageResponse(message="A new code has been sent.")
