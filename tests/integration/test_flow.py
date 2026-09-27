"""Exercise real HA flow manager: all errors, duplicate identity, reconfigure, reauth."""

from dataclasses import replace
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.haassohn.const import DOMAIN
from custom_components.haassohn.library import (
    AuthenticationError,
    ConnectionError,
    HaasSohnError,
    InvalidValue,
    RequestTimeout,
    UnsupportedDevice,
)

DATA = {"host": "stove.invalid", "pin": "0246"}


async def test_user(hass, mock_client):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    with patch("custom_components.haassohn.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "KS01:SYNTHETIC-hsp6"
    assert result["data"]["device_identity"] == "KS01:SYNTHETIC-hsp6"
    mock_client.set_power.assert_not_called()


@pytest.mark.parametrize(
    ("error", "key"),
    [
        (InvalidValue, "invalid_input"),
        (AuthenticationError, "invalid_auth"),
        (RequestTimeout, "timeout"),
        (ConnectionError, "cannot_connect"),
        (UnsupportedDevice, "unsupported_device"),
        (HaasSohnError, "unknown"),
    ],
)
async def test_errors(hass, mock_client, error, key):
    mock_client.get_device_info.side_effect = error("synthetic private details")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=DATA
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": key}
    assert "private" not in str(result)


@pytest.mark.parametrize("host", ["stove.invalid", "new.invalid"])
async def test_duplicate(hass, entry, mock_client, host):
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={**DATA, "host": host}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize("source", [SOURCE_RECONFIGURE, SOURCE_REAUTH])
async def test_update(hass, entry, mock_client, source):
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source, "entry_id": entry.entry_id},
        data=entry.data if source == SOURCE_REAUTH else None,
    )
    assert result["type"] is FlowResultType.FORM
    with patch("custom_components.haassohn.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**DATA, "host": "new.invalid"}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] in {"reauth_successful", "reconfigure_successful"}
    assert entry.data["host"] == "new.invalid"
    assert entry.unique_id == "KS01:SYNTHETIC-hsp6"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


async def test_wrong_device(hass, entry, mock_client, snapshot):
    entry.add_to_hass(hass)
    mock_client.get_device_info.return_value = replace(snapshot.info, serial_number="OTHER")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}, data=DATA
    )
    assert result["reason"] == "wrong_device"


async def test_no_serial_fallback(hass, mock_client, snapshot):
    mock_client.get_device_info.return_value = replace(snapshot.info, serial_number=None)
    with patch("custom_components.haassohn.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=DATA
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id.startswith("local-")
    assert result["data"]["device_identity"] is None


async def test_reconfigure_fallback_duplicate_identity(hass, entry, mock_client):
    entry.add_to_hass(hass)
    anonymous = MockConfigEntry(
        domain=DOMAIN,
        unique_id="local-synthetic",
        data={**DATA, "host": "anonymous.invalid", "device_identity": None},
    )
    anonymous.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": anonymous.entry_id}, data=DATA
    )
    assert result["reason"] == "already_configured"


async def test_reconfigure_fallback_acquires_serial(hass, entry, mock_client):
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        entry, unique_id="local-synthetic", data={**DATA, "device_identity": None}
    )
    with patch("custom_components.haassohn.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}, data=DATA
        )
        await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == "local-synthetic"
    assert entry.data["device_identity"] == "KS01:SYNTHETIC-hsp6"
