"""Wire correctness, capability restrictions, failure handling and privacy."""

import asyncio
import json
from hashlib import md5
from unittest.mock import AsyncMock

import aiohttp
import pytest

from pyhaassohn import FIELDS, Confidence, HaasSohnClient
from pyhaassohn.authentication import sign, validate_pin
from pyhaassohn.capabilities import KNOWN_FIRMWARE
from pyhaassohn.codec import decode
from pyhaassohn.diagnostics import export_diagnostics
from pyhaassohn.exceptions import (
    AuthenticationError,
    CommandNotConfirmed,
    ConnectionError,
    DeviceChanged,
    InvalidValue,
    ProtocolError,
    RequestTimeout,
    UnsupportedDevice,
    UnsupportedOperation,
)
from pyhaassohn.transport import Transport, validate_host

from .emulator import PROFILES, profile


def decoded(data=None, **kwargs):
    return decode(json.dumps(data if data is not None else profile()).encode(), **kwargs)


@pytest.mark.parametrize("model", ["HSP-6", "HSP 6", "HSP6", "hsp-6", "HSP 6 PALLAZZA III"])
def test_hsp_family_model_spellings(model):
    data = profile()
    data["meta"]["typ"] = model
    state = decoded(data)
    assert state.info.family == "HSP 6"
    assert state.info.model == model
    assert state.info.unique_id == decoded().info.unique_id
    assert state.capabilities == decoded().capabilities


@pytest.mark.parametrize("name", PROFILES)
def test_profiles(name):
    state = decoded(profile(name))
    assert state.info.firmware == PROFILES[name][1]
    assert state.info.unique_id == f"KS01:SYNTHETIC-{name}"
    assert state.values["cleaning_in"] == 2
    assert state.capabilities.can_set_target_temperature
    assert state.capabilities.confidence("sp_temp") == Confidence.CONFIRMED_WRITE
    assert state.capabilities.confidence("pgi") == Confidence.OBSERVED_READ_ONLY
    assert state.capabilities.confidence("tvl_temp") == Confidence.UNSUPPORTED
    assert state.capabilities.confidence("invented") == Confidence.UNKNOWN
    assert state.info.wifi_version == "V1.2.5"
    assert "synthetic-challenge" not in repr(state)
    assert "SYNTHETIC-" not in repr(state)


@pytest.mark.parametrize("firmware", KNOWN_FIRMWARE)
def test_firmware_allowlist(firmware):
    data = profile()
    data["meta"]["sw_version"] = firmware
    assert decoded(data).capabilities.writable == {"prg", "sp_temp", "wprg", "eco_mode"}


def test_unknown_firmware_and_restrictions():
    data = profile()
    data["meta"]["sw_version"] = "V99.1"
    assert not decoded(data).capabilities.writable
    assert "is_temp" in decoded(data).capabilities.readable
    data["meta"]["sw_version"] = "V7.08"
    data["meta"].pop("eco_editable")
    data["wprg"] = True
    assert decoded(data).capabilities.writable == {"prg", "wprg"}


@pytest.mark.parametrize("pin", ["123", "12345", 1234, "１２３４", "12a4", " 1234", None])
def test_bad_pins(pin):
    with pytest.raises(InvalidValue):
        validate_pin(pin)


def test_authentication_vector():
    digest = md5(b"0246").hexdigest()
    assert sign("0246", "synthetic") == md5(("synthetic" + digest).encode()).hexdigest()
    assert sign("0246", "a") != sign("0246", "b")


@pytest.mark.parametrize("nonce", ["", None, 7, "x" * 257])
def test_bad_nonce(nonce):
    with pytest.raises(ProtocolError):
        sign("0246", nonce)


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"{",
        b"[]",
        b"null",
        b"{}",
        b"\xff",
        b'{"meta":{},"x":1,"x":2}',
        b'{"meta":{},"x":NaN}',
        b"x" * 65537,
        b"[" * 2000 + b"]" * 2000,
    ],
    ids=[
        "empty",
        "partial",
        "array",
        "null",
        "object",
        "utf8",
        "duplicate",
        "nan",
        "oversized",
        "deep",
    ],
)
def test_malformed(body):
    with pytest.raises(ProtocolError):
        decode(body)


@pytest.mark.parametrize(
    "meta", [{}, {"hw_version": "FUMIS"}, {"hw_version": "KS01", "sw_version": "V7.08"}]
)
def test_unsupported(meta):
    with pytest.raises(UnsupportedDevice):
        decoded({"meta": meta})


