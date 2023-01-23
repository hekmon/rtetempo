"""Sensors for RTE Tempo Calendar integration."""
from __future__ import annotations

import asyncio
import datetime
import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api_worker import APIWorker
from .const import (
    API_ATTRIBUTION,
    API_REQ_TIMEOUT,
    API_VALUE_BLUE,
    API_VALUE_RED,
    API_VALUE_WHITE,
    CYCLE_START_DAY,
    CYCLE_START_MONTH,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
    FRANCE_TZ,
    HOUR_OF_CHANGE,
    OFF_PEAK_START,
    SENSOR_COLOR_BLUE_EMOJI,
    SENSOR_COLOR_BLUE_NAME,
    SENSOR_COLOR_RED_EMOJI,
    SENSOR_COLOR_RED_NAME,
    SENSOR_COLOR_UNKNOWN_EMOJI,
    SENSOR_COLOR_UNKNOWN_NAME,
    SENSOR_COLOR_WHITE_EMOJI,
    SENSOR_COLOR_WHITE_NAME,
    TOTAL_RED_DAYS,
    TOTAL_WHITE_DAYS,
)

_LOGGER = logging.getLogger(__name__)


# config flow setup
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Modern (thru config entry) sensors setup."""
    _LOGGER.debug("%s: setting up sensor plateform", config_entry.title)
    # Retrieve the API Worker object
    try:
        api_worker = hass.data[DOMAIN][config_entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "%s: can not calendar: failed to get the API worker object",
            config_entry.title,
        )
        return
    # Wait request timeout to let API worker get first batch of data before initializing sensors
    await asyncio.sleep(API_REQ_TIMEOUT)
    # Init sensors
    sensors = [
        CurrentColor(config_entry.entry_id, api_worker, False),
        CurrentColor(config_entry.entry_id, api_worker, True),
        NextColor(config_entry.entry_id, api_worker, False),
        NextColor(config_entry.entry_id, api_worker, True),
        NextColorTime(config_entry.entry_id),
        DaysLeft(config_entry.entry_id, api_worker, API_VALUE_BLUE),
        DaysLeft(config_entry.entry_id, api_worker, API_VALUE_WHITE),
        DaysLeft(config_entry.entry_id, api_worker, API_VALUE_RED),
        DaysUsed(config_entry.entry_id, api_worker, API_VALUE_BLUE),
        DaysUsed(config_entry.entry_id, api_worker, API_VALUE_WHITE),
        DaysUsed(config_entry.entry_id, api_worker, API_VALUE_RED),
        NextCycleTime(config_entry.entry_id),
        OffPeakChangeTime(config_entry.entry_id),
    ]
    # Add the entities to HA
    async_add_entities(sensors, True)


class CurrentColor(SensorEntity):
    """Current Color Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    _attr_attribution = API_ATTRIBUTION
    # Sensor properties
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:palette"

    def __init__(self, config_id: str, api_worker: APIWorker, visual: bool) -> None:
        """Initialize the Current Color Sensor."""
        # Generic entity properties
        if visual:
            self._attr_name = "Couleur actuelle (visuel)"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_current_color_emoji"
            self._attr_options = [
                SENSOR_COLOR_BLUE_EMOJI,
                SENSOR_COLOR_WHITE_EMOJI,
                SENSOR_COLOR_RED_EMOJI,
                SENSOR_COLOR_UNKNOWN_EMOJI,
            ]
        else:
            self._attr_name = "Couleur actuelle"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_current_color"
            self._attr_options = [
                SENSOR_COLOR_BLUE_NAME,
                SENSOR_COLOR_WHITE_NAME,
                SENSOR_COLOR_RED_NAME,
                SENSOR_COLOR_UNKNOWN_NAME,
            ]
        # Sensor entity properties
        self._attr_native_value: str | None = None
        # RTE Tempo Calendar entity properties
        self._config_id = config_id
        self._api_worker = api_worker
        self._visual = visual

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
        """Update the value of the sensor from the thread object memory cache."""
        localized_now = datetime.datetime.now(FRANCE_TZ)
        for tempo_day in self._api_worker.get_adjusted_days():
            if tempo_day.Start <= localized_now < tempo_day.End:
                # Found a match !
                self._attr_available = True
                if self._visual:
                    self._attr_native_value = get_color_emoji(tempo_day.Value)
                    self._attr_icon = get_color_icon(tempo_day.Value)
                else:
                    self._attr_native_value = get_color_name(tempo_day.Value)
                return
        # Nothing found
        self._attr_available = False
        self._attr_native_value = None
        if self._visual:
            self._attr_icon = "mdi:palette"


