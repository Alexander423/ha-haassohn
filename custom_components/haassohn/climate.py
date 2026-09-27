"""Primary heat/temperature control; do not infer combustion state from power intent."""

from typing import Any, cast

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import HaasSohnConfigEntry
from .entity import HaasSohnEntity
from .library import FIELDS


async def async_setup_entry(
    hass: HomeAssistant, entry: HaasSohnConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    if {"prg", "sp_temp"} <= coordinator.data.capabilities.writable:
        async_add_entities([HaasSohnClimate(coordinator, "prg")])
    elif {
        "prg",
        "sp_temp",
    } <= coordinator.data.capabilities.readable and coordinator.data.capabilities.known_firmware:
        # Week program can temporarily disable target writes; keep the main entity.
        async_add_entities([HaasSohnClimate(coordinator, "prg")])


class HaasSohnClimate(HaasSohnEntity, ClimateEntity):
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_min_temp = cast(float, FIELDS["sp_temp"].minimum)
    _attr_max_temp = cast(float, FIELDS["sp_temp"].maximum)
    _attr_target_temperature_step = FIELDS["sp_temp"].step

    @property
    def available(self) -> bool:
        return super().available and "prg" in self.coordinator.data.capabilities.writable

    @property
    def supported_features(self) -> ClimateEntityFeature:
        writable = self.coordinator.data.capabilities.writable
        features = ClimateEntityFeature(0)
        if "prg" in writable:
            features |= ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        if "sp_temp" in writable:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        return features

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.values.get("is_temp")

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.values.get("sp_temp")

    @property
    def hvac_mode(self) -> HVACMode | None:
        value = self.coordinator.data.values.get("prg")
        return None if value is None else HVACMode.HEAT if value else HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction | None:
        mode = self.coordinator.data.values.get("mode")
        if mode == "heating":
            return HVACAction.HEATING
        if mode == "off":
            return HVACAction.IDLE if self.hvac_mode == HVACMode.HEAT else HVACAction.OFF
        # Start/ignition, cooling and unknown vendor modes have no exact HA action.
        return None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode not in self.hvac_modes:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="invalid_value")
        await self.coordinator.async_command(
            lambda: self.coordinator.client.set_power(hvac_mode == HVACMode.HEAT)
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if ATTR_TEMPERATURE not in kwargs:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="invalid_value")
        await self.coordinator.async_command(
            lambda: self.coordinator.client.set_target_temperature(kwargs[ATTR_TEMPERATURE])
        )

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)
