"""Capabilities select scalar sensors and their statistics metadata."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import HaasSohnConfigEntry, HaasSohnCoordinator
from .entity import HaasSohnEntity
from .library import ERROR_KEYS, FIELDS, describe_error


async def async_setup_entry(
    hass: HomeAssistant, entry: HaasSohnConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    climate_present = (
        coordinator.data.capabilities.known_firmware
        and {"prg", "sp_temp"} <= coordinator.data.capabilities.readable
    )
    async_add_entities(
        HaasSohnSensor(coordinator, key)
        for key in coordinator.data.capabilities.readable
        if FIELDS[key].kind in {"number", "text"}
        and not (climate_present and key in {"sp_temp", "is_temp"})
    )
    if "error" in coordinator.data.capabilities.readable:
        async_add_entities([ErrorCodesSensor(coordinator, "error")])
        if coordinator.data.info.family in {"HSP 2", "HSP 6", "HSP 7", "HSP 8"}:
            async_add_entities([ReportedErrorSensor(coordinator, "error")])


class HaasSohnSensor(HaasSohnEntity, SensorEntity):
    def __init__(self, coordinator: HaasSohnCoordinator, key: str) -> None:
        super().__init__(coordinator, key)
        definition = FIELDS[key]
        self._attr_native_unit_of_measurement = definition.unit
        self._attr_device_class = {
            "°C": SensorDeviceClass.TEMPERATURE,
            "h": SensorDeviceClass.DURATION,
            "kg": SensorDeviceClass.WEIGHT,
        }.get(definition.unit or "")
        if definition.total:
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif definition.unit == "°C":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        if definition.kind == "number":
            self._attr_suggested_display_precision = 1 if definition.unit in {"°C", "h"} else 0
        if definition.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if key in {"zone", "ht_char", "tvl_temp"}:
            self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> str | float | None:
        return self.coordinator.data.values.get(self.key)


class ErrorCodesSensor(HaasSohnEntity, SensorEntity):
    """Reported codes may be history; never label them as an active fault."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> int | None:
        codes = self.coordinator.data.values.get("error")
        return len(codes) if codes is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, list[int]]:
        return {"codes": list(self.coordinator.data.values.get("error") or ())}


class ReportedErrorSensor(HaasSohnEntity, SensorEntity):
    """Translate the first reported entry without claiming it is latest or active."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = sorted(set(ERROR_KEYS.values()) | {"unknown_code", "no_entries"})

    def __init__(self, coordinator: HaasSohnCoordinator, key: str) -> None:
        super().__init__(coordinator, key)
        self._attr_unique_id = f"{self._attr_unique_id}_description"
        self._attr_translation_key = "reported_error"

    @property
    def native_value(self) -> str | None:
        codes = self.coordinator.data.values.get("error")
        if codes is None:
            return None
        return describe_error(codes[0]) if codes else "no_entries"
