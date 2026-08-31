"""Live-collaboration fan-out: who is currently looking at a schedule
version, and pushing "someone changed it" to everyone else.

Scope, stated plainly so it is not mistaken for more than it is:

- **This layer is never authoritative.** Schedule edits stay
  optimistic-concurrency-controlled by `version_tag` on the REST endpoints
  (`ApplyMoveUseCase`), which already *rejects* a conflicting write with a
  409 whether or not any WebSocket is connected. What this adds is
  awareness (you can see a colleague is in the same version) and latency
  (their change appears without a manual refresh). A dropped or spoofed
  WebSocket message can therefore cost freshness, never correctness — a
  deliberately weak trust requirement for a channel that is harder to
  reason about than a request/response one.

- **Single-node.** Subscriptions live in this process's memory, so two
  backend replicas would each fan out only to their own clients. Making it
  multi-node is a matter of publishing to a shared bus (Redis Pub/Sub is
  the usual choice) and having each replica relay onto its local sockets;
  `Broadcaster` is the seam where that would slot in. Building it now would
  mean adding infrastructure this deployment does not yet have and cannot
  be tested against here, so it is a documented extension point rather than
  speculative code.

- **Native WebSockets, not Socket.io.** Socket.io is its own protocol on
  top of WebSocket and would need `python-socketio` server-side plus its
  client library in the browser. Its selling points (rooms, auto-reconnect,
  long-poll fallback) are respectively ~20 lines here, already handled by
  the frontend hook, and irrelevant for an admin tool on a modern browser.
"""

import asyncio
import logging
from dataclasses import dataclass, field

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Participant:
    user_id: str
    display_name: str


@dataclass
class Broadcaster:
    """Tracks live connections per topic and fans messages out to them.

    Safe under asyncio without explicit locking: every mutation below
    happens between awaits on a single event loop, so no other coroutine
    can observe a half-updated dict. It is NOT safe to mutate from another
    thread — see `publish_threadsafe` for how synchronous request handlers
    reach it.
    """

    _connections: dict[str, dict[WebSocket, Participant]] = field(default_factory=dict)
    _loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Remember the serving event loop so synchronous (threadpool)
        request handlers can hand work back to it."""
        self._loop = loop

    def connect(self, topic: str, websocket: WebSocket, participant: Participant) -> None:
        self._connections.setdefault(topic, {})[websocket] = participant

    def disconnect(self, topic: str, websocket: WebSocket) -> None:
        peers = self._connections.get(topic)
        if peers is None:
            return
        peers.pop(websocket, None)
        if not peers:
            del self._connections[topic]

    def participants(self, topic: str) -> tuple[Participant, ...]:
        """Distinct people (not sockets) currently on `topic` — one person
        with the schedule open in two tabs is still one colleague to be
        aware of."""
        seen: dict[str, Participant] = {}
        for participant in self._connections.get(topic, {}).values():
            seen.setdefault(participant.user_id, participant)
        return tuple(seen.values())

    async def broadcast(
        self, topic: str, message: dict[str, object], *, exclude: WebSocket | None = None
    ) -> None:
        """Send to everyone on `topic`, optionally skipping the originator.

        A send failure only ever removes that one socket: one dead peer must
        not stop the others from being told, and a client that has gone away
        without a clean close is an entirely expected event, not an error
        worth surfacing.
        """
        peers = list(self._connections.get(topic, {}).keys())
        for websocket in peers:
            if websocket is exclude:
                continue
            try:
                await websocket.send_json(message)
            except Exception:  # noqa: BLE001 - a broken peer must not break the rest
                logger.debug("Dropping unreachable websocket on topic %s", topic)
                self.disconnect(topic, websocket)

    def publish_threadsafe(self, topic: str, message: dict[str, object]) -> None:
        """Fan out from a synchronous request handler.

        FastAPI runs `def` (non-async) endpoints in a worker thread, so they
        cannot await `broadcast` directly and must not touch the loop's
        structures from that thread. `run_coroutine_threadsafe` is the
        supported hand-off. Deliberately fire-and-forget: an admin's move
        must not fail, or even slow down, because a colleague's browser is
        unreachable — the REST response is the source of truth and has
        already succeeded by this point.
        """
        if self._loop is None:
            return  # no server loop bound (e.g. a unit test) — nothing to notify
        try:
            asyncio.run_coroutine_threadsafe(self.broadcast(topic, message), self._loop)
        except RuntimeError:
            logger.debug("Event loop unavailable; skipping realtime publish on %s", topic)


def topic_for_version(school_id: str, version_id: str) -> str:
    """One room per (school, schedule version). Scoping by school as well as
    version means a version id colliding across schools — or being guessed —
    still cannot leak one school's activity into another's room."""
    return f"{school_id}:{version_id}"


#: Process-wide singleton. A module-level instance rather than a FastAPI
#: dependency because the WebSocket endpoint and the synchronous REST
#: handlers must reach the *same* registry, and the latter run outside the
#: request-scoped dependency graph's async context.
broadcaster = Broadcaster()
