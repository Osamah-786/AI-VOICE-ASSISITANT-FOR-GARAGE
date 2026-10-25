import asyncio
def _run_coroutine_inline(coro):
    """Run mocked async SDK calls without opening Windows event-loop sockets."""
    try:
        coro.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coro.close()
    raise AssertionError("Mocked coroutine unexpectedly yielded")

import threading
import time
import sys
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class TokenEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()
        self.env = patch.dict("os.environ", {
            "LIVEKIT_API_KEY": "test-key",
            "LIVEKIT_API_SECRET": "test-secret-with-at-least-thirty-two-bytes",
            "LIVEKIT_URL": "wss://example.livekit.cloud",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.asyncio_run_patch = patch.object(server.asyncio, "run", side_effect=_run_coroutine_inline)
        self.asyncio_run_patch.start()
        self.addCleanup(self.asyncio_run_patch.stop)

    def test_first_connection_creates_room_dispatch_and_token(self):
        api = SimpleNamespace(
            room=SimpleNamespace(
                list_rooms=AsyncMock(return_value=SimpleNamespace(rooms=[])),
                create_room=AsyncMock(),
            ),
            agent_dispatch=SimpleNamespace(
                list_dispatch=AsyncMock(return_value=[]),
                create_dispatch=AsyncMock(),
            ),
            aclose=AsyncMock(),
        )
        with patch.object(server, "LiveKitAPI", return_value=api):
            response = self.client.get(
                "/api/token?room=garage-room-123e4567-e89b-12d3-a456-426614174000&participant=web-test"
            )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["token"])
        self.assertEqual(body["room"], "garage-room-123e4567-e89b-12d3-a456-426614174000")
        api.room.create_room.assert_awaited_once()
        api.agent_dispatch.create_dispatch.assert_awaited_once()
        api.aclose.assert_awaited_once()

    def test_pending_dispatch_is_reused(self):
        dispatch = SimpleNamespace(
            agent_name=server.AGENT_NAME,
            state=SimpleNamespace(jobs=[SimpleNamespace(state=SimpleNamespace(status=0))]),
        )
        api = SimpleNamespace(
            room=SimpleNamespace(
                list_rooms=AsyncMock(return_value=SimpleNamespace(rooms=[object()])),
                create_room=AsyncMock(),
            ),
            agent_dispatch=SimpleNamespace(
                list_dispatch=AsyncMock(return_value=[dispatch]),
                create_dispatch=AsyncMock(),
            ),
            aclose=AsyncMock(),
        )
        with patch.object(server, "LiveKitAPI", return_value=api):
            response = self.client.get(
                "/api/token?room=garage-room-123e4567-e89b-12d3-a456-426614174000&participant=web-test"
            )

        self.assertEqual(response.status_code, 200)
        api.agent_dispatch.create_dispatch.assert_not_awaited()

    def test_terminal_dispatch_is_replaced(self):
        dispatch = SimpleNamespace(
            agent_name=server.AGENT_NAME,
            state=SimpleNamespace(jobs=[SimpleNamespace(state=SimpleNamespace(status=2))]),
        )
        api = SimpleNamespace(
            room=SimpleNamespace(
                list_rooms=AsyncMock(return_value=SimpleNamespace(rooms=[object()])),
                create_room=AsyncMock(),
            ),
            agent_dispatch=SimpleNamespace(
                list_dispatch=AsyncMock(return_value=[dispatch]),
                create_dispatch=AsyncMock(),
            ),
            aclose=AsyncMock(),
        )
        with patch.object(server, "LiveKitAPI", return_value=api):
            response = self.client.get(
                "/api/token?room=garage-room-123e4567-e89b-12d3-a456-426614174000&participant=web-test"
            )

        self.assertEqual(response.status_code, 200)
        api.agent_dispatch.create_dispatch.assert_awaited_once()

    def test_invalid_static_room_is_rejected(self):
        response = self.client.get("/api/token?room=garage-room&participant=web-test")
        self.assertEqual(response.status_code, 400)


    def test_transient_dispatch_failure_is_retried_once(self):
        attempts = 0

        async def flaky_dispatch(*_args):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise server.aiohttp.ClientConnectionError("temporary network failure")

        with patch.object(server, "_ensure_agent_dispatch", side_effect=flaky_dispatch):
            response = self.client.get(
                "/api/token?room=garage-room-123e4567-e89b-12d3-a456-426614174000&participant=web-test"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(attempts, 2)

    def test_permanent_dispatch_failure_is_not_retried(self):
        async def fail_permanently(*_args):
            raise ValueError("invalid request")

        with patch.object(server, "_ensure_agent_dispatch", side_effect=fail_permanently) as dispatch:
            response = self.client.get(
                "/api/token?room=garage-room-123e4567-e89b-12d3-a456-426614174000&participant=web-test"
            )

        self.assertEqual(response.status_code, 502)
        dispatch.assert_called_once()

    def test_concurrent_same_session_requests_serialize_dispatch(self):
        active = 0
        max_active = 0
        count_lock = threading.Lock()

        async def fake_ensure(*_args):
            nonlocal active, max_active
            with count_lock:
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.03)
            with count_lock:
                active -= 1

        room = "garage-room-123e4567-e89b-12d3-a456-426614174000"
        responses = []
        with patch.object(server, "_ensure_agent_dispatch", side_effect=fake_ensure):
            threads = [
                threading.Thread(target=lambda: responses.append(
                    server.app.test_client().get(f"/api/token?room={room}&participant=web-test")
                ))
                for _ in range(2)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        self.assertEqual([response.status_code for response in responses], [200, 200])
        self.assertEqual(max_active, 1)


if __name__ == "__main__":
    unittest.main()
