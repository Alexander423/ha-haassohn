"""Single import boundary for the standalone library.

HACS ships an exact generated copy until a public PyPI release is available.
Core migration replaces this module's imports with the published dependency.
"""

from ._vendor.pyhaassohn import FIELDS, HaasSohnClient, StoveState
from ._vendor.pyhaassohn.diagnostics import export_diagnostics
from ._vendor.pyhaassohn.errors import ERROR_KEYS, describe_error
from ._vendor.pyhaassohn.exceptions import (
    AuthenticationError,
    ConnectionError,
    DeviceChanged,
    HaasSohnError,
    InvalidValue,
    RequestTimeout,
    UnsupportedDevice,
)

__all__ = [
    "ERROR_KEYS",
    "describe_error",
    "FIELDS",
    "AuthenticationError",
    "ConnectionError",
    "DeviceChanged",
    "HaasSohnClient",
    "HaasSohnError",
    "InvalidValue",
    "RequestTimeout",
    "StoveState",
    "UnsupportedDevice",
    "export_diagnostics",
]
