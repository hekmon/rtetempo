from __future__ import annotations

import logging
from datetime import timedelta
from typing import List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_change

from .forecast import ForecastDay, async_fetch_opendpe_forecast

_LOGGER = logging.getLogger(__name__)


class ForecastCoordinator(DataUpdateCoordinator[List[ForecastDay]]):
    """Coordinator in charge of fetching Open-DPE forecasts."""

    def __init__(self, hass: HomeAssistant):
        """Initializing the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Tempo Forecast Coordinator",
            update_interval=timedelta(hours=6),  # refresh every 6 hours
        )

        self.hass = hass
        self.session = async_get_clientsession(hass)

        # Daily uptade after midnight then every 6 hours (JSON is updated around 06:00)
        async_track_time_change(
            hass,
            self._scheduled_refresh,
            hour=7,
            minute=0,
            second=0,
        )

        _LOGGER.debug(
            "ForecastCoordinator initialisé : refresh quotidien programmé à 07:00 + intervalle 6h"
        )

    async def _scheduled_refresh(self, now):
        """Update at 07:00 every day."""
        _LOGGER.debug("Open DPE: lancement du refresh programmé à 07:00")
        await self.async_request_refresh()

    async def _async_update_data(self) -> List[ForecastDay]:
        """Open DPE data recovery."""
        try:
            forecasts = await async_fetch_opendpe_forecast(self.session)
            _LOGGER.debug("Open DPE: %s jours récupérés", len(forecasts))
            return forecasts

        except Exception as exc:
            _LOGGER.error("Open DPE: erreur lors de la mise à jour: %s", exc)
            raise UpdateFailed(f"Erreur mise à jour des prévisions Open DPE: {exc}")

