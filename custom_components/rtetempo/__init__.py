"""The RTE Tempo Calendar integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant

from .api_worker import APIWorker
from .const import CONFIG_CLIEND_SECRET, CONFIG_CLIENT_ID, DOMAIN, OPTION_ADJUSTED_DAYS

PLATFORMS: list[Platform] = [Platform.CALENDAR, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up rtetempo from a config entry."""
    # Create the serial reader thread and start it
    api_worker = APIWorker(
        client_id=str(entry.data.get(CONFIG_CLIENT_ID)),
        client_secret=str(entry.data.get(CONFIG_CLIEND_SECRET)),
        adjusted_days=bool(entry.options.get(OPTION_ADJUSTED_DAYS)),
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
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    # main init done
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove the related entry
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    # Retrieved the API Worker for this config entry
    try:
        serial_reader = hass.data[DOMAIN][entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "Can not update options for %s: failed to get the API Worker object",
            entry.title,
        )
        return
    # Update its options
    serial_reader.update_options(entry.options.get(OPTION_ADJUSTED_DAYS))
