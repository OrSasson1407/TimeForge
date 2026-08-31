"""DeviceToken: one push-notification destination belonging to one user.

Keyed by the token itself rather than by user, because one person
legitimately has several (phone plus tablet, or the same phone after a
reinstall — FCM issues a fresh token then and the old one simply stops
working). Fanning out to every registered token and pruning the ones the
provider rejects is the normal, expected lifecycle, not an error path.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class DevicePlatform(StrEnum):
    IOS = "IOS"
    ANDROID = "ANDROID"


@dataclass(frozen=True, slots=True)
class DeviceToken:
    #: The FCM registration token. Also the document id — see module note.
    token: str
    user_id: str
    school_id: str
    platform: DevicePlatform
    registered_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.token:
            raise ValueError("DeviceToken.token must not be empty")
        if not self.user_id:
            raise ValueError("DeviceToken.user_id must not be empty")
        if not self.school_id:
            raise ValueError("DeviceToken.school_id must not be empty")
