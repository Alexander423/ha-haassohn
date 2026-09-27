"""Load real platforms, verify services, metadata, availability and lifecycle."""

import json
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.climate import HVACAction, HVACMode
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.haassohn import async_unload_entry
from custom_components.haassohn._vendor.pyhaassohn.codec import decode
from custom_components.haassohn.climate import HaasSohnClimate
from custom_components.haassohn.coordinator import HaasSohnCoordinator
from custom_components.haassohn.diagnostics import async_get_config_entry_diagnostics
from custom_components.haassohn.library import AuthenticationError, HaasSohnClient, HaasSohnError
from tests.emulator import profile


async def setup(hass, entry):
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_hyphenated_model_and_text_state(hass, entry, mock_client, caplog):
    """Real HA must publish string modes and the HSP-6 error description on reads."""
    data = profile()
    data["meta"]["typ"] = "HSP-6"
    data["meta"]["sw_version"] = "V5.10"
    data["meta"].pop("eco_editable", None)
    data["error"] = []
    mock_client.get_state.return_value = decode(json.dumps(data).encode())
    await setup(hass, entry)
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    mode_entity = next(
        e for e in entities if e.unique_id.endswith("_mode") and e.domain == "sensor"
    )
    error_entity = next(e for e in entities if e.unique_id.endswith("_error_description"))
    assert hass.states.get(mode_entity.entity_id).state == "off"
    assert hass.states.get(error_entity.entity_id).state == "no_entries"
    for mode in ("start", "heating", "cooling", "vendor_specific", "off"):
        data["mode"] = mode
        entry.runtime_data.async_set_updated_data(decode(json.dumps(data).encode()))
        await hass.async_block_till_done()
        assert hass.states.get(mode_entity.entity_id).state == mode
    data["error"] = [{"nr": 18}]
    entry.runtime_data.async_set_updated_data(decode(json.dumps(data).encode()))
    await hass.async_block_till_done()
    assert hass.states.get(error_entity.entity_id).state == "power_interruption"
    assert "Unexpected error updating listener" not in caplog.text
    for command in ("set_power", "set_target_temperature", "set_eco_mode", "set_week_program"):
        getattr(mock_client, command).assert_not_awaited()


async def test_setup_entities_and_services(hass, entry, mock_client, snapshot):
    await setup(hass, entry)
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert len(devices) == 1
    assert devices[0].serial_number == "SYNTHETIC-hsp6"
    climate = next(e for e in entities if e.domain == "climate")
    state = hass.states.get(climate.entity_id)
    assert state.state == "off"
    assert state.attributes["current_temperature"] == 20.5
    assert state.attributes["min_temp"] == 10
    assert state.attributes["max_temp"] == 30
    assert len([e for e in entities if e.domain == "climate"]) == 1
    assert not any(e.unique_id.endswith("_is_temp") for e in entities)
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": climate.entity_id, "temperature": 23},
        blocking=True,
    )
    mock_client.set_target_temperature.assert_awaited_once_with(23)
    await hass.services.async_call(
        "climate", "turn_on", {"entity_id": climate.entity_id}, blocking=True
    )
    mock_client.set_power.assert_awaited_with(True)
    await hass.services.async_call(
        "climate", "turn_off", {"entity_id": climate.entity_id}, blocking=True
    )
    mock_client.set_power.assert_awaited_with(False)
    for entity in [e for e in entities if e.domain == "switch"]:
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity.entity_id}, blocking=True
        )
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": entity.entity_id}, blocking=True
        )
    mock_client.set_eco_mode.assert_awaited_with(False)
    mock_client.set_week_program.assert_awaited_with(False)
    assert await hass.config_entries.async_unload(entry.entry_id)
    mock_client.close.assert_awaited_once()


async def test_coordinator_recovery(hass, entry, mock_client, snapshot):
    await setup(hass, entry)
    coordinator = entry.runtime_data
    mock_client.get_state.side_effect = HaasSohnError("private")
    for _ in range(5):
        await coordinator.async_refresh()
    assert not coordinator.last_update_success
    assert coordinator.update_interval == timedelta(seconds=300)
    assert all(
        state.state == "unavailable"
        for state in hass.states.async_all()
        if state.entity_id.startswith(("climate.", "sensor.", "switch.", "binary_sensor."))
    )
    mock_client.get_state.side_effect = None
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.update_interval == timedelta(seconds=30)
    assert any(s.state == "off" for s in hass.states.async_all("climate"))


async def test_auth_and_commands(hass, entry, mock_client, snapshot):
    entry.add_to_hass(hass)
    coordinator = HaasSohnCoordinator(hass, entry, mock_client)
    coordinator.async_set_updated_data(snapshot)
    mock_client.get_state.side_effect = AuthenticationError()
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()
    with patch.object(entry, "async_start_reauth") as reauth:
        with pytest.raises(HomeAssistantError):
            await coordinator.async_command(AsyncMock(side_effect=AuthenticationError()))
        reauth.assert_called_once()
    with pytest.raises(HomeAssistantError):
        await coordinator.async_command(AsyncMock(side_effect=HaasSohnError()))
    assert not coordinator.last_update_success


