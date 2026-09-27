"""Shareable diagnostics; config data is intentionally never copied."""

from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import HaasSohnConfigEntry
from .library import export_diagnostics


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HaasSohnConfigEntry
) -> dict[str, Any]:
    return export_diagnostics(entry.runtime_data.client)
