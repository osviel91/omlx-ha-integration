# Agent Notes

## Scope

- This repo is a Home Assistant custom integration for HACS; integration code lives under `custom_components/omlx_monitor/`.
- `main` is released/stable; `develop` receives PRs. Release tags are cut from `main` and should match `manifest.json` version, e.g. `v0.2.0`.

## Verification

- There is no test suite or CI config in this repo yet.
- Run the only documented check after Python changes:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile custom_components/omlx_monitor/*.py
```

## Runtime/API Facts

- The integration logs into oMLX with the main admin API key via `/admin/api/login`, then polls `/admin/api/stats` every 10 seconds.
- Keep compatibility notes tied to the oMLX `0.6.x` dashboard API shape unless verified against another version.
- Do not log, document, or commit real API keys, local logs with secrets, or user network details.

## Entity Model

- Global sensors are defined in `SENSORS` in `sensor.py`.
- Per-loaded-model sensors are defined in `MODEL_SENSORS`; they are created dynamically when a model appears in `active_models.models`.
- Home Assistant may keep stale per-model entity registry entries after a model unloads; this is documented behavior, not cleanup code to add casually.
- Keep raw oMLX payload attributes only on high-value sensors (`loaded_models`, model `status`, model `cache_ssd`) to avoid bloating every entity.

## HACS/Public Repo

- Keep `hacs.json`, `manifest.json`, and README sensor lists in sync when adding/removing entities.
- `manifest.json` has no external `requirements`; prefer Home Assistant-provided libraries unless a dependency is truly necessary.
- Public-facing config strings in `strings.json` are English; add translation files instead of switching the base strings to another language.

## Contribution Workflow

- Follow `CONTRIBUTING.md`: branch from `develop`, open PRs into `develop`, merge/release to `main` separately.
- `.github/CODEOWNERS` assigns all files to `@osviel91`; avoid changing ownership without explicit request.
