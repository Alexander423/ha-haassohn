"""Public API for the legacy HAAS+SOHN local protocol."""

from .capabilities import FIELDS, Capabilities, Confidence
from .client import HaasSohnClient
from .models import DeviceInfo, StoveState

__all__ = ["FIELDS", "Capabilities", "Confidence", "DeviceInfo", "HaasSohnClient", "StoveState"]
__version__ = "0.1.0"
