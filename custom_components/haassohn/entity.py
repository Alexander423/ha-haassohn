"""Common device association and snapshot-based availability."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HaasSohnCoordinator


class HaasSohnEntity(CoordinatorEntity[HaasSohnCoordinator]):
    """All entities of one physical appliance share the config-entry identity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: HaasSohnCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self.key = key
        entry = coordinator.config_entry
        assert entry is not None
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_translation_key = key
        info = coordinator.data.info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(entry.unique_id))},
            name=info.model,
            manufacturer=info.manufacturer,
            model=info.model,
            sw_version=info.firmware,
            hw_version=info.controller,
            serial_number=info.serial_number,
        )

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.values.get(self.key) is not None
