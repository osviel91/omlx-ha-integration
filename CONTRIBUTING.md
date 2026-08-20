# Contributing

Thanks for helping improve oMLX Monitor.

## Workflow

1. Fork the repository.
2. Create a branch from `develop`.
3. Make the smallest change that solves the issue.
4. Run the syntax check.
5. Open a pull request into `develop`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile custom_components/omlx_monitor/*.py
```

## Pull Requests

- Describe what changed and why.
- Mention the oMLX version tested.
- Mention the Home Assistant version tested.
- Include screenshots if the change affects entity names, devices, or UI setup.
- Do not include API keys, logs with secrets, or local network details.

## Release Flow

- `develop` receives pull requests.
- `main` tracks released/stable code.
- Releases are tagged from `main` using the integration version, for example `v0.2.0`.
