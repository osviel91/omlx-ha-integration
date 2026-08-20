from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OmlxApiError, OmlxClient
from .const import CONF_URL, DOMAIN


class OmlxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            client = OmlxClient(
                async_get_clientsession(self.hass),
                url,
                user_input[CONF_API_KEY],
            )
            try:
                await client.validate()
            except OmlxApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"oMLX ({url})",
                    data={CONF_URL: url, CONF_API_KEY: user_input[CONF_API_KEY]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default="http://127.0.0.1:8000"): str,
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )
