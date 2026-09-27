"""Integration constants."""

from homeassistant.const import Platform

DOMAIN = "haassohn"
CONF_PIN = "pin"
CONF_IDENTITY = "device_identity"
PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]
