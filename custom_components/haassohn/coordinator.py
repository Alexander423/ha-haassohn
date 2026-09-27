"""One snapshot per poll; exponential backoff for old WLAN controllers."""

import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .library import AuthenticationError, HaasSohnClient, HaasSohnError, StoveState

_LOGGER = logging.getLogger(__name__)
type HaasSohnConfigEntry = ConfigEntry[HaasSohnCoordinator]


class HaasSohnCoordinator(DataUpdateCoordinator[StoveState]):
    """Own connection state and publish only device-confirmed values."""

    def __init__(
        self, hass: HomeAssistant, entry: HaasSohnConfigEntry, client: HaasSohnClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
            always_update=False,
        )
        self.client = client
        self._failures = 0

    async def _async_update_data(self) -> StoveState:
        try:
            state = await self.client.get_state()
        except AuthenticationError:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from None
        except HaasSohnError:
            self._failures = min(self._failures + 1, 4)
            self.update_interval = timedelta(seconds=min(30 * 2**self._failures, 300))
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="cannot_connect"
            ) from None
        self._failures = 0
        self.update_interval = timedelta(seconds=30)
        return state

    async def async_command(self, operation: Callable[[], Awaitable[StoveState]]) -> None:
        """Run a command and refresh the shared snapshot without optimistic updates."""
        try:
            state = await operation()
        except AuthenticationError:
            assert self.config_entry is not None
            self.config_entry.async_start_reauth(self.hass)
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from None
        except HaasSohnError:
            # A failed readback must not leave old values presented as current.
            self.async_set_update_error(UpdateFailed("Command could not be confirmed"))
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="command_failed"
            ) from None
        self.async_set_updated_data(state)
