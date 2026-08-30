"""Room entity (docs/04-DESIGN.md #1-2, docs/05-DATABASE.md #4/#24).

Capabilities are the *only* mechanism that links a lesson's room requirement
to a room (HC-004) — never a hardcoded subject-to-room-name mapping
(master prompt #55). A capability is represented here simply as its code
(e.g. "CHEMISTRY_LAB"); the human-readable catalog (code -> label) is
school-level configuration, not part of the Room entity itself
(docs/05-DATABASE.md #25).
"""

from dataclasses import dataclass, field

from app.domain.models.enums import RoomStatus


@dataclass(frozen=True, slots=True)
class Room:
    id: str
    school_id: str
    name: str
    capacity: int
    room_type: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    status: RoomStatus = RoomStatus.ACTIVE

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Room.id must not be empty")
        if not self.school_id:
            raise ValueError("Room.school_id must not be empty")
        if not self.name:
            raise ValueError("Room.name must not be empty")
        if not self.room_type:
            raise ValueError("Room.room_type must not be empty")
        if self.capacity <= 0:
            raise ValueError("Room.capacity must be > 0")

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    def can_seat(self, student_count: int) -> bool:
        return student_count <= self.capacity
