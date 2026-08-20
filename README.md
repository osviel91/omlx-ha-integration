# oMLX Monitor for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)

Home Assistant custom integration for monitoring an [oMLX](https://omlx.ai/) server.

It polls the same admin dashboard endpoint used by oMLX, `/admin/api/stats`, and exposes server, cache, request, and per-loaded-model metrics as Home Assistant sensors.

## Features

- Local polling, no cloud dependency.
- UI setup through Home Assistant config flow.
- HACS custom repository compatible.
- Server-wide dashboard metrics.
- Runtime SSD and memory cache observability.
- Dynamic sensors for every currently loaded oMLX model.
- Raw oMLX model/cache payloads exposed as attributes on the most useful sensors.

## Install

### HACS

1. Open **HACS > Integrations > Custom repositories**.
2. Add `https://github.com/osviel91/omlx-ha-integration`.
3. Select category **Integration**.
4. Install **oMLX Monitor**.
5. Restart Home Assistant.

### Manual

Copy `custom_components/omlx_monitor` into your Home Assistant `custom_components` folder and restart Home Assistant.

## Configure

Add the integration from **Settings > Devices & services > Add integration > oMLX Monitor**.

Use the oMLX server URL, for example `http://192.168.1.20:8000`, and the main oMLX API key.

The integration logs in through `/admin/api/login` and then polls `/admin/api/stats` every 10 seconds.

## Global Sensors

| Sensor | Unit | Description |
| --- | --- | --- |
| Total prefill tokens | tokens | Session prompt/prefill tokens reported by oMLX. |
| Cached tokens | tokens | Prompt tokens served from cache. |
| Cache efficiency | % | Cached tokens versus total prefill tokens. |
| Average prefill speed | tok/s | Average prompt processing speed. |
| Average generation speed | tok/s | Average output token generation speed. |
| Total requests | count | Requests handled by the server session. |
| Active requests | count | Requests currently running. |
| Waiting requests | count | Requests waiting in scheduler queues. |
| Loaded models | count | Models currently loaded or loading. Includes active model and runtime cache payloads as attributes. |
| Process/model memory used | GiB | Current oMLX model/process memory usage as reported by the dashboard. |
| Process/model memory limit | GiB | Current oMLX model/process memory ceiling. |
| Memory pressure soft limit | GiB | Soft memory pressure threshold. |
| Memory pressure hard limit | GiB | Hard memory pressure threshold. |
| Runtime cache SSD | GiB | Total SSD runtime cache size. |
| Runtime cache SSD limit | GiB | Configured/effective SSD cache limit. |
| Runtime cache memory | GiB | Hot in-memory runtime cache size. |
| Runtime cache memory limit | GiB | Hot in-memory cache limit. |
| Runtime cache memory entries | count | Hot cache entries. |
| Runtime cache SSD files | count | SSD cache files. |

## Per-Model Sensors

For every loaded model, the integration creates a separate Home Assistant device named `oMLX <model id>` with these sensors:

| Sensor | Unit | Description |
| --- | --- | --- |
| Status | text | `loading`, `active`, or `idle`. Includes the raw active model payload as attributes. |
| Actual size | GiB | Actual loaded model size when oMLX reports it. |
| Estimated size | GiB | Estimated model memory footprint. |
| Active requests | count | Active requests for this model. |
| Waiting requests | count | Queued requests for this model. |
| Prefilling requests | count | Requests currently in prefill. |
| Generating requests | count | Requests currently generating tokens. |
| Generation speed | tok/s | Sum of current generation speed for active generating requests. Includes per-request generation details as attributes. |
| Idle time | seconds | Seconds since last access, when available. |
| TTL remaining | seconds | Remaining unload TTL, when configured. |
| Cache SSD | GiB | SSD runtime cache used by this model. Includes raw per-model cache payload as attributes. |
| Cache memory | GiB | Hot memory cache used by this model. |
| Cache SSD files | count | SSD cache files for this model. |
| Cache indexed blocks | count | Indexed cache blocks. |
| Cache memory entries | count | Hot cache entries for this model. |

Per-model entities are created when a model appears in oMLX's active model list. Home Assistant keeps old entity registry entries after models unload; disable or remove entities you no longer want.

## Security

This integration uses the main oMLX admin API key because the dashboard stats endpoint requires admin authentication. Keep oMLX on a trusted network, or put it behind HTTPS/authentication if you expose it outside localhost/LAN.

## Compatibility

Tested against oMLX dashboard API shape from oMLX `0.6.x`. If oMLX changes `/admin/api/stats`, open an issue with the response shape and Home Assistant logs.

## Development

Run a quick syntax check before pushing changes:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile custom_components/omlx_monitor/*.py
```
