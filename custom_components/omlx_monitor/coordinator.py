from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OmlxApiError, OmlxClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

LOGGER = logging.getLogger(__name__)


class OmlxCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, client: OmlxClient) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        try:
            return await self.client.stats()
        except OmlxApiError as err:
            raise UpdateFailed(str(err)) from err
