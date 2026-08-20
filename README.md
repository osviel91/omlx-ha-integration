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

The integration exposes dashboard counters, speeds, active/waiting requests, loaded model count, model memory, and runtime cache usage. The `loaded_models` sensor also includes the active models and runtime cache payload as attributes.