async def test_setup_failure_cleanup(hass, entry, mock_client):
    entry.add_to_hass(hass)
    mock_client.get_state.side_effect = HaasSohnError()
    assert not await hass.config_entries.async_setup(entry.entry_id)
    mock_client.close.assert_awaited_once()


async def test_unload_failure(hass, entry, mock_client):
    await setup(hass, entry)
    with patch.object(hass.config_entries, "async_unload_platforms", return_value=False):
        assert not await async_unload_entry(hass, entry)
    mock_client.close.assert_not_called()


@pytest.mark.parametrize(
    ("mode", "power", "action"),
    [
        ("off", False, HVACAction.OFF),
        ("off", True, HVACAction.IDLE),
        ("heating", True, HVACAction.HEATING),
        ("start", True, None),
        ("cooling", False, None),
        ("unknown", True, None),
    ],
)
async def test_climate_semantics(hass, entry, mock_client, mode, power, action):
    entry.add_to_hass(hass)
    data = profile()
    data.update(mode=mode, prg=power)
    coordinator = HaasSohnCoordinator(hass, entry, mock_client)
    coordinator.async_set_updated_data(decode(json.dumps(data).encode()))
    entity = HaasSohnClimate(coordinator, "prg")
    assert entity.hvac_action == action
    assert entity.hvac_mode == (HVACMode.HEAT if power else HVACMode.OFF)
    with pytest.raises(HomeAssistantError):
        await entity.async_set_hvac_mode(HVACMode.COOL)
    with pytest.raises(HomeAssistantError):
        await entity.async_set_temperature()


async def test_readonly_firmware_and_missing_values(hass, entry, mock_client):
    data = profile()
    data["meta"]["sw_version"] = "V99"
    data["tvl_temp"] = 60
    mock_client.get_state.return_value = decode(json.dumps(data).encode())
    await setup(hass, entry)
    assert not hass.states.async_all("climate")
    assert not hass.states.async_all("switch")
    assert len(hass.states.async_all("sensor")) > 5
    data["prg"] = None
    data["is_temp"] = None
    data["cleaning_in"] = None
    data["error"] = None
    entry.runtime_data.async_set_updated_data(decode(json.dumps(data).encode()))
    await hass.async_block_till_done()
    assert any(s.state == "unavailable" for s in hass.states.async_all("sensor"))


async def test_week_program_at_setup(hass, entry, mock_client):
    data = profile()
    data["wprg"] = True
    mock_client.get_state.return_value = decode(json.dumps(data).encode())
    await setup(hass, entry)
    assert hass.states.async_all("climate")


async def test_diagnostics(hass, entry, mock_client):
    await setup(hass, entry)
    with patch(
        "custom_components.haassohn.diagnostics.export_diagnostics", return_value={"safe": True}
    ):
        result = await async_get_config_entry_diagnostics(hass, entry)
    assert result == {"safe": True}
    assert "pin" not in result


@pytest.mark.usefixtures("socket_enabled")
async def test_real_http_end_to_end(hass, entry, stove_server):
    """Actual HA platform services -> library -> TCP emulator -> confirmed HA state."""
    emulator, port = stove_server
    real_client = HaasSohnClient("127.0.0.1", emulator.pin, port=port, record_unknown=True)
    with patch("custom_components.haassohn.HaasSohnClient", return_value=real_client):
        await setup(hass, entry)
    climate = hass.states.async_all("climate")[0]
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": climate.entity_id, "temperature": 24},
        blocking=True,
    )
    assert emulator.writes == [{"sp_temp": 24.0}]
    assert hass.states.get(climate.entity_id).attributes["temperature"] == 24
    diagnostic = await async_get_config_entry_diagnostics(hass, entry)
    encoded = json.dumps(diagnostic)
    assert "0246" not in encoded and "SYNTHETIC-" not in encoded and "127.0.0.1" not in encoded
    # Failed auth invokes reauth but never sends a second POST or optimistic state.
    emulator.reject = True
    with patch.object(entry, "async_start_reauth") as reauth:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                "climate", "turn_on", {"entity_id": climate.entity_id}, blocking=True
            )
        reauth.assert_called_once()
    assert hass.states.get(climate.entity_id).state == "off"
    assert emulator.requests.count("POST") == 2
    await hass.config_entries.async_unload(entry.entry_id)


async def test_runtime_capability_loss(hass, entry, mock_client):
    await setup(hass, entry)
    data = profile()
    data["meta"]["sw_version"] = "V99"
    data["room_mode"] = None
    data["error"] = None
    entry.runtime_data.async_set_updated_data(decode(json.dumps(data).encode()))
    await hass.async_block_till_done()
    assert all(s.state == "unavailable" for s in hass.states.async_all("switch"))
    assert hass.states.async_all("climate")[0].attributes["supported_features"] == 0
    # A fault history description is not guessed when the optional error field vanishes.
    assert any(s.state == "unavailable" for s in hass.states.async_all("sensor"))


async def test_no_optional_fields(hass, entry, mock_client):
    data = profile("hark")
    for key in ("error", "weekprogram", "eco_mode", "wprg", "room_mode"):
        data.pop(key)
    mock_client.get_state.return_value = decode(json.dumps(data).encode())
    await setup(hass, entry)
    assert not hass.states.async_all("switch")
