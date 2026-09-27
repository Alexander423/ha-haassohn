"""Stable, credential-free exceptions. Never include response bodies or URLs."""


class HaasSohnError(Exception):
    """Base library error."""


class ConnectionError(HaasSohnError):
    """Device could not be reached or disconnected."""


class RequestTimeout(ConnectionError):
    """A bounded request timed out."""


class AuthenticationError(HaasSohnError):
    """Device rejected authentication (HTTP 401/403)."""


class ProtocolError(HaasSohnError):
    """Malformed, oversized, or unexpected response."""


class UnsupportedDevice(HaasSohnError):
    """Device does not identify as the supported legacy controller."""


class UnsupportedOperation(HaasSohnError):
    """No confirmed write capability in the current snapshot."""


class InvalidValue(HaasSohnError, ValueError):
    """Invalid outgoing value or connection option."""


class CommandNotConfirmed(HaasSohnError):
    """A write may have executed, but its result was not confirmed. Do not retry blindly."""


class DeviceChanged(HaasSohnError):
    """Hardware identity changed at the configured endpoint."""