class NextColor(SensorEntity):
    """Next Color Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    _attr_attribution = API_ATTRIBUTION
    # Sensor properties
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:palette"

    def __init__(self, config_id: str, api_worker: APIWorker, visual: bool) -> None:
        """Initialize the Next Color Sensor."""
        # Generic entity properties
        if visual:
            self._attr_name = "Prochaine couleur (visuel)"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_next_color_emoji"
            self._attr_options = [
                SENSOR_COLOR_BLUE_EMOJI,
                SENSOR_COLOR_WHITE_EMOJI,
                SENSOR_COLOR_RED_EMOJI,
                SENSOR_COLOR_UNKNOWN_EMOJI,
            ]
        else:
            self._attr_name = "Prochaine couleur"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_next_color"
            self._attr_options = [
                SENSOR_COLOR_BLUE_NAME,
                SENSOR_COLOR_WHITE_NAME,
                SENSOR_COLOR_RED_NAME,
                SENSOR_COLOR_UNKNOWN_NAME,
            ]
        # Sensor entity properties
        self._attr_native_value: str | None = None
        # RTE Tempo Calendar entity properties
        self._config_id = config_id
        self._api_worker = api_worker
        self._visual = visual

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
        """Update the value of the sensor from the thread object memory cache."""
        localized_now = datetime.datetime.now(FRANCE_TZ)
        for tempo_day in self._api_worker.get_adjusted_days():
            if localized_now < tempo_day.Start:
                # Found a match !
                self._attr_available = True
                if self._visual:
                    self._attr_native_value = get_color_emoji(tempo_day.Value)
                    self._attr_icon = get_color_icon(tempo_day.Value)
                else:
                    self._attr_native_value = get_color_name(tempo_day.Value)
                return
        # Special case for emoji
        if self._visual:
            self._attr_available = True
            self._attr_native_value = SENSOR_COLOR_UNKNOWN_EMOJI
            self._attr_icon = "mdi:palette"
        else:
            self._attr_available = False
            self._attr_native_value = None


def get_color_emoji(value: str) -> str:
    """Return the corresponding emoji for a day color."""
    if value == API_VALUE_RED:
        return SENSOR_COLOR_RED_EMOJI
    if value == API_VALUE_WHITE:
        return SENSOR_COLOR_WHITE_EMOJI
    if value == API_VALUE_BLUE:
        return SENSOR_COLOR_BLUE_EMOJI
    _LOGGER.warning("Can not get color emoji for unknown value: %s", value)
    return SENSOR_COLOR_UNKNOWN_EMOJI


def get_color_icon(value: str) -> str:
    """Return the corresponding emoji for a day color."""
    if value == API_VALUE_RED:
        return "mdi:alert"
    if value == API_VALUE_WHITE:
        return "mdi:information-outline"
    if value == API_VALUE_BLUE:
        return "mdi:check-bold"
    _LOGGER.warning("Can not get color icon for unknown value: %s", value)
    return "mdi:palette"


def get_color_name(value: str) -> str:
    """Return the corresponding emoji for a day color."""
    if value == API_VALUE_RED:
        return SENSOR_COLOR_RED_NAME
    if value == API_VALUE_WHITE:
        return SENSOR_COLOR_WHITE_NAME
    if value == API_VALUE_BLUE:
        return SENSOR_COLOR_BLUE_NAME
    _LOGGER.warning("Can not get color name for unknown value: %s", value)
    return SENSOR_COLOR_UNKNOWN_NAME


class NextColorTime(SensorEntity):
    """Next Color Time Remaining Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    _attr_name = "Prochaine couleur (changement)"
    # Sensor properties
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, config_id: str) -> None:
        """Initialize the Next Color Time Remaining Sensor."""
        # Generic entity properties
        self._attr_unique_id = f"{DOMAIN}_{config_id}_next_color_change"
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
        """Update the value of the sensor from the thread object memory cache."""
        localized_now = datetime.datetime.now(FRANCE_TZ)
        if localized_now.hour >= HOUR_OF_CHANGE:
            tomorrow = localized_now + datetime.timedelta(days=1)
            self._attr_native_value = datetime.datetime(
                year=tomorrow.year,
                month=tomorrow.month,
                day=tomorrow.day,
                hour=HOUR_OF_CHANGE,
                tzinfo=FRANCE_TZ,
            )
        else:
            self._attr_native_value = datetime.datetime(
                year=localized_now.year,
                month=localized_now.month,
                day=localized_now.day,
                hour=HOUR_OF_CHANGE,
                tzinfo=FRANCE_TZ,
            )


