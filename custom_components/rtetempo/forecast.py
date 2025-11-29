from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from typing import List, Optional

import aiohttp

OPEN_DPE_URL = "https://open-dpe.fr/assets/tempo_days_lite.json"

_LOGGER = logging.getLogger(__name__)


#   Forecast model
@dataclass
class ForecastDay:
    """Tempo forecast for a given day."""

    date: datetime.date
    color: str                     # "bleu", "blanc", "rouge" (normalized to lowercase)
    probability: Optional[float]   # 0.67 for example (for 67%)
    source: str = "open_dpe"


#   Main function (Open-DPE)
async def async_fetch_opendpe_forecast(
    session: aiohttp.ClientSession,
) -> List[ForecastDay]:
    """Fetch Tempo forecasts from the Open DPE JSON."""

    try:
        async with session.get(OPEN_DPE_URL, timeout=10) as response:
            if response.status != 200:
                _LOGGER.error("Open-DPE: HTTP %s", response.status)
                return []

            data = await response.json()

    except Exception as exc:
        _LOGGER.error("Open DPE: erreur lors de la récupération JSON : %s", exc)
        return []

    forecasts: List[ForecastDay] = []

    for entry in data:
        try:
            forecast_date = datetime.datetime.strptime(
                entry["date"], "%Y-%m-%d"
            ).date()
            color = entry.get("couleur", "").lower()
            prob = entry.get("probability", None)

            forecasts.append(
                ForecastDay(
                    date=forecast_date,
                    color=color,
                    probability=prob,
                    source="open_dpe",
                )
            )

        except Exception as exc:
            _LOGGER.warning("Open DPE: ligne ignorée (%s) : %s", exc, entry)
            continue

    return forecasts