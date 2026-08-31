"""`/ws` — the live-collaboration WebSocket (see
`app/infrastructure/realtime/manager.py` for the scope and trust model).

Authentication is by FIRST MESSAGE, not a query parameter. A browser cannot
attach an Authorization header to a WebSocket handshake, which leaves two
options: put the ID token in the URL, or send it as the first frame. URLs
are routinely written to server logs, proxy logs, and browser history, so
putting a bearer token there would leak credentials into places that are
neither expected nor easy to purge. The connection is therefore accepted
first, then required to prove itself before it is subscribed to anything —
and closed if it does not.
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.api.dependencies import get_user_repository
from app.application.repositories import UserRepository
from app.core.errors import AuthenticationError
from app.domain.models import User
from app.infrastructure.firebase.auth import resolve_user
from app.infrastructure.realtime import Participant, broadcaster, topic_for_version

logger = logging.getLogger(__name__)

router = APIRouter(tags=["collaboration"])

#: Closure codes. 1008 is the RFC 6455 "policy violation" code, which is
#: what an auth failure is at the protocol level.
_POLICY_VIOLATION = 1008

#: How long a freshly accepted socket may stay silent before it must have
#: authenticated. Without this an unauthenticated connection could be held
#: open indefinitely, which is a trivially cheap resource-exhaustion vector.
_AUTH_TIMEOUT_SECONDS = 10.0


async def _authenticate(websocket: WebSocket, user_repository: UserRepository) -> User | None:
    """Consume the first frame and resolve it to a TimeForge user, or close
    the socket and return None."""
    try:
        opening = await asyncio.wait_for(websocket.receive_json(), timeout=_AUTH_TIMEOUT_SECONDS)
    except (TimeoutError, WebSocketDisconnect, ValueError):
        await websocket.close(code=_POLICY_VIOLATION, reason="Expected an auth message")
        return None

    token = opening.get("token") if isinstance(opening, dict) else None
    if not isinstance(token, str) or not token:
        await websocket.close(code=_POLICY_VIOLATION, reason="Expected an auth message")
        return None

    try:
        # Exactly the same resolution path as every REST request: the token
        # is Firebase-signature-verified and the ROLE comes from Firestore,
        # never from a client claim (docs/03-ARCHITECTURE.md #23-24). A
        # suspended account is rejected here too.
        return resolve_user(token, user_repository)
    except AuthenticationError:
        await websocket.close(code=_POLICY_VIOLATION, reason="Invalid credentials")
        return None


@router.websocket("/ws/schedules/{version_id}")
async def collaborate_on_version(
    websocket: WebSocket,
    version_id: str,
    school_id: str = Query(...),
    user_repository: UserRepository = Depends(get_user_repository),
) -> None:
    await websocket.accept()

    user = await _authenticate(websocket, user_repository)
    if user is None:
        return

    # A user may only join their own school's room. Without this check, a
    # valid token from school A could subscribe to school B's activity.
    if user.school_id != school_id:
        await websocket.close(code=_POLICY_VIOLATION, reason="Wrong school")
        return

    topic = topic_for_version(school_id, version_id)
    participant = Participant(user_id=user.id, display_name=user.display_name)
    broadcaster.connect(topic, websocket, participant)

    try:
        await _announce_presence(topic)
        while True:
            # Nothing a client sends is trusted or acted upon — the loop
            # exists to keep the socket open and to notice disconnects.
            # Every real change still goes through the REST API, which is
            # what then triggers a server-side broadcast.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.disconnect(topic, websocket)
        await _announce_presence(topic)


async def _announce_presence(topic: str) -> None:
    await broadcaster.broadcast(
        topic,
        {
            "type": "presence",
            "participants": [
                {"user_id": p.user_id, "display_name": p.display_name}
                for p in broadcaster.participants(topic)
            ],
        },
    )
