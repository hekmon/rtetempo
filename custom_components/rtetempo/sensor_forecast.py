from __future__ import annotations

import logging
from typing import Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .forecast_coordinator import ForecastCoordinator
from .forecast import ForecastDay
from .const import (
    DOMAIN,
    DEVICE_NAME,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
)

_LOGGER = logging.getLogger(__name__)


class OpenDPEForecastSensor(CoordinatorEntity, SensorEntity):
    """Forecast sensor for a given day (J+1, J+2, …)."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:calendar"

    def __init__(self, coordinator: ForecastCoordinator, index: int):
        """
        index = 0 → J+1
        index = 1 → J+2
        etc.
        """
        super().__init__(coordinator)

        self.index = index

        self._attr_name = f"OpenDPE J{index + 1}"
        self._attr_unique_id = f"{DOMAIN}_forecast_opendpe_j{index + 1}"

        # Valeurs possibles
        self._attr_options = ["bleu", "blanc", "rouge", "inconnu"]

        self._attr_native_value: Optional[str] = None
        self._attr_extra_state_attributes = {}

    @property
    def device_info(self) -> DeviceInfo:
        """Home Assistant device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, "forecast")},
            name="RTE Tempo Forecast",
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    @property
    def available(self) -> bool:
        """The sensor is available if we have enough data."""
        data = self.coordinator.data
        return data is not None and len(data) > self.index

    def _handle_coordinator_update(self) -> None:
        """Synchronize the sensor state with the coordinator data."""
        data = self.coordinator.data

        if not data or len(data) <= self.index:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            self.async_write_ha_state()
            return

        forecast: ForecastDay = data[self.index]

        # Couleur principale
        color = forecast.color.lower()
        if color not in ["bleu", "blanc", "rouge"]:
            color = "inconnu"

        self._attr_native_value = color

        # Attributs supplémentaires
        self._attr_extra_state_attributes = {
            "date": forecast.date.isoformat(),
            "probabilité": forecast.probability,
            ATTR_ATTRIBUTION: "Données Tempo : Open DPE (https://open-dpe.fr)",
        }

        self.async_write_ha_state()
