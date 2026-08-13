"""Config flow for VOO Technicolor DOCSIS integration."""
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, InvalidAuth, VooTechnicolorApi
from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
)


class VooDocsisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VOO Technicolor DOCSIS Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial user setup step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]

            # Unique ID based on host
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = VooTechnicolorApi(host=host, username=username, password=password, session=session)
            try:
                await api.async_authenticate()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"VOO Modem ({host})",
                    data=user_input,
                )
            finally:
                await api.close()

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): cv.string,
                vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return VooDocsisOptionsFlowHandler(config_entry)


class VooDocsisOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for VOO Technicolor integration."""

    def __init__(self, config_entry: Optional[config_entries.ConfigEntry] = None) -> None:
        """Initialize options flow compatible with all HA versions."""
        if config_entry is not None:
            self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        config_entry = getattr(self, "config_entry", None)
        if config_entry:
            scan_interval = config_entry.options.get(
                CONF_SCAN_INTERVAL,
                config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            )
        else:
            scan_interval = DEFAULT_SCAN_INTERVAL

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=scan_interval): cv.positive_int,
                }
            ),
        )
