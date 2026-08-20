# oMLX Monitor for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)

Custom integration that polls the oMLX admin dashboard endpoint `/admin/api/stats`.

## Install

### HACS

Add this repository as a HACS custom repository with category **Integration**, then install **oMLX Monitor** and restart Home Assistant.

### Manual

Copy `custom_components/omlx_monitor` into your Home Assistant `custom_components` folder and restart Home Assistant.

## Configure

Add the integration from **Settings > Devices & services > Add integration > oMLX Monitor**.

Use the oMLX server URL, for example `http://192.168.1.20:8000`, and the main oMLX API key.

## Exposed sensors

The integration exposes dashboard counters, speeds, active/waiting requests, loaded model count, process/model memory, memory pressure limits, and runtime cache usage.

For every loaded model it also creates sensors for status, size, active/waiting/prefill/generation requests, current generation speed, idle time, TTL, SSD cache, memory cache, cache files, indexed blocks, and cache entries. The model status and cache sensors keep the raw oMLX payload as attributes.
