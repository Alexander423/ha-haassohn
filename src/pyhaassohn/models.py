"""Immutable decoded snapshots; device identities are excluded from repr."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .capabilities import Capabilities


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    manufacturer: str
    model: str
    family: str | None
    firmware: str
    controller: str
    serial_number: str | None = field(repr=False)
    wifi_version: str | None = None
    boot_version: str | None = None
    wifi_boot_version: str | None = None
    protocol: str = "legacy-status-json"

    @property
    def unique_id(self) -> str | None:
        """Identity uses controller and manufacturer serial, never an address or PIN."""
        if self.serial_number is None:
            return None
        return f"{self.controller}:{self.serial_number}"


@dataclass(frozen=True, slots=True)
class StoveState:
    info: DeviceInfo
    values: Mapping[str, Any]
    capabilities: Capabilities
    received_at: datetime = field(compare=False)
    unknown: Mapping[str, Any] = field(repr=False, compare=False)
    nonce: str | None = field(repr=False, compare=False)


@dataclass(slots=True)
class CommunicationStats:
    requests: int = 0
    failures: int = 0
    writes: int = 0
    last_success: datetime | None = None