def test_no_operating_fields():
    with pytest.raises(ProtocolError):
        decoded({"meta": profile()["meta"]})


@pytest.mark.parametrize("value", [True, None, {}, [], "bad", "nan", "inf", 10**200, -1])
def test_invalid_counter(value):
    data = profile()
    data["on_time"] = value
    assert decoded(data).values["on_time"] is None


@pytest.mark.parametrize("value", [[], {}, None, 1, "", "x" * 129])
def test_invalid_mode(value):
    data = profile()
    data["mode"] = value
    assert decoded(data).values["mode"] is None


@pytest.mark.parametrize("value", [None, {}, [4], [{"nr": -1}], [{"nr": True}], [{"nr": "oops"}]])
def test_invalid_errors(value):
    data = profile()
    data["error"] = value
    assert decoded(data).values["error"] is None


def test_errors_schedule_and_optional_fields():
    data = profile()
    data["error"] = [{"nr": "18", "time": "private"}, {"nr": 41}]
    data["is_temp"] = "21.4"
    data["eco_mode"] = 1
    data["tvl_temp"] = 60
    state = decoded(data)
    assert state.values["error"] == (18, 41)
    assert state.values["is_temp"] == 21.4
    assert state.values["eco_mode"] is None
    assert state.values["weekprogram"][0]["temp"] == 21
    with pytest.raises(TypeError):
        state.values["weekprogram"][0]["temp"] = 99
    assert state.capabilities.confidence("tvl_temp") == Confidence.MODEL_SPECIFIC


@pytest.mark.parametrize("value", [None, [1], [{}], [{"day": "x" * 40}], list(range(129))])
def test_invalid_schedules(value):
    data = profile()
    data["weekprogram"] = value
    assert decoded(data).values["weekprogram"] is None


@pytest.mark.parametrize("serial", [None, "", "0000", "unknown", "n/a", "none"])
def test_missing_serial(serial):
    data = profile()
    data["meta"]["sn"] = serial
    assert decoded(data).info.unique_id is None


@pytest.mark.parametrize("value", [True, None, "21", 9, 31, 21.5, float("inf"), float("nan")])
async def test_invalid_temperature_no_io(value):
    async with HaasSohnClient("localhost", "0246") as client:
        with pytest.raises(InvalidValue):
            await client.set_target_temperature(value)
        assert client.stats.requests == 0


@pytest.mark.parametrize("key", ["prg", "eco_mode", "wprg"])
@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_boolean_validation(key, value):
    with pytest.raises(InvalidValue):
        FIELDS[key].validate_write(value)


@pytest.mark.parametrize(
    "host",
    [
        "http://localhost",
        "host/path",
        "a@b",
        "x:80",
        " a",
        "a b",
        "",
        None,
        "-a",
        "a-",
        "a..b",
        "a" * 254,
    ],
)
def test_invalid_hosts(host):
    with pytest.raises(InvalidValue):
        validate_host(host)


@pytest.mark.parametrize(
    ("host", "expected"),
    [("LOCALHOST.", "localhost"), ("127.0.0.1", "127.0.0.1"), ("::1", "[::1]")],
)
def test_hosts(host, expected):
    assert validate_host(host) == expected


@pytest.mark.parametrize(
    "kwargs",
    [{"port": 0}, {"port": True}, {"timeout": 0}, {"timeout": 121}, {"timeout": float("nan")}],
)
def test_transport_options(kwargs):
    with pytest.raises(InvalidValue):
        Transport("localhost", **kwargs)


async def test_read_write_and_serialization(stove_server):
    emulator, port = stove_server
    async with HaasSohnClient("127.0.0.1", emulator.pin, port=port) as client:
        assert not client.capabilities.readable
        assert (await client.get_device_info()).controller == "KS01"
        assert not client.authentication_verified
        await asyncio.gather(
            client.set_power(True),
            client.set_target_temperature(22),
            client.set_eco_mode(True),
            client.set_week_program(True),
        )
        assert emulator.requests == ["GET"] + ["GET", "POST", "GET"] * 4
        assert len(emulator.writes) == 4
        with pytest.raises(UnsupportedOperation):
            await client.set_target_temperature(24)
        await client.set_week_program(False)
        assert client.stats.writes == 5
        assert client.stats.failures == 0
    assert client._transport._session is None


