from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientSession
from yarl import URL


class OmlxApiError(Exception):
    """Raised when oMLX cannot be queried."""


@dataclass
class OmlxClient:
    session: ClientSession
    url: str
    api_key: str

    def __post_init__(self) -> None:
        self._base = URL(self.url.rstrip("/"))
        self._logged_in = False

    async def _login(self) -> None:
        async with self.session.post(
            self._base / "admin" / "api" / "login",
            json={"api_key": self.api_key, "remember": True},
        ) as resp:
            if resp.status != 200:
                raise OmlxApiError(f"login failed: HTTP {resp.status}")
            self._logged_in = True

    async def stats(self) -> dict[str, Any]:
        if not self._logged_in:
            await self._login()

        async with self.session.get(self._base / "admin" / "api" / "stats") as resp:
            if resp.status == 401:
                self._logged_in = False
                await self._login()
                return await self.stats()
            if resp.status != 200:
                raise OmlxApiError(f"stats failed: HTTP {resp.status}")
            return await resp.json()

    async def validate(self) -> None:
        await self.stats()
