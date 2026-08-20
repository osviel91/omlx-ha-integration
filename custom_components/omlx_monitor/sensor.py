from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfInformation, UnitOfTime
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


def _gib(value: Any) -> float:
    return round((value or 0) / 1024**3, 2)


def _models(data: dict[str, Any]) -> list[dict[str, Any]]:
    models = _path(data, "active_models", "models", default=[])
    return models if isinstance(models, list) else []


def _runtime_models(data: dict[str, Any]) -> list[dict[str, Any]]:
    models = _path(data, "runtime_cache", "models", default=[])
    return models if isinstance(models, list) else []


def _model_by_id(data: dict[str, Any], model_id: str) -> dict[str, Any]:
    return next((m for m in _models(data) if m.get("id") == model_id), {})


def _runtime_model_by_id(data: dict[str, Any], model_id: str) -> dict[str, Any]:
    return next((m for m in _runtime_models(data) if m.get("id") == model_id), {})


def _generating_tps(model: dict[str, Any]) -> float:
    return round(sum((g.get("tokens_per_second") or 0) for g in model.get("generating", [])), 2)


@dataclass(frozen=True, kw_only=True)
class OmlxSensorDescription(SensorEntityDescription):
    value: Callable[[dict[str, Any]], Any]


@dataclass(frozen=True, kw_only=True)
class OmlxModelSensorDescription(SensorEntityDescription):
    value: Callable[[dict[str, Any], str], Any]
    attributes: Callable[[dict[str, Any], str], dict[str, Any] | None] = lambda _d, _m: None


SENSORS: tuple[OmlxSensorDescription, ...] = (
    OmlxSensorDescription(key="total_prompt_tokens", name="Total prefill tokens", native_unit_of_measurement="tokens", state_class=SensorStateClass.TOTAL_INCREASING, value=lambda d: d.get("total_prompt_tokens")),
    OmlxSensorDescription(key="total_cached_tokens", name="Cached tokens", native_unit_of_measurement="tokens", state_class=SensorStateClass.TOTAL_INCREASING, value=lambda d: d.get("total_cached_tokens")),
    OmlxSensorDescription(key="cache_efficiency", name="Cache efficiency", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT, value=lambda d: d.get("cache_efficiency")),
    OmlxSensorDescription(key="avg_prefill_tps", name="Average prefill speed", native_unit_of_measurement="tok/s", state_class=SensorStateClass.MEASUREMENT, value=lambda d: d.get("avg_prefill_tps")),
    OmlxSensorDescription(key="avg_generation_tps", name="Average generation speed", native_unit_of_measurement="tok/s", state_class=SensorStateClass.MEASUREMENT, value=lambda d: d.get("avg_generation_tps")),
    OmlxSensorDescription(key="total_requests", name="Total requests", state_class=SensorStateClass.TOTAL_INCREASING, value=lambda d: d.get("total_requests")),
    OmlxSensorDescription(key="active_requests", name="Active requests", state_class=SensorStateClass.MEASUREMENT, value=lambda d: _path(d, "active_models", "total_active_requests", default=0)),
    OmlxSensorDescription(key="waiting_requests", name="Waiting requests", state_class=SensorStateClass.MEASUREMENT, value=lambda d: _path(d, "active_models", "total_waiting_requests", default=0)),
    OmlxSensorDescription(key="loaded_models", name="Loaded models", state_class=SensorStateClass.MEASUREMENT, value=lambda d: len(_models(d))),
    OmlxSensorDescription(key="model_memory_used", name="Process/model memory used", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: _gib(_path(d, "active_models", "model_memory_used", default=0))),
    OmlxSensorDescription(key="model_memory_max", name="Process/model memory limit", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: _gib(_path(d, "active_models", "model_memory_max", default=0))),
    OmlxSensorDescription(key="memory_pressure_soft_limit", name="Memory pressure soft limit", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: _gib(_path(d, "active_models", "memory_pressure", "soft_bytes", default=0))),
    OmlxSensorDescription(key="memory_pressure_hard_limit", name="Memory pressure hard limit", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: _gib(_path(d, "active_models", "memory_pressure", "hard_bytes", default=0))),
    OmlxSensorDescription(key="runtime_cache_ssd", name="Runtime cache SSD", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: _gib(_path(d, "runtime_cache", "total_size_bytes", default=0))),
    OmlxSensorDescription(key="runtime_cache_ssd_limit", name="Runtime cache SSD limit", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: _gib(_path(d, "runtime_cache", "disk_max_bytes", default=0))),
    OmlxSensorDescription(key="runtime_cache_memory", name="Runtime cache memory", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: _gib(_path(d, "runtime_cache", "hot_cache_size_bytes", default=0))),
    OmlxSensorDescription(key="runtime_cache_memory_limit", name="Runtime cache memory limit", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d: _gib(_path(d, "runtime_cache", "hot_cache_max_bytes", default=0))),
    OmlxSensorDescription(key="runtime_cache_entries", name="Runtime cache memory entries", state_class=SensorStateClass.MEASUREMENT, value=lambda d: _path(d, "runtime_cache", "hot_cache_entries", default=0)),
    OmlxSensorDescription(key="runtime_cache_files", name="Runtime cache SSD files", state_class=SensorStateClass.MEASUREMENT, value=lambda d: _path(d, "runtime_cache", "total_num_files", default=0)),
)

