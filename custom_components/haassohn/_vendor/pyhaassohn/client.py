"""Asynchronous high-level client with serialized read/challenge/write/readback cycles."""

import asyncio
import json
from datetime import UTC, datetime
from types import TracebackType

import aiohttp

from .authentication import sign, validate_pin
from .capabilities import FIELDS, Capabilities
from .codec import decode
from .exceptions import (
    AuthenticationError,
    CommandNotConfirmed,
    DeviceChanged,
    HaasSohnError,
    UnsupportedOperation,
)
from .models import CommunicationStats, DeviceInfo, StoveState
from .transport import Transport


class HaasSohnClient:
    """Local legacy client. Reads cannot authenticate the PIN; see docs/protocol.md."""

    def __init__(
        self,
        host: str,
        pin: str,
        *,
        session: aiohttp.ClientSession | None = None,
        timeout: float = 10,
        port: int = 80,
        record_unknown: bool = False,
        expected_unique_id: str | None = None,
    ) -> None:
        validate_pin(pin)
        self._pin = pin
        self._transport = Transport(host, session=session, timeout=timeout, port=port)
        self._lock = asyncio.Lock()
        self._record_unknown = record_unknown
        self._identity = expected_unique_id
        self._state: StoveState | None = None
        self.stats = CommunicationStats()
        self.authentication_verified = False

    async def __aenter__(self) -> "HaasSohnClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Finish any active transaction and close only an owned session."""
        async with self._lock:
            await self._transport.close()

    @property
    def capabilities(self) -> Capabilities:
        return (
            self._state.capabilities
            if self._state
            else Capabilities(frozenset(), frozenset(), False)
        )

    @property
    def state(self) -> StoveState | None:
        return self._state

    async def _read(self) -> StoveState:
        self.stats.requests += 1
        try:
            state = decode(await self._transport.request(), record_unknown=self._record_unknown)
            if self._identity is not None and state.info.unique_id != self._identity:
                raise DeviceChanged("Device identity changed")
            self._identity = state.info.unique_id
        except HaasSohnError:
            self.stats.failures += 1
            raise
        self._state = state
        self.stats.last_success = datetime.now(UTC)
        return state

    async def get_state(self) -> StoveState:
        async with self._lock:
            return await self._read()

    async def get_device_info(self) -> DeviceInfo:
        return (await self.get_state()).info

    async def set_power(self, enabled: bool) -> StoveState:
        return await self._write("prg", enabled)

    async def set_target_temperature(self, temperature: float) -> StoveState:
        return await self._write("sp_temp", temperature)

    async def set_eco_mode(self, enabled: bool) -> StoveState:
        return await self._write("eco_mode", enabled)

    async def set_week_program(self, enabled: bool) -> StoveState:
        """Enable the stored program; does not edit schedule slots."""
        return await self._write("wprg", enabled)

    async def _write(self, key: str, value: object) -> StoveState:
        definition = FIELDS[key]
        value = definition.validate_write(value)
        async with self._lock:
            state = await self._read()  # Fresh nonce and fresh restrictions, even after reboot.
            if key not in state.capabilities.writable:
                raise UnsupportedOperation("Command is not confirmed for the current device state")
            token = sign(self._pin, state.nonce or "")
            payload = json.dumps({key: value}, separators=(",", ":"), allow_nan=False).encode()
            self.stats.requests += 1
            self.stats.writes += 1
            try:
                await self._transport.request(
                    "POST",
                    body=payload,
                    headers={"X-HS-PIN": token, "Content-Type": "application/json"},
                )
            except AuthenticationError:
                self.authentication_verified = False
                self.stats.failures += 1
                raise
            except HaasSohnError:
                self.stats.failures += 1
                raise CommandNotConfirmed("Write outcome is uncertain; inspect the stove") from None
            try:
                result = await self._read()
            except HaasSohnError:
                raise CommandNotConfirmed("Unable to read back the command result") from None
            if result.values.get(key) != value:
                raise CommandNotConfirmed("Device did not confirm the requested value")
            # A 200 response alone does not prove authentication. This means the
            # command was accepted and its requested state read back, not a login.
            self.authentication_verified = state.values.get(key) != value
            return result
