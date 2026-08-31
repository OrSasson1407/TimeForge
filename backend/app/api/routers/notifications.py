"""`/notifications` — push-device registration for the mobile client.

The token is bound to the caller's server-verified identity and school, not
to whatever the request body claims. A client can therefore only ever
register a device against itself, which is what stops one user subscribing
to another school's announcements by posting a chosen school_id.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user, get_device_token_repository
from app.api.schemas.auth import MessageResponse
from app.application.repositories import DeviceTokenRepository
from app.domain.models import User
from app.domain.models.device import DevicePlatform, DeviceToken

router = APIRouter(prefix="/notifications", tags=["notifications"])


class RegisterDeviceRequest(BaseModel):
    token: str = Field(min_length=1, max_length=4096)
    platform: DevicePlatform


@router.post("/devices", response_model=MessageResponse, status_code=201)
def register_device(
    body: RegisterDeviceRequest,
    user: User = Depends(get_current_user),
    device_repository: DeviceTokenRepository = Depends(get_device_token_repository),
) -> MessageResponse:
    """Idempotent: the mobile app re-registers on every launch, because FCM
    can rotate a token at any time and the only way to notice is to send the
    current one again."""
    device_repository.save(
        DeviceToken(
            token=body.token,
            user_id=user.id,
            school_id=user.school_id,
            platform=body.platform,
        )
    )
    return MessageResponse(message="Device registered for notifications.")


@router.delete("/devices/{token}", response_model=MessageResponse)
def unregister_device(
    token: str,
    user: User = Depends(get_current_user),
    device_repository: DeviceTokenRepository = Depends(get_device_token_repository),
) -> MessageResponse:
    """Called on sign-out so a shared or handed-on device stops receiving a
    former user's school announcements.

    Only the owner may unregister a token. Reports success either way rather
    than 404-ing on someone else's token: the caller has no legitimate need
    to distinguish "already gone" from "not yours", and doing so would turn
    this into an oracle for probing whether a given token is registered.
    """
    existing = device_repository.get(token)
    if existing is not None and existing.user_id == user.id:
        device_repository.delete(token)
    return MessageResponse(message="Device unregistered.")