class DaysLeft(SensorEntity):
    """Days Left Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    _attr_attribution = API_ATTRIBUTION
    # Sensor properties
    _attr_native_unit_of_measurement = "j"
    _attr_icon = "mdi:timer-sand"

    def __init__(self, config_id: str, api_worker: APIWorker, color: str) -> None:
        """Initialize the Days Left Sensor."""
        # Generic entity properties
        if color == API_VALUE_BLUE:
            self._attr_name = f"Cycle Jours restants {SENSOR_COLOR_BLUE_NAME}"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_days_left_blue"
        elif color == API_VALUE_WHITE:
            self._attr_name = f"Cycle Jours restants {SENSOR_COLOR_WHITE_NAME}"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_days_left_white"
        elif color == API_VALUE_RED:
            self._attr_name = f"Cycle Jours restants {SENSOR_COLOR_RED_NAME}"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_days_left_red"
        else:
            raise Exception(f"invalid color {color}")
        # Sensor entity properties
        self._attr_native_value: int | None = None
        # RTE Tempo Calendar entity properties
        self._config_id = config_id
        self._api_worker = api_worker
        self._color = color

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
        """Update the value of the sensor from the thread object memory cache."""
        # First compute the number of days this cycle has (handles leap year)
        localized_now = datetime.datetime.now(tz=FRANCE_TZ)
        if localized_now.month < CYCLE_START_MONTH:
            cycle_start = datetime.date(
                year=localized_now.year - 1,
                month=CYCLE_START_MONTH,
                day=CYCLE_START_DAY,
            )
            cycle_end = datetime.date(
                year=localized_now.year, month=CYCLE_START_MONTH, day=CYCLE_START_DAY
            )
        else:
            cycle_start = datetime.date(
                year=localized_now.year, month=CYCLE_START_MONTH, day=CYCLE_START_DAY
            )
            cycle_end = datetime.date(
                year=localized_now.year + 1,
                month=CYCLE_START_MONTH,
                day=CYCLE_START_DAY,
            )
        total_days = (cycle_end - cycle_start).days
        # Now compute how many blue days there is in this cycle
        total_blue_days = total_days - TOTAL_WHITE_DAYS - TOTAL_RED_DAYS
        # Count already defined days since the beginning of the cycle
        nb_blue_days = 0
        nb_white_days = 0
        nb_red_days = 0
        for tempo_day in self._api_worker.get_regular_days():
            if tempo_day.Start < cycle_start:
                break
            if tempo_day.Value == API_VALUE_BLUE:
                nb_blue_days += 1
            elif tempo_day.Value == API_VALUE_WHITE:
                nb_white_days += 1
            elif tempo_day.Value == API_VALUE_RED:
                nb_red_days += 1
            else:
                raise Exception(f"invalid color {tempo_day.Value}")
        # Now compute remaining days
        if self._color == API_VALUE_BLUE:
            self._attr_native_value = total_blue_days - nb_blue_days
        elif self._color == API_VALUE_WHITE:
            self._attr_native_value = TOTAL_WHITE_DAYS - nb_white_days
        elif self._color == API_VALUE_RED:
            self._attr_native_value = TOTAL_RED_DAYS - nb_red_days
        else:
            raise Exception(f"invalid color {self._color}")


class DaysUsed(SensorEntity):
    """Days Used Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    _attr_attribution = API_ATTRIBUTION
    # Sensor properties
    _attr_native_unit_of_measurement = "j"
    _attr_icon = "mdi:timer-sand-complete"

    def __init__(self, config_id: str, api_worker: APIWorker, color: str) -> None:
        """Initialize the Days Used Sensor."""
        # Generic entity properties
        if color == API_VALUE_BLUE:
            self._attr_name = f"Cycle Jours déjà placés {SENSOR_COLOR_BLUE_NAME}"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_days_used_blue"
        elif color == API_VALUE_WHITE:
            self._attr_name = f"Cycle Jours déjà placés {SENSOR_COLOR_WHITE_NAME}"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_days_used_white"
        elif color == API_VALUE_RED:
            self._attr_name = f"Cycle Jours déjà placés {SENSOR_COLOR_RED_NAME}"
            self._attr_unique_id = f"{DOMAIN}_{config_id}_days_used_red"
        else:
            raise Exception(f"invalid color {color}")
        # Sensor entity properties
        self._attr_native_value: int | None = None
        # RTE Tempo Calendar entity properties
        self._config_id = config_id
        self._api_worker = api_worker
        self._color = color

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
        """Update the value of the sensor from the thread object memory cache."""
        # First compute the number of days this cycle has (handles leap year)
        localized_now = datetime.datetime.now(tz=FRANCE_TZ)
        if localized_now.month < CYCLE_START_MONTH:
            cycle_start = datetime.date(
                year=localized_now.year - 1,
                month=CYCLE_START_MONTH,
                day=CYCLE_START_DAY,
            )
        else:
            cycle_start = datetime.date(
                year=localized_now.year, month=CYCLE_START_MONTH, day=CYCLE_START_DAY
            )
        # Count already defined days since the beginning of the cycle
        nb_blue_days = 0
        nb_white_days = 0
        nb_red_days = 0
        for tempo_day in self._api_worker.get_regular_days():
            if tempo_day.Start < cycle_start:
                break
            if tempo_day.Value == API_VALUE_BLUE:
                nb_blue_days += 1
            elif tempo_day.Value == API_VALUE_WHITE:
                nb_white_days += 1
            elif tempo_day.Value == API_VALUE_RED:
                nb_red_days += 1
            else:
                raise Exception(f"invalid color {tempo_day.Value}")
        # Now compute remaining days
        if self._color == API_VALUE_BLUE:
            self._attr_native_value = nb_blue_days
        elif self._color == API_VALUE_WHITE:
            self._attr_native_value = nb_white_days
        elif self._color == API_VALUE_RED:
            self._attr_native_value = nb_red_days
        else:
            raise Exception(f"invalid color {self._color}")


