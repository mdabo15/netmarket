"""Unit tests for the in-process WebSocket connection registry
(app/notifications/ws_manager.py) — connecting, targeted push, and dropping
a socket that fails to send rather than raising into the caller."""

import uuid

import pytest

from app.notifications.ws_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self, *, fails: bool = False) -> None:
        self.fails = fails
        self.accepted = False
        self.sent: list[dict] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, payload: dict) -> None:
        if self.fails:
            raise RuntimeError("connection closed")
        self.sent.append(payload)


@pytest.fixture
def manager() -> ConnectionManager:
    return ConnectionManager()


async def test_send_to_user_reaches_all_of_that_users_sockets(manager: ConnectionManager) -> None:
    user_id = uuid.uuid4()
    ws1, ws2 = FakeWebSocket(), FakeWebSocket()
    await manager.connect(user_id, ws1)
    await manager.connect(user_id, ws2)

    await manager.send_to_user(user_id, {"hello": "world"})

    assert ws1.sent == [{"hello": "world"}]
    assert ws2.sent == [{"hello": "world"}]


async def test_send_to_user_does_not_reach_other_users(manager: ConnectionManager) -> None:
    user_id, other_id = uuid.uuid4(), uuid.uuid4()
    ws = FakeWebSocket()
    await manager.connect(other_id, ws)

    await manager.send_to_user(user_id, {"hello": "world"})

    assert ws.sent == []


async def test_dead_socket_is_dropped_without_raising(manager: ConnectionManager) -> None:
    user_id = uuid.uuid4()
    dead, alive = FakeWebSocket(fails=True), FakeWebSocket()
    await manager.connect(user_id, dead)
    await manager.connect(user_id, alive)

    await manager.send_to_user(user_id, {"hello": "world"})

    assert alive.sent == [{"hello": "world"}]
    assert dead not in manager._connections.get(user_id, set())
