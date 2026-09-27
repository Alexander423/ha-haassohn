"""Only confirmed boolean states and derived maintenance thresholds."""

from typing import cast

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import HaasSohnConfigEntry, HaasSohnCoordinator
from .entity import HaasSohnEntity
from .library import FIELDS


async def async_setup_entry(
    hass: HomeAssistant, entry: HaasSohnConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    capabilities = coordinator.data.capabilities
    climate_present = capabilities.known_firmware and {"prg", "sp_temp"} <= capabilities.readable
    async_add_entities(
        HaasSohnBinarySensor(coordinator, key)
        for key in capabilities.readable
        if FIELDS[key].kind == "bool"
        and key not in capabilities.writable
        and key != "pgi"
        and not (key == "prg" and climate_present)
    )
    async_add_entities(
        HaasSohnBinarySensor(coordinator, key)
        for key in ("cleaning_in", "maintenance_in")
        if key in capabilities.readable
    )


class HaasSohnBinarySensor(HaasSohnEntity, BinarySensorEntity):
    def __init__(self, coordinator: HaasSohnCoordinator, key: str) -> None:
        super().__init__(coordinator, key)
        if key in {"cleaning_in", "maintenance_in"}:
            self._attr_translation_key = key + "_due"
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.values.get(self.key)
        if value is None:
            return None
        return value <= 0 if self.key in {"cleaning_in", "maintenance_in"} else cast(bool, value)
