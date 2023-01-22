"""Binary sensors for linkytic integration."""
from __future__ import annotations

import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
    FRANCE_TZ,
    HOUR_OF_CHANGE,
    OFF_PEAK_START,
)


# config flow setup
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Modern (thru config entry) sensors setup."""
    # Init sensors
    sensors = [
        OffPeakHours(config_entry.entry_id),
    ]
    # Add the entities to HA
    async_add_entities(sensors, True)


class OffPeakHours(BinarySensorEntity):
    """Serial connectivity to the Linky TIC serial interface."""

    # Generic properties
    #   https://developers.home-assistant.io/docs/core/entity#generic-properties
    _attr_has_entity_name = True
    _attr_name = "Heures Creuses"
    _attr_should_poll = True
    _attr_icon = "mdi:cash-clock"

    # Binary sensor properties
    #   https://developers.home-assistant.io/docs/core/entity/binary-sensor/#properties
    # _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, config_id: str) -> None:
        """Initialize the OffPeakHours binary sensor."""
        # Generic entity properties
        self._attr_unique_id = f"{DOMAIN}_{config_id}_off_peak"
        # Sensor entity properties
        self._attr_native_value: datetime.datetime | None = None
        # RTE Tempo Calendar entity properties
        self._config_id = config_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    @callback
    def update(self) -> None:
        """Update/Recompute the value of the sensor."""
        localized_now = datetime.datetime.now(tz=FRANCE_TZ)
        if localized_now.hour >= OFF_PEAK_START or localized_now.hour < HOUR_OF_CHANGE:
            self._attr_is_on = True
        else:
            self._attr_is_on = False
