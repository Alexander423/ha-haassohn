"""Real loopback HTTP server: no physical appliance or credentials required."""

import pytest
from aiohttp import web

from .emulator import StoveEmulator


@pytest.fixture
async def stove_server(unused_tcp_port):
    emulator = StoveEmulator()
    app = web.Application()
    app.router.add_route("*", "/status.cgi", emulator.handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", unused_tcp_port)
    await site.start()
    yield emulator, unused_tcp_port
    await runner.cleanup()
