"""Config flow for RTE Tempo Calendar."""
from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from requests.exceptions import RequestException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .api_worker import BadRequest, ServerError, UnexpectedError, application_tester
from .const import (
    CONFIG_CLIEND_SECRET,
    CONFIG_CLIENT_ID,
    DOMAIN,
    OPTION_ADJUSTED_DAYS,
    RTE_APPS_URL,
)

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONFIG_CLIENT_ID): str,
        vol.Required(CONFIG_CLIEND_SECRET): str,
    }
)


async def async_validate_credentials(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> dict[str, str] | None:
    """Validate application credentials against the RTE API.

    Return None on success, or the errors dict (errors["base"] = <key>) for
    the calling step on failure.
    """
    try:
        client_id = user_input[CONFIG_CLIENT_ID]
        client_secret = user_input[CONFIG_CLIEND_SECRET]
        await hass.async_add_executor_job(
            lambda: application_tester(str(client_id), str(client_secret))
        )
    except RequestException as request_exception:
        _LOGGER.error(
            "Application validation failed: network error: %s", request_exception
        )
        return {"base": "network_error"}
    except OAuth2Error as oauth_error:
        _LOGGER.error("Application validation failed: oauth error: %s", oauth_error)
        return {"base": "oauth_error"}
    except BadRequest as http_error:
        _LOGGER.error(
            "Application validation failed: bad request error: %s", http_error
        )
        return {"base": "http_client_error"}
    except ServerError as http_error:
        _LOGGER.error("Application validation failed: server error: %s", http_error)
        return {"base": "http_server_error"}
    except UnexpectedError as http_error:
        _LOGGER.error(
            "Application validation failed: unexpected error: %s", http_error
        )
        return {"base": "http_unexpected_error"}
    return None


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RTE Tempo Calendar."""

    VERSION = 1

    _entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # No input
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders={"rte_apps_url": RTE_APPS_URL},
            )
        # Validate input
        await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONFIG_CLIENT_ID]}")
        self._abort_if_unique_id_configured()
        errors = await async_validate_credentials(self.hass, user_input)
        if errors is not None:
            # Show errors
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
                description_placeholders={"rte_apps_url": RTE_APPS_URL},
            )
        return self.async_create_entry(
            title=user_input[CONFIG_CLIENT_ID], data=user_input
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Handle reauthentication when the credentials have been rejected."""
        # entry_data is unused but required by HA's reauth calling convention
        # (same pattern as the nanoleaf core integration)
        self._entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        if self._entry is None:
            # The config entry requesting the reauth is gone: nothing to update
            return self.async_abort(reason="unknown_entry")
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the reauth confirmation step."""
        # No input
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders={"rte_apps_url": RTE_APPS_URL},
            )
        # Validate input
        errors = await async_validate_credentials(self.hass, user_input)
        if errors is not None:
            # Show errors
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
                description_placeholders={"rte_apps_url": RTE_APPS_URL},
            )
        # Compute the new unique id
        new_unique_id = f"{DOMAIN}_{user_input[CONFIG_CLIENT_ID]}"
        # Make sure no other config entry already owns this new unique id
        if self._async_unique_id_taken(self._entry, new_unique_id):
            return self.async_abort(reason="already_configured")
        # Update the entry: the update listener schedules the reload (this
        # flow must not reload itself while an update listener is registered)
        self.hass.config_entries.async_update_entry(
            self._entry,
            title=user_input[CONFIG_CLIENT_ID],
            data=dict(user_input),
            unique_id=new_unique_id,
        )
        return self.async_abort(reason="reauth_successful")

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the reconfiguration step."""
        entry = self._get_reconfigure_entry()
        # No input
        if user_input is None:
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=self.add_suggested_values_to_schema(
                    STEP_USER_DATA_SCHEMA, entry.data
                ),
                description_placeholders={"rte_apps_url": RTE_APPS_URL},
            )
        # Validate input
        errors = await async_validate_credentials(self.hass, user_input)
        if errors is not None:
            # Show errors
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=self.add_suggested_values_to_schema(
                    STEP_USER_DATA_SCHEMA, user_input
                ),
                errors=errors,
                description_placeholders={"rte_apps_url": RTE_APPS_URL},
            )
        # Compute the new unique id
        new_unique_id = f"{DOMAIN}_{user_input[CONFIG_CLIENT_ID]}"
        # Make sure no other config entry already owns this new unique id
        if self._async_unique_id_taken(entry, new_unique_id):
            return self.async_abort(reason="already_configured")
        # Update the entry: the update listener schedules the reload (this
        # flow must not reload itself while an update listener is registered)
        self.hass.config_entries.async_update_entry(
            entry,
            title=user_input[CONFIG_CLIENT_ID],
            data=dict(user_input),
            unique_id=new_unique_id,
        )
        return self.async_abort(reason="reconfigure_successful")

    def _async_unique_id_taken(
        self, entry: config_entries.ConfigEntry, new_unique_id: str
    ) -> bool:
        """Return True iff another config entry already owns the new unique id.

        An entry keeping its own unique id never collides with itself.
        """
        return new_unique_id != entry.unique_id and any(
            other.unique_id == new_unique_id
            for other in self.hass.config_entries.async_entries(DOMAIN)
            if other.entry_id != entry.entry_id
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles the options of a Linky TIC connection."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPTION_ADJUSTED_DAYS,
                        default=self.config_entry.options.get(OPTION_ADJUSTED_DAYS),
                    ): bool
                }
            ),
        )
