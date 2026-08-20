from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OmlxCoordinator


def _path(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    return default if value is None else value


@dataclass(frozen=True, kw_only=True)
class OmlxSensorDescription(SensorEntityDescription):
    value: Callable[[dict[str, Any]], Any]


SENSORS: tuple[OmlxSensorDescription, ...] = (
    OmlxSensorDescription(key="total_prompt_tokens", translation_key="total_prompt_tokens", native_unit_of_measurement="tokens", state_class=SensorStateClass.TOTAL_INCREASING, value=lambda d: d.get("total_prompt_tokens")),
    OmlxSensorDescription(key="total_cached_tokens", translation_key="total_cached_tokens", native_unit_of_measurement="tokens", state_class=SensorStateClass.TOTAL_INCREASING, value=lambda d: d.get("total_cached_tokens")),
    OmlxSensorDescription(key="cache_efficiency", translation_key="cache_efficiency", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT, value=lambda d: d.get("cache_efficiency")),
    OmlxSensorDescription(key="avg_prefill_tps", translation_key="avg_prefill_tps", native_unit_of_measurement="tok/s", state_class=SensorStateClass.MEASUREMENT, value=lambda d: d.get("avg_prefill_tps")),
    OmlxSensorDescription(key="avg_generation_tps", translation_key="avg_generation_tps", native_unit_of_measurement="tok/s", state_class=SensorStateClass.MEASUREMENT, value=lambda d: d.get("avg_generation_tps")),
    OmlxSensorDescription(key="total_requests", translation_key="total_requests", state_class=SensorStateClass.TOTAL_INCREASING, value=lambda d: d.get("total_requests")),
    OmlxSensorDescription(key="active_requests", translation_key="active_requests", state_class=SensorStateClass.MEASUREMENT, value=lambda d: _path(d, "active_models", "total_active_requests", default=0)),
    OmlxSensorDescription(key="waiting_requests", translation_key="waiting_requests", state_class=SensorStateClass.MEASUREMENT, value=lambda d: _path(d, "active_models", "total_waiting_requests", default=0)),
    OmlxSensorDescription(key="loaded_models", translation_key="loaded_models", state_class=SensorStateClass.MEASUREMENT, value=lambda d: len(_path(d, "active_models", "models", default=[]))),
    OmlxSensorDescription(key="model_memory_used", translation_key="model_memory_used", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: round((_path(d, "active_models", "model_memory_used", default=0) or 0) / 1024**3, 2)),
    OmlxSensorDescription(key="model_memory_max", translation_key="model_memory_max", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: round((_path(d, "active_models", "model_memory_max", default=0) or 0) / 1024**3, 2)),
    OmlxSensorDescription(key="runtime_cache_ssd", translation_key="runtime_cache_ssd", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: round((_path(d, "runtime_cache", "total_size_bytes", default=0) or 0) / 1024**3, 2)),
    OmlxSensorDescription(key="runtime_cache_memory", translation_key="runtime_cache_memory", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: round((_path(d, "runtime_cache", "hot_cache_size_bytes", default=0) or 0) / 1024**3, 2)),
    OmlxSensorDescription(key="runtime_cache_files", translation_key="runtime_cache_files", state_class=SensorStateClass.MEASUREMENT, value=lambda d: _path(d, "runtime_cache", "total_num_files", default=0)),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: OmlxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(OmlxSensor(coordinator, entry, description) for description in SENSORS)


class OmlxSensor(CoordinatorEntity[OmlxCoordinator], SensorEntity):
    entity_description: OmlxSensorDescription

    def __init__(self, coordinator: OmlxCoordinator, entry: ConfigEntry, description: OmlxSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "oMLX Server",
            "manufacturer": "oMLX",
        }

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != "loaded_models":
            return None
        data = self.coordinator.data or {}
        return {
            "host": data.get("host"),
            "port": data.get("port"),
            "active_models": _path(data, "active_models", "models", default=[]),
            "runtime_cache": data.get("runtime_cache"),
        }
