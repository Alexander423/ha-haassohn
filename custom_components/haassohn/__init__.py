"""Direct local HAAS+SOHN stove integration."""

from homeassistant.core import HomeAssistant

from .const import CONF_IDENTITY, CONF_PIN, PLATFORMS
from .coordinator import HaasSohnConfigEntry, HaasSohnCoordinator
from .library import HaasSohnClient


async def async_setup_entry(hass: HomeAssistant, entry: HaasSohnConfigEntry) -> bool:
    """Start a single coordinator; clean up even when the first refresh fails."""
    client = HaasSohnClient(
        entry.data["host"],
        entry.data[CONF_PIN],
        expected_unique_id=entry.data.get(CONF_IDENTITY),
        record_unknown=True,
    )
    coordinator = HaasSohnCoordinator(hass, entry, client)
    try:
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        # Also covers cancellation; an owned HTTP session must not leak on setup failure.
        await client.close()
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HaasSohnConfigEntry) -> bool:
    """Stop entity polling before closing the session."""
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.client.close()
        return True
    return False
