"""NotifySchedulePublishedUseCase: tell every registered device in a school
that a new timetable is live.

Publishing is the *only* event that pushes. A draft edit is admin working
state that may be reverted, and pushing every intermediate move would train
people to ignore the notifications entirely — which would cost far more
than it gains on the one occasion the timetable actually changes.

Best-effort throughout. The publish it follows has already committed; this
must never raise, so a dead handset or an FCM outage cannot turn a
successful publish into a failed request.
"""

import logging
from dataclasses import dataclass

from app.application.repositories import DeviceTokenRepository, PushSenderPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class NotifySchedulePublishedUseCase:
    device_repository: DeviceTokenRepository
    push_sender: PushSenderPort

    def execute(self, school_id: str, *, school_name: str) -> int:
        """Returns how many devices were targeted (before pruning), for
        logging and tests. Never raises."""
        try:
            devices = self.device_repository.list_for_school(school_id)
        except Exception:  # noqa: BLE001 - see module docstring
            logger.exception("Could not load device tokens for school %s", school_id)
            return 0

        tokens = [device.token for device in devices]
        if not tokens:
            return 0

        try:
            invalid = self.push_sender.send_to_tokens(
                tokens,
                title="Timetable updated",
                body=f"A new schedule has been published for {school_name}.",
            )
        except Exception:  # noqa: BLE001 - see module docstring
            logger.exception("Push dispatch failed for school %s", school_id)
            return len(tokens)

        for token in invalid:
            try:
                self.device_repository.delete(token)
            except Exception:  # noqa: BLE001 - pruning is housekeeping, not the point
                logger.warning("Could not prune invalid device token")
        return len(tokens)
