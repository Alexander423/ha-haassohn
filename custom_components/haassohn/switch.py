"""Eco and stored weekly program activation; power belongs to climate."""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import HaasSohnConfigEntry
from .entity import HaasSohnEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: HaasSohnConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        HaasSohnSwitch(coordinator, key)
        for key in ("eco_mode", "wprg")
        if key in coordinator.data.capabilities.writable
    )


class HaasSohnSwitch(HaasSohnEntity, SwitchEntity):
    @property
    def available(self) -> bool:
        return super().available and self.key in self.coordinator.data.capabilities.writable

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.values.get(self.key)

    async def _set(self, enabled: bool) -> None:
        operation = (
            self.coordinator.client.set_eco_mode
            if self.key == "eco_mode"
            else self.coordinator.client.set_week_program
        )
        await self.coordinator.async_command(lambda: operation(enabled))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
