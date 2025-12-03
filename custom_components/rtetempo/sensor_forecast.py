from __future__ import annotations

from typing import Optional
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    SENSOR_COLOR_BLUE_EMOJI,
    SENSOR_COLOR_WHITE_EMOJI,
    SENSOR_COLOR_RED_EMOJI,
    SENSOR_COLOR_UNKNOWN_EMOJI,
    SENSOR_COLOR_BLUE_NAME,
    SENSOR_COLOR_WHITE_NAME,
    SENSOR_COLOR_RED_NAME,
    SENSOR_COLOR_UNKNOWN_NAME,
)

from .forecast_coordinator import ForecastCoordinator
from .forecast import ForecastDay


# -------- Helper functions (copied from sensor.py of RTE Tempo) ----------------

def get_color_emoji(value: str) -> str:
    if value == "rouge":
        return SENSOR_COLOR_RED_EMOJI
    if value == "blanc":
        return SENSOR_COLOR_WHITE_EMOJI
    if value == "bleu":
        return SENSOR_COLOR_BLUE_EMOJI
    return SENSOR_COLOR_UNKNOWN_EMOJI


def get_color_name(value: str) -> str:
    if value == "rouge":
        return SENSOR_COLOR_RED_NAME
    if value == "blanc":
        return SENSOR_COLOR_WHITE_NAME
    if value == "bleu":
        return SENSOR_COLOR_BLUE_NAME
    return SENSOR_COLOR_UNKNOWN_NAME


def get_color_icon(value: str) -> str:
    if value == "rouge":
        return "mdi:alert"
    if value == "blanc":
        return "mdi:information-outline"
    if value == "bleu":
        return "mdi:check-bold"
    return "mdi:palette"


# ---------------- Forecast Sensor ----------------------


class OpenDPEForecastSensor(CoordinatorEntity, SensorEntity):
    """OpenDPE forecast sensor (text or visual version)."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_has_entity_name = True

    def __init__(self, coordinator: ForecastCoordinator, index: int, visual: bool):
        super().__init__(coordinator)

        self.index = index
        self.visual = visual

        # ----- Sensor naming and options -----
        if visual:
            self._attr_name = f"OpenDPE J{index + 1} (visuel)"
            self._attr_unique_id = f"{DOMAIN}_forecast_opendpe_j{index + 1}_emoji"
            self._attr_options = [
                SENSOR_COLOR_BLUE_EMOJI,
                SENSOR_COLOR_WHITE_EMOJI,
                SENSOR_COLOR_RED_EMOJI,
                SENSOR_COLOR_UNKNOWN_EMOJI,
            ]
            self._attr_icon = "mdi:palette"

        else:
            self._attr_name = f"OpenDPE J{index + 1}"
            self._attr_unique_id = f"{DOMAIN}_forecast_opendpe_j{index + 1}"
            self._attr_options = [
                SENSOR_COLOR_BLUE_NAME,
                SENSOR_COLOR_WHITE_NAME,
                SENSOR_COLOR_RED_NAME,
                SENSOR_COLOR_UNKNOWN_NAME,
            ]
            self._attr_icon = "mdi:calendar"

        self._attr_native_value: Optional[str] = None
        self._attr_extra_state_attributes = {}

    # ---------------- Device Info ----------------------

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info shared by all forecast sensors."""
        return DeviceInfo(
            identifiers={(DOMAIN, "forecast")},
            name="RTE Tempo Forecast",
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    # ---------------- Availability ----------------------

    @property
    def available(self) -> bool:
        data = self.coordinator.data
        return data is not None and len(data) > self.index

    # ---------------- Coordinator update handler ----------------------

    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data

        if not data or len(data) <= self.index:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            self.async_write_ha_state()
            return

        forecast: ForecastDay = data[self.index]
        color = forecast.color.lower()

        if color not in ["bleu", "blanc", "rouge"]:
            color = "inconnu"

        # ----- VISUAL VERSION -----
        if self.visual:
            self._attr_native_value = get_color_emoji(color)
            self._attr_icon = get_color_icon(color)

        # ----- TEXT VERSION -----
        else:
            self._attr_native_value = get_color_name(color)

        # Extra attributes for both sensors
        self._attr_extra_state_attributes = {
            "date": forecast.date.isoformat(),
            "probability": forecast.probability,
            "attribution": "Données Tempo : Open DPE (https://open-dpe.fr)",
        }

        self.async_write_ha_state()
