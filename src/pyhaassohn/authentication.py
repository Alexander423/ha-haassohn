"""Legacy challenge/response, mandated by the device (not modern encryption)."""

import re
from hashlib import md5

from .exceptions import InvalidValue, ProtocolError


def validate_pin(pin: str) -> None:
    """Preserve leading zeros; reject coercion and non-ASCII digits."""
    if not isinstance(pin, str) or re.fullmatch(r"[0-9]{4}", pin) is None:
        raise InvalidValue("APP PIN must contain four ASCII digits")


def sign(pin: str, nonce: str) -> str:
    """Return the lowercase MD5 of nonce + lowercase MD5 of the PIN."""
    validate_pin(pin)
    if not isinstance(nonce, str) or not nonce or len(nonce) > 256:
        raise ProtocolError("Missing or invalid authentication challenge")
    hashed_pin = md5(pin.encode("ascii"), usedforsecurity=False).hexdigest()
    return md5((nonce + hashed_pin).encode("utf-8"), usedforsecurity=False).hexdigest()