MODEL_SENSORS: tuple[OmlxModelSensorDescription, ...] = (
    OmlxModelSensorDescription(key="status", name="Status", value=lambda d, m: "loading" if _model_by_id(d, m).get("is_loading") else "active" if _model_by_id(d, m).get("active_requests") else "idle", attributes=lambda d, m: _model_by_id(d, m)),
    OmlxModelSensorDescription(key="actual_size", name="Actual size", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _gib(_model_by_id(d, m).get("actual_size"))),
    OmlxModelSensorDescription(key="estimated_size", name="Estimated size", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _gib(_model_by_id(d, m).get("estimated_size"))),
    OmlxModelSensorDescription(key="active_requests", name="Active requests", state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _model_by_id(d, m).get("active_requests", 0)),
    OmlxModelSensorDescription(key="waiting_requests", name="Waiting requests", state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _model_by_id(d, m).get("waiting_requests", 0)),
    OmlxModelSensorDescription(key="prefilling_requests", name="Prefilling requests", state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: len(_model_by_id(d, m).get("prefilling", []))),
    OmlxModelSensorDescription(key="generating_requests", name="Generating requests", state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: len(_model_by_id(d, m).get("generating", []))),
    OmlxModelSensorDescription(key="generation_speed", name="Generation speed", native_unit_of_measurement="tok/s", state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _generating_tps(_model_by_id(d, m)), attributes=lambda d, m: {"generating": _model_by_id(d, m).get("generating", [])}),
    OmlxModelSensorDescription(key="idle_time", name="Idle time", device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.SECONDS, state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _model_by_id(d, m).get("idle_seconds")),
    OmlxModelSensorDescription(key="ttl_remaining", name="TTL remaining", device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.SECONDS, state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _model_by_id(d, m).get("ttl_remaining_seconds")),
    OmlxModelSensorDescription(key="cache_ssd", name="Cache SSD", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _gib(_runtime_model_by_id(d, m).get("total_size_bytes")), attributes=lambda d, m: _runtime_model_by_id(d, m)),
    OmlxModelSensorDescription(key="cache_memory", name="Cache memory", device_class=SensorDeviceClass.DATA_SIZE, native_unit_of_measurement=UnitOfInformation.GIBIBYTES, state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _gib(_runtime_model_by_id(d, m).get("hot_cache_size_bytes"))),
    OmlxModelSensorDescription(key="cache_files", name="Cache SSD files", state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _runtime_model_by_id(d, m).get("num_files", 0)),
    OmlxModelSensorDescription(key="cache_indexed_blocks", name="Cache indexed blocks", state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _runtime_model_by_id(d, m).get("indexed_blocks", 0)),
    OmlxModelSensorDescription(key="cache_memory_entries", name="Cache memory entries", state_class=SensorStateClass.MEASUREMENT, value=lambda d, m: _runtime_model_by_id(d, m).get("hot_cache_entries", 0)),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: OmlxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(OmlxSensor(coordinator, entry, description) for description in SENSORS)
    seen_models: set[str] = set()

    def add_model_entities() -> None:
        new_entities = []
        for model in _models(coordinator.data or {}):
            model_id = model.get("id")
            if not model_id or model_id in seen_models:
                continue
            seen_models.add(model_id)
            new_entities.extend(
                OmlxModelSensor(coordinator, entry, model_id, description)
                for description in MODEL_SENSORS
            )
        if new_entities:
            async_add_entities(new_entities)

    add_model_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_model_entities))


class OmlxSensor(CoordinatorEntity[OmlxCoordinator], SensorEntity):
    entity_description: OmlxSensorDescription

    def __init__(self, coordinator: OmlxCoordinator, entry: ConfigEntry, description: OmlxSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_has_entity_name = True
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


class OmlxModelSensor(CoordinatorEntity[OmlxCoordinator], SensorEntity):
    entity_description: OmlxModelSensorDescription

    def __init__(
        self,
        coordinator: OmlxCoordinator,
        entry: ConfigEntry,
        model_id: str,
        description: OmlxModelSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        safe_model_id = model_id.replace("/", "_").replace(".", "_")
        self.entity_description = description
        self._model_id = model_id
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{safe_model_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id, model_id)},
            "name": f"oMLX {model_id}",
            "manufacturer": "oMLX",
            "via_device": (DOMAIN, entry.entry_id),
        }

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.coordinator.data or {}, self._model_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self.entity_description.attributes(self.coordinator.data or {}, self._model_id)
