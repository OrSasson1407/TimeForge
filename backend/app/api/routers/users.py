"""`/users` — the admin approval queue for self-registered accounts, plus
account management (docs/02-PRD.md #28a). Every route here requires an
Admin; a PENDING user resolves its own identity through `/auth/me`, never
through this router.
"""

import uuid
from dataclasses import replace
from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_audit_repository,
    get_identity_admin,
    get_teacher_repository,
    get_user_repository,
    require_admin,
)
from app.api.schemas.auth import (
    AdminUserResponse,
    ApproveUserRequest,
    MessageResponse,
    PendingUserResponse,
    UserResponse,
    user_to_response,
)
from app.application.repositories import (
    AuditRepository,
    IdentityAdminPort,
    TeacherRepository,
    UserRepository,
)
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.domain.models import Actor, AuditEntityType, AuditEvent, AuditOperation, User, UserRole

router = APIRouter(prefix="/users", tags=["users"])


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


@router.get("", response_model=list[AdminUserResponse])
def list_users(
    _admin: User = Depends(require_admin),
    user_repository: UserRepository = Depends(get_user_repository),
    identity_admin: IdentityAdminPort = Depends(get_identity_admin),
) -> list[AdminUserResponse]:
    """Every account that has *already* been assigned a role — the
    counterpart to `/users/pending`, for suspending/reactivating existing
    Admins and Teachers rather than reviewing new registrations."""
    users = user_repository.list_by_role(UserRole.ADMIN) + user_repository.list_by_role(
        UserRole.TEACHER
    )
    return [
        AdminUserResponse(
            id=user.id,
            email=identity_admin.get_email(user.id) or "",
            role=user.role,
            school_id=user.school_id,
            display_name=user.display_name,
            teacher_id=user.teacher_id,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        for user in users
    ]


@router.get("/pending", response_model=list[PendingUserResponse])
def list_pending_users(
    _admin: User = Depends(require_admin),
    user_repository: UserRepository = Depends(get_user_repository),
    identity_admin: IdentityAdminPort = Depends(get_identity_admin),
) -> list[PendingUserResponse]:
    pending = [u for u in user_repository.list_by_role(UserRole.PENDING) if u.email_verified]

    return [
        PendingUserResponse(
            id=user.id,
            email=identity_admin.get_email(user.id) or "",
            display_name=user.display_name,
            school_id=user.school_id,
            created_at=user.created_at,
        )
        for user in pending
    ]


@router.post("/{user_id}/approve", response_model=UserResponse)
def approve_user(
    user_id: str,
    body: ApproveUserRequest,
    admin: User = Depends(require_admin),
    user_repository: UserRepository = Depends(get_user_repository),
    teacher_repository: TeacherRepository = Depends(get_teacher_repository),
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> UserResponse:
    user = user_repository.get(user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
    if user.role is not UserRole.PENDING:
        raise ConflictError(f"User {user_id} is not awaiting approval")

    teacher_id = None
    if body.role is UserRole.TEACHER:
        if not body.teacher_id:
            raise ValidationError("teacher_id is required when approving as TEACHER")
        if teacher_repository.get(user.school_id, body.teacher_id) is None:
            raise NotFoundError(f"Teacher {body.teacher_id} not found in school {user.school_id}")
        teacher_id = body.teacher_id

    updated = replace(user, role=body.role, teacher_id=teacher_id)
    user_repository.save(updated)
    _record_auth_event(
        audit_repository,
        actor=admin,
        operation=AuditOperation.USER_APPROVED,
        user_id=user_id,
        reason=f"Approved as {body.role.value}",
    )
    return user_to_response(updated)


@router.post("/{user_id}/reject", response_model=MessageResponse)
def reject_user(
    user_id: str,
    admin: User = Depends(require_admin),
    user_repository: UserRepository = Depends(get_user_repository),
    identity_admin: IdentityAdminPort = Depends(get_identity_admin),
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> MessageResponse:
    user = user_repository.get(user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
    if user.role is not UserRole.PENDING:
        raise ConflictError(
            f"User {user_id} is not awaiting approval — only a pending registration can be rejected"
        )

    user_repository.delete(user_id)
    identity_admin.delete_user(user_id)  # best-effort; Firestore removal is what revokes access
    _record_auth_event(
        audit_repository, actor=admin, operation=AuditOperation.USER_REJECTED, user_id=user_id
    )

    return MessageResponse(message="Registration rejected")


@router.post("/{user_id}/suspend", response_model=UserResponse)
def suspend_user(
    user_id: str,
    admin: User = Depends(require_admin),
    user_repository: UserRepository = Depends(get_user_repository),
    identity_admin: IdentityAdminPort = Depends(get_identity_admin),
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> UserResponse:
    if user_id == admin.id:
        raise ValidationError("You cannot suspend your own account")

    user = user_repository.get(user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
    if user.role is UserRole.PENDING:
        raise ConflictError("A pending registration should be rejected, not suspended")
    if not user.is_active:
        raise ConflictError(f"User {user_id} is already suspended")

    updated = replace(user, is_active=False)
    user_repository.save(updated)
    identity_admin.set_disabled(user_id, disabled=True)
    _record_auth_event(
        audit_repository, actor=admin, operation=AuditOperation.USER_SUSPENDED, user_id=user_id
    )
    return user_to_response(updated)


@router.post("/{user_id}/reactivate", response_model=UserResponse)
def reactivate_user(
    user_id: str,
    admin: User = Depends(require_admin),
    user_repository: UserRepository = Depends(get_user_repository),
    identity_admin: IdentityAdminPort = Depends(get_identity_admin),
    audit_repository: AuditRepository = Depends(get_audit_repository),
) -> UserResponse:
    user = user_repository.get(user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
    if user.is_active:
        raise ConflictError(f"User {user_id} is not suspended")

    updated = replace(user, is_active=True)
    user_repository.save(updated)
    identity_admin.set_disabled(user_id, disabled=False)
    _record_auth_event(
        audit_repository, actor=admin, operation=AuditOperation.USER_REACTIVATED, user_id=user_id
    )
    return user_to_response(updated)
