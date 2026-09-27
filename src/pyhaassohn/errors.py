"""Conservative manual code descriptions, not active-fault detection or repair advice.

Evidence: MAN, printed pages 20–22; numeric error.nr wire shape IO/OH/BR.
The protocol does not retain an F/W severity prefix. Unknown codes stay unknown.
"""

from types import MappingProxyType

ERROR_KEYS = MappingProxyType(
    {
        7: "exhaust_sensor",
        8: "exhaust_sensor",
        9: "door_open_idle",
        11: "room_sensor",
        12: "room_sensor_short",
        15: "exhaust_fan",
        18: "power_interruption",
        23: "flame_sensor",
        24: "lower_flame_sensor",
        33: "wifi_connection",
        34: "internet_connection",
        40: "cleaning_overdue",
        41: "maintenance_overdue",
        42: "maintenance_reset",
        50: "backup_battery",
        1000: "controller_restart",
    }
)


def describe_error(code: int) -> str:
    """Translation key for a reported code, without guessing multi-cause diagnoses."""
    return ERROR_KEYS.get(code, "unknown_code")
