"""Bounded local HTTP transport. No redirects, proxy environment or automatic write retries."""

import asyncio
import ipaddress
import re
from collections.abc import Mapping

import aiohttp

from .codec import MAX_RESPONSE_BYTES
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    InvalidValue,
    ProtocolError,
    RequestTimeout,
)


def validate_host(host: str) -> str:
    """Accept a hostname or IPv4/IPv6 literal, never URL credentials or paths."""
    if not isinstance(host, str) or not host or host != host.strip():
        raise InvalidValue("Invalid host")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if (
            len(host) > 253
            or re.fullmatch(r"[A-Za-z0-9.-]+", host) is None
            or any(
                not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
                for label in host.rstrip(".").split(".")
            )
        ):
            raise InvalidValue("Invalid host") from None
        return host.lower().rstrip(".")
    return f"[{address}]" if address.version == 6 else str(address)


class Transport:
    """Session owner or borrower; borrowed sessions are never closed."""

    def __init__(
        self,
        host: str,
        *,
        session: aiohttp.ClientSession | None = None,
        timeout: float = 10,
        port: int = 80,
    ) -> None:
        if type(port) is not int or not 1 <= port <= 65535:
            raise InvalidValue("Invalid port")
        if type(timeout) not in (float, int) or not 0 < timeout <= 120:
            raise InvalidValue("Timeout must be between zero and 120 seconds")
        self._url = f"http://{validate_host(host)}:{port}/status.cgi"
        self._session = session
        self._owned = session is None
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def close(self) -> None:
        if self._owned and self._session is not None:
            await self._session.close()
            self._session = None

    async def request(
        self,
        method: str = "GET",
        *,
        body: bytes | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> bytes:
        if self._session is None:
            self._session = aiohttp.ClientSession(
                trust_env=False, cookie_jar=aiohttp.DummyCookieJar()
            )
        try:
            async with self._session.request(
                method,
                self._url,
                data=body,
                headers=headers,
                timeout=self._timeout,
                allow_redirects=False,
            ) as response:
                if response.status in (401, 403):
                    raise AuthenticationError("Device rejected authentication")
                if response.status != 200:
                    raise ProtocolError("Unexpected HTTP status")
                result = bytearray()
                async for chunk in response.content.iter_chunked(4096):
                    result.extend(chunk)
                    if len(result) > MAX_RESPONSE_BYTES:
                        raise ProtocolError("Response exceeds size limit")
                return bytes(result)
        except TimeoutError:
            raise RequestTimeout("Device request timed out") from None
        except (aiohttp.ClientError, OSError):
            raise ConnectionError("Device connection failed") from None
        except asyncio.CancelledError:
            # The response context manager releases the connection on cancellation.
            raise
