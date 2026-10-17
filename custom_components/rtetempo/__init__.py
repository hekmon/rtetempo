"""The RTE Tempo Calendar integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant

from .api_worker import APIWorker
from .const import CONFIG_CLIEND_SECRET, CONFIG_CLIENT_ID, DOMAIN, OPTION_ADJUSTED_DAYS

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.CALENDAR, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up rtetempo from a config entry."""
    # Build a thread safe trigger to request a reauth flow: the API worker runs
    # in its own thread so the call must be scheduled on the event loop with
    # hass.add_job (documented thread safe)

    def reauth_trigger() -> None:
        """Request a Home Assistant reauth flow (thread safe)."""

        async def async_start_reauth() -> None:
            """Start the reauth flow from the event loop."""
            # ConfigEntry.async_start_reauth is a sync callback but must run in
            # the event loop, hence this coroutine scheduled via hass.add_job
            entry.async_start_reauth(hass)

        hass.add_job(async_start_reauth)

    # Create the serial reader thread and start it
    api_worker = APIWorker(
        client_id=str(entry.data.get(CONFIG_CLIENT_ID)),
        client_secret=str(entry.data.get(CONFIG_CLIEND_SECRET)),
        adjusted_days=bool(entry.options.get(OPTION_ADJUSTED_DAYS)),
        reauth_trigger=reauth_trigger,
    )
    api_worker.start()
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, api_worker.signalstop)
    # Add options callback
    entry.async_on_unload(entry.add_update_listener(update_listener))
    entry.async_on_unload(lambda: api_worker.signalstop("config_entry_unload"))
    # Add the serial reader to HA and initialize sensors
    try:
        hass.data[DOMAIN][entry.entry_id] = api_worker
    except KeyError:
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN][entry.entry_id] = api_worker
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # main init done
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove the related entry
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle config entry updates: schedule reload on credentials change.

    As an integration with an update listener, this listener owns reload
    scheduling (see HA's async_update_reload_and_abort usage report).
    """
    # Retrieved the API Worker for this config entry
    try:
        serial_reader = hass.data[DOMAIN][entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "Can not update options for %s: failed to get the API Worker object",
            entry.title,
        )
        return
    # Credentials changed: the running worker was built with the old ones so
    # the entry must be reloaded to rebuild it with the new credentials
    if (
        str(entry.data.get(CONFIG_CLIENT_ID)) != serial_reader.client_id
        or str(entry.data.get(CONFIG_CLIEND_SECRET)) != serial_reader.client_secret
    ):
        hass.config_entries.async_schedule_reload(entry.entry_id)
        return
    # Update its options
    serial_reader.update_options(entry.options.get(OPTION_ADJUSTED_DAYS))
