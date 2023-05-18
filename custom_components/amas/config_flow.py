"""Config flow for amastech integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_API_TOKEN,
    CONF_HOST,
    CONF_NAME
)
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import (
    DOMAIN, 
    DEFAULT_NAME, 
    AMASHub
)


class AMASFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a AMASTech config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._config: dict = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        return await self.async_step_init(user_input)

    async def async_step_init(
        self, user_input: dict[str, Any] | None, is_import: bool = False
    ) -> FlowResult:
        """Handle init step of a flow."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            api_key = user_input[CONF_ACCESS_TOKEN]
            name = user_input[CONF_NAME]
            mactoken = user_input[CONF_API_TOKEN]
            
            hub = AMASHub(host, self.hass, async_create_clientsession(self.hass))

            if await hub.authenticate(api_key, mactoken):
                self._config[CONF_NAME] = name
                self._config[CONF_HOST] = host
                self._config[CONF_ACCESS_TOKEN] = api_key
                self._config[CONF_API_TOKEN] = mactoken
                return self.async_create_entry(
                title=self._config[CONF_NAME],
                data={
                    **self._config,
                },
                )
            else:
                raise ConfigEntryAuthFailed

        user_input = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, '')): str,
                    vol.Required(
                        CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)
                    ): str,
                    vol.Required(
                        CONF_ACCESS_TOKEN,
                        default=user_input.get(CONF_ACCESS_TOKEN, ''),
                    ): str,
                    vol.Required(
                        CONF_API_TOKEN,
                        default=user_input.get(CONF_API_TOKEN, ''),
                    ): str,
                }
            ),
            errors=errors,
        )