class NextCycleTime(SensorEntity):
    """Next Cycle Time Remaining Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    _attr_name = "Cycle Prochaine réinitialisation"
    # Sensor properties
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, config_id: str) -> None:
        """Initialize the Cycle Time Remaining Sensor."""
        # Generic entity properties
        self._attr_unique_id = f"{DOMAIN}_{config_id}_next_cycle_reinit"
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
        """Update the value of the sensor from the thread object memory cache."""
        localized_now = datetime.datetime.now(tz=FRANCE_TZ)
        if (
            localized_now.month >= CYCLE_START_MONTH
            and localized_now.day >= CYCLE_START_DAY
        ):
            self._attr_native_value = datetime.datetime(
                year=localized_now.year + 1,
                month=CYCLE_START_MONTH,
                day=CYCLE_START_DAY,
                hour=HOUR_OF_CHANGE,
                tzinfo=localized_now.tzinfo,
            )
        else:
            self._attr_native_value = datetime.datetime(
                year=localized_now.year,
                month=CYCLE_START_MONTH,
                day=CYCLE_START_DAY,
                hour=HOUR_OF_CHANGE,
                tzinfo=FRANCE_TZ,
            )


class OffPeakChangeTime(SensorEntity):
    """Off Peak Change Time Remaining Sensor Entity."""

    # Generic properties
    _attr_has_entity_name = True
    _attr_name = "Heures Creuses (changement)"
    # Sensor properties
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, config_id: str) -> None:
        """Initialize the Off Peak Change Time Remaining Sensor."""
        # Generic entity properties
        self._attr_unique_id = f"{DOMAIN}_{config_id}_off_peak_change_time"
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
        if localized_now.hour < HOUR_OF_CHANGE:
            self._attr_native_value = datetime.datetime(
                year=localized_now.year,
                month=localized_now.month,
                day=localized_now.day,
                hour=HOUR_OF_CHANGE,
                tzinfo=localized_now.tzinfo,
            )
        elif localized_now.hour < OFF_PEAK_START:
            self._attr_native_value = datetime.datetime(
                year=localized_now.year,
                month=localized_now.month,
                day=localized_now.day,
                hour=OFF_PEAK_START,
                tzinfo=localized_now.tzinfo,
            )
        else:
            tomorrow = localized_now + datetime.timedelta(days=1)
            self._attr_native_value = datetime.datetime(
                year=tomorrow.year,
                month=tomorrow.month,
                day=tomorrow.day,
                hour=HOUR_OF_CHANGE,
                tzinfo=tomorrow.tzinfo,
            )
