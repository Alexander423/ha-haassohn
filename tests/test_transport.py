"""Real socket edge cases that mocks cannot validate: framing, redirects and cancellation."""

import asyncio
import json
from contextlib import asynccontextmanager

import pytest

from pyhaassohn import HaasSohnClient
from pyhaassohn.exceptions import ConnectionError, ProtocolError, RequestTimeout
from tests.emulator import profile


@asynccontextmanager
async def raw_server(reply, delay=0, parts=False):
    tasks = set()

    async def handler(reader, writer):
        task = asyncio.current_task()
        tasks.add(task)
        try:
            await reader.readuntil(b"\r\n\r\n")
            if delay:
                await asyncio.sleep(delay)
            if parts:
                for index in range(0, len(reply), 17):
                    writer.write(reply[index : index + 17])
                    await writer.drain()
                    await asyncio.sleep(0)
            else:
                writer.write(reply)
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            tasks.discard(task)

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    try:
        yield server.sockets[0].getsockname()[1]
    finally:
        server.close()
        await server.wait_closed()
        active = list(tasks)
        for task in active:
            task.cancel()
        await asyncio.gather(*active, return_exceptions=True)


def response(body):
    return (
        b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
        + str(len(body)).encode()
        + b"\r\nConnection: close\r\n\r\n"
        + body
    )


async def test_fragmented_response():
    async with (
        raw_server(response(json.dumps(profile()).encode()), parts=True) as port,
        HaasSohnClient("127.0.0.1", "0246", port=port) as client,
    ):
        assert (await client.get_state()).values["is_temp"] == 20.5


async def test_partial_and_disconnect():
    async with (
        raw_server(b"HTTP/1.1 200 OK\r\nContent-Length: 999\r\n\r\n{") as port,
        HaasSohnClient("127.0.0.1", "0246", port=port) as client,
    ):
        with pytest.raises(ConnectionError):
            await client.get_state()


async def test_oversized_body():
    async with (
        raw_server(response(b"x" * 70000)) as port,
        HaasSohnClient("127.0.0.1", "0246", port=port) as client,
    ):
        with pytest.raises(ProtocolError):
            await client.get_state()


async def test_redirect_refused():
    async with (
        raw_server(
            b"HTTP/1.1 302 Found\r\nLocation: http://example.invalid/\r\nContent-Length: 0\r\n\r\n"
        ) as port,
        HaasSohnClient("127.0.0.1", "0246", port=port) as client,
    ):
        with pytest.raises(ProtocolError):
            await client.get_state()


async def test_total_timeout():
    async with (
        raw_server(b"", delay=5) as port,
        HaasSohnClient("127.0.0.1", "0246", port=port, timeout=0.02) as client,
    ):
        with pytest.raises(RequestTimeout):
            await client.get_state()


async def test_cancel_releases_transaction_lock():
    async with (
        raw_server(response(json.dumps(profile()).encode()), delay=0.2) as port,
        HaasSohnClient("127.0.0.1", "0246", port=port) as client,
    ):
        task = asyncio.create_task(client.get_state())
        await asyncio.sleep(0.02)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        async with asyncio.timeout(2):
            assert (await client.get_state()).info.controller == "KS01"
