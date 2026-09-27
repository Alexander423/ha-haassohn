"""TEST ONLY: synthetic legacy HTTP emulator, not a hardware compatibility claim."""

from copy import deepcopy
from hashlib import md5
from typing import Any

from aiohttp import web

PROFILES = {
    "hsp2": ("HSP 2.17 PREMIUM III", "V7.02"),
    "hsp6": ("HSP 6 PELLETTO IV 419.08", "V7.08"),
    "hsp7": ("HSP 7 DIANA", "V7.04-oKV"),
    "hsp8": ("HSP 8 CATANIA II 444.08-ST", "V5.10"),
    "hark": ("Hark Ecomat 6", "V6.01"),
}


def profile(name: str = "hsp6") -> dict[str, Any]:
    model, version = PROFILES[name]
    return {
        "meta": {
            "hw_version": "KS01",
            "sw_version": version,
            "typ": model,
            "sn": f"SYNTHETIC-{name}",
            "nonce": "synthetic-challenge",
            "wifi_sw_version": "V1.2.5",
            "wifi_bootl_version": "V1.0",
            "bootl_version": "V1.0",
            "eco_editable": True,
        },
        "prg": False,
        "wprg": False,
        "sp_temp": 21,
        "is_temp": 20.5,
        "eco_mode": False,
        "mode": "off",
        "ignitions": 123,
        "on_time": 500,
        "consumption": 200,
        "maintenance_in": 800,
        "cleaning_in": 120,
        "room_mode": True,
        "ht_char": 2,
        "zone": 0,
        "pgi": False,
        "error": [],
        "weekprogram": [{"day": "1", "begin": "06:00", "end": "08:00", "temp": 21}],
    }


class StoveEmulator:
    """Independently computes authentication and accepts only published commands."""

    def __init__(self, name: str = "hsp6") -> None:
        self.data = deepcopy(profile(name))
        self.pin = "0246"  # Synthetic test-only credential, never a real stove PIN.
        self.requests: list[str] = []
        self.writes: list[dict[str, Any]] = []
        self.reject = False
        self.ignore_write = False
        self.status = 200

    async def handle(self, request: web.Request) -> web.Response:
        self.requests.append(request.method)
        if self.status != 200:
            return web.Response(status=self.status)
        if request.method == "POST":
            digest = md5(self.pin.encode()).hexdigest()
            expected = md5((self.data["meta"]["nonce"] + digest).encode()).hexdigest()
            if self.reject or request.headers.get("X-HS-PIN") != expected:
                return web.Response(status=403)
            value = await request.json()
            assert len(value) == 1 and set(value) <= {"prg", "sp_temp", "eco_mode", "wprg"}
            self.writes.append(value)
            if not self.ignore_write:
                self.data.update(value)
        self.data["meta"]["nonce"] = f"synthetic-{len(self.requests)}"
        return web.json_response(self.data)
