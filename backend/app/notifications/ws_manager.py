"""In-process WebSocket connection registry for live notification push.

Single-process, in-memory by design — the API runs as one container today
(see docker-compose.yml), so there is no need for a Redis pub/sub relay to
fan out across multiple instances. If the API is ever scaled horizontally,
a connected user's socket may live on a different instance than the one
handling the write that triggers the notification; at that point this would
need to move to Redis pub/sub. Until then this is simpler and has one fewer
moving part.
"""

import logging
import uuid
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: uuid.UUID, payload: dict) -> None:
        sockets = list(self._connections.get(user_id, ()))
        for websocket in sockets:
            try:
                await websocket.send_json(payload)
            except Exception:  # noqa: BLE001 - une socket morte ne doit jamais faire échouer l'appelant
                logger.info("Échec d'envoi WebSocket, connexion retirée", exc_info=True)
                self.disconnect(user_id, websocket)


manager = ConnectionManager()