async def test_invalid_auth_and_no_retries(stove_server):
    emulator, port = stove_server
    async with HaasSohnClient("127.0.0.1", "9999", port=port) as client:
        await client.get_state()  # GET cannot validate a PIN.
        with pytest.raises(AuthenticationError):
            await client.set_power(True)
        assert emulator.requests == ["GET", "GET", "POST"]
        assert client.stats.failures == 1
        assert not client.authentication_verified


async def test_confirmation_mismatch(stove_server):
    emulator, port = stove_server
    emulator.ignore_write = True
    async with HaasSohnClient("127.0.0.1", emulator.pin, port=port) as client:
        with pytest.raises(CommandNotConfirmed):
            await client.set_power(True)
        assert client.state.values["prg"] is False
        assert len(emulator.writes) == 1


async def test_identity_change_and_firmware_change(stove_server):
    emulator, port = stove_server
    async with HaasSohnClient("127.0.0.1", emulator.pin, port=port) as client:
        await client.get_state()
        emulator.data["meta"]["sw_version"] = "V99"
        with pytest.raises(UnsupportedOperation):
            await client.set_power(True)
        emulator.data["meta"]["sn"] = "OTHER-SYNTHETIC"
        with pytest.raises(DeviceChanged):
            await client.set_power(True)
        assert not emulator.writes


async def test_transport_failure_recovery(stove_server):
    emulator, port = stove_server
    async with HaasSohnClient("127.0.0.1", emulator.pin, port=port) as client:
        emulator.status = 503
        with pytest.raises(ProtocolError):
            await client.get_state()
        emulator.status = 200
        assert (await client.get_state()).values["is_temp"] == 20.5
        assert client.stats.failures == 1


async def test_unreachable(unused_tcp_port):
    async with HaasSohnClient("127.0.0.1", "0246", port=unused_tcp_port) as client:
        with pytest.raises(ConnectionError):
            await client.get_state()


async def test_timeout_and_cancellation():
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.request.side_effect = TimeoutError
    transport = Transport("localhost", session=session)
    with pytest.raises(RequestTimeout):
        await transport.request()
    session.request.side_effect = asyncio.CancelledError
    with pytest.raises(asyncio.CancelledError):
        await transport.request()
    await transport.close()
    session.close.assert_not_called()


async def test_uncertain_write_and_readback_failures(stove_server):
    emulator, port = stove_server
    async with HaasSohnClient("127.0.0.1", emulator.pin, port=port) as client:
        client._transport.request = AsyncMock(
            side_effect=[json.dumps(profile()).encode(), RequestTimeout("timeout")]
        )
        with pytest.raises(CommandNotConfirmed):
            await client.set_power(True)
        client._transport.request = AsyncMock(
            side_effect=[json.dumps(profile()).encode(), b"", ConnectionError("lost")]
        )
        with pytest.raises(CommandNotConfirmed):
            await client.set_power(True)


async def test_diagnostics_redaction(stove_server):
    emulator, port = stove_server
    async with HaasSohnClient("127.0.0.1", emulator.pin, port=port, record_unknown=True) as client:
        assert set(export_diagnostics(client)) == {"communication"}
        emulator.data.update(
            {
                "mystery": True,
                "number": 123456,
                "text": "secret",
                "nonce": "secret",
                "PIN": "secret",
                "bad key": "secret",
            }
        )
        emulator.data["meta"]["ssid"] = "secret"
        await client.get_state()
        exported = export_diagnostics(client)
        encoded = json.dumps(exported)
        for private in [emulator.pin, "synthetic-", "SYNTHETIC-", "secret", "123456", "127.0.0.1"]:
            assert private not in encoded
        assert exported["unknown"]["mystery"]["raw"] is True
        assert exported["unknown"]["number"]["raw"] == "[redacted]"
        emulator.data["meta"]["sw_version"] = "private firmware"
        await client.get_state()
        assert export_diagnostics(client)["device"]["firmware"] == "[redacted]"
        emulator.data["meta"]["typ"] = "HSP-6"
        await client.get_state()
        assert export_diagnostics(client)["device"]["model"] == "HSP-6"
        assert export_diagnostics(client)["device"]["family"] == "HSP 6"
        emulator.data["meta"]["typ"] = "private model"
        emulator.data["meta"].pop("wifi_sw_version")
        await client.get_state()
        exported = export_diagnostics(client)
        assert exported["device"]["model"] == "[unrecognized model]"
        assert exported["device"]["wifi_version"] is None
