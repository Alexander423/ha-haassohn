"""UI connection setup, identity-preserving reconfiguration and reauthentication."""

from typing import Any
from uuid import uuid4

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .const import CONF_IDENTITY, CONF_PIN, DOMAIN
from .library import (
    AuthenticationError,
    ConnectionError,
    HaasSohnClient,
    HaasSohnError,
    InvalidValue,
    RequestTimeout,
    UnsupportedDevice,
)


class HaasSohnConfigFlow(ConfigFlow, domain=DOMAIN):
    """GET verifies reachability and protocol, never falsely claims to verify PIN."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._configure("user", user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._configure("reconfigure", user_input)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._configure("reauth_confirm", user_input)

    async def _configure(self, step: str, user_input: dict[str, Any] | None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = (
            self._get_reconfigure_entry()
            if step == "reconfigure"
            else self._get_reauth_entry()
            if step == "reauth_confirm"
            else None
        )
        if user_input is not None:
            try:
                async with HaasSohnClient(user_input[CONF_HOST], user_input[CONF_PIN]) as client:
                    info = await client.get_device_info()
            except InvalidValue:
                errors["base"] = "invalid_input"
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except RequestTimeout:
                errors["base"] = "timeout"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except UnsupportedDevice:
                errors["base"] = "unsupported_device"
            except HaasSohnError:
                errors["base"] = "unknown"
            else:
                user_input = {**user_input, CONF_HOST: user_input[CONF_HOST].lower().rstrip(".")}
                identity = info.unique_id
                if entry is not None:
                    original = entry.data.get(CONF_IDENTITY)
                    if original is not None and identity != original:
                        return self.async_abort(reason="wrong_device")
                    if identity:
                        # Also protect fallback entries from being reconfigured to another
                        # already registered physical stove.
                        for existing in self._async_current_entries():
                            if existing.entry_id != entry.entry_id and (
                                existing.data.get(CONF_IDENTITY) == identity
                            ):
                                return self.async_abort(reason="already_configured")
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            **user_input,
                            CONF_IDENTITY: identity,
                        },
                    )
                # Host is used only to prevent duplicates when no serial is available.
                # It is never used as a permanent identity.
                if identity and any(
                    existing.data.get(CONF_IDENTITY) == identity
                    for existing in self._async_current_entries()
                ):
                    return self.async_abort(reason="already_configured")
                self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
                await self.async_set_unique_id(identity or f"local-{uuid4()}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info.model, data={**user_input, CONF_IDENTITY: identity}
                )
        defaults = entry.data if entry else {}
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
                vol.Required(CONF_PIN): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )
        return self.async_show_form(step_id=step, data_schema=schema, errors=errors)
