"""Home Assistant's real test harness with only the appliance boundary mocked."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.haassohn._vendor.pyhaassohn.codec import decode
from custom_components.haassohn.const import DOMAIN
from tests.emulator import profile


@pytest.fixture(autouse=True)
def enable_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def snapshot():
    return decode(json.dumps(profile()).encode())


@pytest.fixture
def entry():
    return MockConfigEntry(
        domain=DOMAIN,
        title="Synthetic stove",
        unique_id="KS01:SYNTHETIC-hsp6",
        data={"host": "stove.invalid", "pin": "0246", "device_identity": "KS01:SYNTHETIC-hsp6"},
    )


@pytest.fixture
def mock_client(snapshot):
    client = AsyncMock()
    client.get_state.return_value = snapshot
    client.get_device_info.return_value = snapshot.info
    client.__aenter__.return_value = client
    client.set_power.return_value = snapshot
    client.set_target_temperature.return_value = snapshot
    client.set_eco_mode.return_value = snapshot
    client.set_week_program.return_value = snapshot
    with (
        patch("custom_components.haassohn.HaasSohnClient", return_value=client),
        patch("custom_components.haassohn.config_flow.HaasSohnClient", return_value=client),
    ):
        yield client
